"""
Holiday Engine

Single source of truth for exchange holidays.

Used By:
- NSE Equity Acquisition
- NSE F&O Acquisition
- BSE Equity Acquisition (future)
- BSE F&O Acquisition (future)
- Corporate Actions Acquisition
- Backtesting
- Analytics
"""

from datetime import datetime

import pandas as pd

from nselib import trading_holiday_calendar

from engines.common.config import (
    NSE_HOLIDAY_FILE,
    SPECIAL_SESSIONS_FILE,
)

from engines.common.logger import (
    get_logger,
)

logger = get_logger(
    "holiday_engine"
)


def update_nse_holidays():
    """
    Refresh NSE holiday file.

    Incremental:
    If current year already exists,
    skip download.
    """

    try:

        current_year = (
            datetime.now().year
        )

        # --------------------------------
        # Existing Data
        # --------------------------------

        if NSE_HOLIDAY_FILE.exists():

            existing_df = pd.read_csv(
                NSE_HOLIDAY_FILE
            )

        else:

            existing_df = pd.DataFrame(
                columns=[
                    "Date",
                    "Year",
                    "Holiday",
                ]
            )

        # --------------------------------
        # Skip If Current Year Exists
        # --------------------------------

        if (
            not existing_df.empty
            and
            "Year" in existing_df.columns
            and
            current_year in set(
                existing_df["Year"]
            )
        ):

            logger.info(
                f"NSE holidays already available "
                f"for {current_year}"
            )

            return

        # --------------------------------
        # NSELib Holiday Download
        # --------------------------------

        holiday_df = (
            trading_holiday_calendar()
        )

        if holiday_df.empty:

            logger.warning(
                "No NSE holidays returned"
            )

            return

        # --------------------------------
        # Equities Holidays Only
        # --------------------------------

        holiday_df = holiday_df[

            holiday_df["Product"]
            .astype(str)
            .str.strip()
            .eq("Equities")

        ]

        holiday_df = holiday_df[

            [
                "tradingDate",
                "description",
            ]

        ]

        holiday_df.columns = [

            "Date",
            "Holiday",

        ]

        holiday_df["Date"] = pd.to_datetime(
            holiday_df["Date"],
            dayfirst=True,
        )

        holiday_df["Year"] = (
            holiday_df["Date"]
            .dt.year
        )

        holiday_df["Date"] = (
            holiday_df["Date"]
            .dt.strftime(
                "%Y-%m-%d"
            )
        )

        # --------------------------------
        # Merge History
        # --------------------------------

        combined = pd.concat(

            [
                existing_df,
                holiday_df,
            ],

            ignore_index=True,

        )

        combined = (

            combined

            .drop_duplicates(
                subset=["Date"]
            )

            .sort_values(
                by="Date"
            )

            .reset_index(
                drop=True
            )

        )

        NSE_HOLIDAY_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        combined.to_csv(
            NSE_HOLIDAY_FILE,
            index=False
        )

        logger.info(
            f"NSE holidays stored: "
            f"{len(combined)}"
        )

    except Exception as e:

        logger.exception(
            f"NSE holiday update error: {e}"
        )


def load_nse_holidays():
    """
    Returns:

    {
        '20250126',
        '20250314',
        ...
    }
    """

    try:

        if not NSE_HOLIDAY_FILE.exists():

            logger.warning(
                "Holiday file not found"
            )

            return set()

        df = pd.read_csv(
            NSE_HOLIDAY_FILE
        )

        df.columns = (
            df.columns
            .str.strip()
            .str.upper()
        )

        if "DATE" not in df.columns:

            logger.warning(
                "DATE column missing "
                "in holiday file"
            )

            return set()

        holidays = {

            d.strftime("%Y%m%d")

            for d in pd.to_datetime(
                df["DATE"]
            )

        }

        return holidays

    except Exception as e:

        logger.exception(
            f"Holiday load error: {e}"
        )

        return set()


def is_holiday(
    trade_date
):
    """
    trade_date:
        datetime.date

    Returns:
        True / False
    """

    holiday_set = (
        load_nse_holidays()
    )

    return (

        trade_date.strftime(
            "%Y%m%d"
        )

        in holiday_set

    )


# ============================================================
# SPECIAL TRADING SESSIONS
#
# NSE occasionally holds a LIVE trading session on a date that is
# otherwise a weekend or a listed holiday -- e.g. the annual Diwali
# Muhurat session, or (starting 2026) a special session on Union Budget
# day whenever Feb 1 falls on a weekend. These are announced via an
# individual NSE circular each time (see NSE/CMTR/xxxxx circulars), but
# only two RECURRING patterns exist today:
#
#   1. Diwali Muhurat -- NSE's own current-year holiday calendar marks
#      this date with an asterisk in the description (e.g.
#      "Diwali Laxmi Pujan*") even though it's listed under Equities
#      holidays. This lets us auto-detect it every year with no manual
#      maintenance, as long as NSE keeps this convention.
#   2. Union Budget Day -- fixed to Feb 1 every year since 2017; NSE
#      began running a special LIVE session on it whenever it falls on
#      a weekend starting 2026 (confirmed via NSE circular
#      NSE/CMTR/72349, dated 2026-01-16, for 01-Feb-2026 Sunday).
#
# Both are merged into get_trading_days() below so the EXISTING daily
# acquisition pipeline (validate_archive -> refresh_missing_dates ->
# backfill_missing_dates, already run daily as part of
# nse_equity_acquisition_engine.main()) picks these dates up and
# backfills them automatically -- no separate fetch logic needed.
#
# data/reference/special_trading_sessions.csv is the persistent record:
# auto-detected dates get appended here, and it also serves as a manual
# override file if a third pattern is ever announced that doesn't fit
# either rule above.
# ============================================================

BUDGET_DAY_SPECIAL_SESSION_START_YEAR = 2026


def _load_special_sessions_file():

    if not SPECIAL_SESSIONS_FILE.exists():

        return pd.DataFrame(
            columns=["Date", "Year", "Reason", "Source"]
        )

    return pd.read_csv(SPECIAL_SESSIONS_FILE)


def _detect_muhurat_from_calendar():
    """
    Check the CURRENT nselib holiday calendar for an Equities holiday
    whose description carries NSE's own asterisk marker -- their
    convention for "holiday, but a special session happens". Only
    covers the current year (nselib's API doesn't accept a year param),
    so this must run at least once a year to stay current.
    """

    try:

        df = trading_holiday_calendar()

    except Exception as e:

        logger.warning(
            f"Could not fetch holiday calendar for Muhurat detection: {e}"
        )

        return []

    eq = df[
        df["Product"].astype(str).str.strip().eq("Equities")
    ]

    marked = eq[
        eq["description"].astype(str).str.contains(r"\*", na=False, regex=True)
    ]

    out = []

    for _, row in marked.iterrows():

        try:
            d = pd.to_datetime(row["tradingDate"], dayfirst=True)
        except Exception:
            continue

        out.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Year": d.year,
            "Reason": f"Diwali Muhurat Trading ({row['description']})",
            "Source": "auto_detected_calendar_asterisk",
        })

    return out


def _detect_budget_day(year: int):
    """
    Feb 1 of `year`, only if it falls on a Saturday or Sunday AND the
    year is on/after the year this practice began (see
    BUDGET_DAY_SPECIAL_SESSION_START_YEAR). Returns None otherwise.
    """

    if year < BUDGET_DAY_SPECIAL_SESSION_START_YEAR:
        return None

    d = pd.Timestamp(year=year, month=2, day=1)

    if d.dayofweek not in (5, 6):   # 5=Saturday, 6=Sunday
        return None

    return {
        "Date": d.strftime("%Y-%m-%d"),
        "Year": year,
        "Reason": "Union Budget Day Special Session",
        "Source": "fixed_rule",
    }


def refresh_special_sessions():
    """
    Detect this year's Muhurat date (+ Budget Day if applicable) and
    merge into data/reference/special_trading_sessions.csv. Safe to run
    every day -- dedupes by Date, existing rows (including the manually
    seeded historical Muhurat list) are never overwritten.
    """

    existing = _load_special_sessions_file()

    new_rows = _detect_muhurat_from_calendar()

    current_year = datetime.now().year

    budget_row = _detect_budget_day(current_year)
    if budget_row:
        new_rows.append(budget_row)

    # Also check next year's Budget Day -- by December, next year's
    # Feb 1 is already knowable and worth having in the file early.
    budget_row_next = _detect_budget_day(current_year + 1)
    if budget_row_next:
        new_rows.append(budget_row_next)

    if not new_rows:
        return existing

    new_df = pd.DataFrame(new_rows)

    combined = (
        pd.concat([existing, new_df], ignore_index=True)
        .drop_duplicates(subset=["Date"], keep="first")
        .sort_values(by="Date")
        .reset_index(drop=True)
    )

    if len(combined) > len(existing):
        SPECIAL_SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(SPECIAL_SESSIONS_FILE, index=False)
        logger.info(
            f"Special trading sessions: {len(combined) - len(existing)} new date(s) added"
        )

    return combined


def load_special_sessions():
    """
    Returns:
        {'20261108', '20260201', ...}
    """

    try:

        df = _load_special_sessions_file()

        if df.empty or "Date" not in df.columns:
            return set()

        return {
            d.strftime("%Y%m%d")
            for d in pd.to_datetime(df["Date"])
        }

    except Exception as e:

        logger.exception(
            f"Special sessions load error: {e}"
        )

        return set()


def get_trading_days(
    start_date,
    end_date,
):
    """
    Returns valid NSE trading dates within [start_date, end_date]:
    weekday business days minus holidays, PLUS any special weekend/
    holiday trading sessions (Diwali Muhurat, Budget Day -- see
    refresh_special_sessions()) that fall in range.
    """

    holidays = (
        load_nse_holidays()
    )

    trading_days = [

        d

        for d in pd.date_range(
            start=start_date,
            end=end_date,
            freq="B"
        )

        if (
            d.strftime(
                "%Y%m%d"
            )
            not in holidays
        )

    ]

    special = load_special_sessions()

    if special:

        extra = [
            d
            for d in pd.date_range(start=start_date, end=end_date, freq="D")
            if d.strftime("%Y%m%d") in special
        ]

        if extra:
            trading_days = sorted(set(trading_days) | set(extra))

    return trading_days


def refresh_holidays():
    """
    Public wrapper
    """

    update_nse_holidays()


if __name__ == "__main__":

    refresh_holidays()

    print(
        f"Holidays Loaded: "
        f"{len(load_nse_holidays())}"
    )
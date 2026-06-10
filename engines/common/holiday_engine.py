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


def get_trading_days(
    start_date,
    end_date,
):
    """
    Returns only valid
    NSE trading dates.

    Weekends removed.
    Holidays removed.
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
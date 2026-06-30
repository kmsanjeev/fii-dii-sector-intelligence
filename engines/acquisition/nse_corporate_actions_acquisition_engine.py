"""
NSE Corporate Actions Acquisition Engine
Phase-2 Acquisition Foundation

Source:
    NSELib

Outputs:
    data/NSE/corporate_actions/YYYY.csv
    data/NSE/corporate_actions/YYYY.parquet

Master:
    data/NSE/equity_master/
        nse_corporate_actions_master.csv
        nse_corporate_actions_master.parquet

Derived:
    data/NSE/equity_master/
        nse_corporate_actions_derived.csv
        nse_corporate_actions_derived.parquet
"""

import sys
from datetime import date
from datetime import datetime
from pathlib import Path

import pandas as pd

from nselib import capital_market

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common.config import (
    CORPORATE_ACTION_START_YEAR,
    CORPORATE_ACTIONS_DIR,
    EQUITY_MASTER_DIR,
    WRITE_CSV,
    WRITE_PARQUET,
)

from engines.common.logger import (
    get_logger,
)

from engines.common.progress import (
    progress,
)

logger = get_logger(
    "nse_corporate_actions"
)

# ============================================================
# FILES
# ============================================================

MASTER_CSV = (
    EQUITY_MASTER_DIR /
    "nse_corporate_actions_master.csv"
)

MASTER_PARQUET = (
    EQUITY_MASTER_DIR /
    "nse_corporate_actions_master.parquet"
)

DERIVED_CSV = (
    EQUITY_MASTER_DIR /
    "nse_corporate_actions_derived.csv"
)

DERIVED_PARQUET = (
    EQUITY_MASTER_DIR /
    "nse_corporate_actions_derived.parquet"
)

# ============================================================
# SCHEMA
# ============================================================

EXPECTED_COLUMNS = [

    "symbol",
    "series",
    "ind",
    "faceVal",
    "subject",
    "exDate",
    "recDate",
    "bcStartDate",
    "bcEndDate",
    "ndStartDate",
    "comp",
    "isin",
    "ndEndDate",
    "caBroadcastDate",

]

# ============================================================
# HELPERS
# ============================================================

def ensure_storage():

    CORPORATE_ACTIONS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    EQUITY_MASTER_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def year_csv_file(
    year: int
) -> Path:

    return (
        CORPORATE_ACTIONS_DIR /
        f"{year}.csv"
    )


def year_parquet_file(
    year: int
) -> Path:

    return (
        CORPORATE_ACTIONS_DIR /
        f"{year}.parquet"
    )


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_columns(
    df: pd.DataFrame
) -> pd.DataFrame:

    rename_map = {

        "SYMBOL": "symbol",
        "SERIES": "series",
        "IND": "ind",
        "FACEVAL": "faceVal",
        "SUBJECT": "subject",
        "EXDATE": "exDate",
        "RECDATE": "recDate",
        "BCSTARTDATE": "bcStartDate",
        "BCENDDATE": "bcEndDate",
        "NDSTARTDATE": "ndStartDate",
        "COMP": "comp",
        "ISIN": "isin",
        "NDENDDATE": "ndEndDate",
        "CABROADCASTDATE": "caBroadcastDate",

    }

    df.columns = (
        df.columns
        .str.strip()
    )

    df.rename(
        columns=rename_map,
        inplace=True
    )

    return df


def enforce_schema(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = normalize_columns(df)

    missing = (

        set(EXPECTED_COLUMNS)

        -

        set(df.columns)

    )

    if missing:

        raise ValueError(
            f"Missing columns: {missing}"
        )

    df = df[
        EXPECTED_COLUMNS
    ].copy()

    return df


# ============================================================
# VALIDATION
# ============================================================

def is_valid_corporate_action_file(
    file_path: Path
) -> bool:

    try:

        df = pd.read_csv(
            file_path,
            nrows=5
        )

        return all(
            col in df.columns
            for col in [
                "symbol",
                "subject",
                "exDate",
                "isin",
            ]
        )

    except Exception:

        return False


# ============================================================
# DOWNLOAD
# ============================================================

def fetch_year(
    year: int
) -> pd.DataFrame:

    logger.info(
        f"Fetching corporate actions "
        f"for {year}"
    )

    from_date = (
        f"01-01-{year}"
    )

    to_date = (
        f"31-12-{year}"
    )

    try:

        df = (
            capital_market
            .corporate_actions_for_equity(
                from_date=from_date,
                to_date=to_date
            )
        )

    except Exception as e:

        logger.exception(
            f"{year} fetch failed: {e}"
        )

        return pd.DataFrame()

    if df is None:
        return pd.DataFrame()

    if len(df) == 0:
        return pd.DataFrame()

    df = normalize_columns(df)

    return df


# ============================================================
# STORAGE
# ============================================================

def save_year(
    year: int,
    df: pd.DataFrame
):

    csv_file = (
        year_csv_file(year)
    )

    parquet_file = (
        year_parquet_file(year)
    )

    if csv_file.exists():

        existing = pd.read_csv(
            csv_file
        )

        df = pd.concat(
            [
                existing,
                df
            ],
            ignore_index=True
        )

        df = (

            df

            .drop_duplicates(

                subset=[

                    "symbol",
                    "subject",
                    "exDate",
                    "isin",

                ]

            )

            .reset_index(
                drop=True
            )

        )

    if WRITE_CSV:

        df.to_csv(
            csv_file,
            index=False
        )

    if WRITE_PARQUET:

        df.to_parquet(
            parquet_file,
            index=False
        )

    logger.info(
        f"{year}: stored "
        f"{len(df)} records"
    )
    
# ============================================================
# MASTER BUILDER
# ============================================================

def refresh_master():

    frames = []

    for year in range(
        CORPORATE_ACTION_START_YEAR,
        datetime.now().year + 1
    ):

        csv_file = (
            year_csv_file(year)
        )

        if not csv_file.exists():
            continue

        try:

            df = pd.read_csv(
                csv_file
            )

            if not df.empty:

                frames.append(
                    df
                )

        except Exception as e:

            logger.exception(
                f"{year}: {e}"
            )

    if not frames:

        logger.warning(
            "No corporate action data found"
        )

        return pd.DataFrame()

    master = pd.concat(
        frames,
        ignore_index=True
    )

    master = (

        master

        .drop_duplicates()

        .sort_values(
            by=[
                "exDate",
                "symbol"
            ]
        )

        .reset_index(
            drop=True
        )

    )

    if WRITE_CSV:

        master.to_csv(
            MASTER_CSV,
            index=False
        )

    if WRITE_PARQUET:

        master.to_parquet(
            MASTER_PARQUET,
            index=False
        )

    logger.info(
        f"Master refreshed: "
        f"{len(master)} records"
    )

    return master


# ============================================================
# ADJUSTMENT FACTOR     R
# ============================================================

def parse_adjustment_factor(
    subject: str
):

    if pd.isna(subject):

        return (
            None,
            None
        )

    import re

    text = (
        str(subject)
        .upper()
        .strip()
    )

    bonus_factor = None
    split_factor = None

    # --------------------------------------------------------
    # BONUS
    # --------------------------------------------------------

    if "BONUS" in text:

        match = re.search(
            r"(\d+)\s*:\s*(\d+)",
            text
        )

        if match:

            new_shares = int(
                match.group(1)
            )

            old_shares = int(
                match.group(2)
            )

            bonus_factor = (

                old_shares

                /

                (

                    old_shares +
                    new_shares

                )

            )

    # --------------------------------------------------------
    # SPLIT / FACE VALUE CHANGE
    # --------------------------------------------------------

    if (
        "SPLIT" in text
        or
        "FACE VALUE" in text
        or
        "FV SPLIT" in text
    ):

        try:

            split_match = re.search(

                r"FROM\s+RS?\s*(\d+)"
                r".*?"
                r"TO\s+R(?:S|E)?\s*(\d+)",

                text,

                re.IGNORECASE

            )

            if split_match:

                old_face = float(
                    split_match.group(1)
                )

                new_face = float(
                    split_match.group(2)
                )

                if old_face > 0:

                    split_factor = (
                        new_face /
                        old_face
                    )

        except Exception:

            pass

    # --------------------------------------------------------
    # BONUS + SPLIT
    # --------------------------------------------------------

    if (
        bonus_factor is not None
        and
        split_factor is not None
    ):

        return (

            "BONUS_SPLIT",

            (
                bonus_factor *
                split_factor
            )

        )

    # --------------------------------------------------------
    # BONUS ONLY
    # --------------------------------------------------------

    if bonus_factor is not None:

        return (
            "BONUS",
            bonus_factor
        )

    # --------------------------------------------------------
    # SPLIT ONLY
    # --------------------------------------------------------

    if split_factor is not None:

        return (
            "SPLIT",
            split_factor
        )

    # --------------------------------------------------------
    # RIGHTS ISSUE
    # --------------------------------------------------------

    if "RIGHTS" in text:

        return (
            "RIGHTS",
            None
        )

    # --------------------------------------------------------
    # BUYBACK
    # --------------------------------------------------------

    if "BUY BACK" in text or "BUYBACK" in text:

        return (
            "BUYBACK",
            None
        )

    # --------------------------------------------------------
    # DIVIDEND
    # --------------------------------------------------------

    if "DIVIDEND" in text:

        return (
            "DIVIDEND",
            None
        )

    # --------------------------------------------------------
    # INTEREST PAYMENT
    # --------------------------------------------------------

    if "INTEREST" in text:

        return (
            "INTEREST",
            None
        )

    return (
        None,
        None
    )

# ============================================================
# DERIVED BUILDER
# ============================================================

def refresh_derived():

    if not MASTER_CSV.exists():

        logger.warning(
            "Master file missing"
        )

        return pd.DataFrame()

    master = pd.read_csv(
        MASTER_CSV
    )

    if master.empty:

        return pd.DataFrame()

    derived = master.copy()

    derived[
        "adjustment_type"
    ] = None

    derived[
        "adjustment_factor"
    ] = None

    derived[
        "price_impact"
    ] = False

    derived[
        "volume_adjustment"
    ] = False

    total = len(
        derived
    )

    for idx in progress(
        range(total),
        desc="Corporate Actions"
    ):

        subject = (
            derived.at[
                idx,
                "subject"
            ]
        )

        adj_type, factor = (
            parse_adjustment_factor(
                subject
            )
        )

        derived.at[
            idx,
            "adjustment_type"
        ] = adj_type

        derived.at[
            idx,
            "adjustment_factor"
        ] = factor

        if adj_type in {

            "BONUS",
            "SPLIT"

        }:

            derived.at[
                idx,
                "price_impact"
            ] = True

            derived.at[
                idx,
                "volume_adjustment"
            ] = True

    if WRITE_CSV:

        derived.to_csv(
            DERIVED_CSV,
            index=False
        )

    if WRITE_PARQUET:

        derived.to_parquet(
            DERIVED_PARQUET,
            index=False
        )

    logger.info(
        f"Derived refreshed: "
        f"{len(derived)} records"
    )

    return derived


# ============================================================
# ACQUISITION LOG
# ============================================================

ACQUISITION_LOG = (
    CORPORATE_ACTIONS_DIR /
    "corporate_actions_acquisition_log.csv"
)


def log_acquisition_run(
    fetched,
    new_records,
    total_master
):

    row = pd.DataFrame([{

        "RUN_DATE":
            datetime.now(),

        "RECORDS_FETCHED":
            fetched,

        "NEW_RECORDS":
            new_records,

        "TOTAL_MASTER":
            total_master,

    }])

    if ACQUISITION_LOG.exists():

        existing = pd.read_csv(
            ACQUISITION_LOG
        )

        row = pd.concat(
            [
                existing,
                row
            ],
            ignore_index=True
        )

    row.to_csv(
        ACQUISITION_LOG,
        index=False
    )
    
# ============================================================
# DOWNLOAD YEAR
# ============================================================

def download_year(
    year: int
):

    ensure_storage()

    logger.info(
        f"Corporate Actions "
        f"Download: {year}"
    )

    df = fetch_year(
        year
    )

    if df.empty:

        logger.warning(
            f"{year}: no records"
        )

        return {

            "year": year,
            "fetched": 0

        }

    before_count = len(df)

    save_year(
        year,
        df
    )

    master = (
        refresh_master()
    )

    derived = (
        refresh_derived()
    )

    log_acquisition_run(

        fetched=before_count,

        new_records=before_count,

        total_master=(
            len(master)
            if isinstance(
                master,
                pd.DataFrame
            )
            else 0
        )

    )

    return {

        "year": year,
        "fetched": before_count,
        "master": (
            len(master)
            if isinstance(
                master,
                pd.DataFrame
            )
            else 0
        ),
        "derived": (
            len(derived)
            if isinstance(
                derived,
                pd.DataFrame
            )
            else 0
        )

    }


# ============================================================
# DOWNLOAD RANGE
# ============================================================

def download_range(
    start_year: int,
    end_year: int
):

    results = []

    years = list(

        range(
            start_year,
            end_year + 1
        )

    )

    for year in progress(
        years,
        desc="Corporate Actions"
    ):

        result = (
            download_year(
                year
            )
        )

        results.append(
            result
        )

    return results


# ============================================================
# FULL BACKFILL
# ============================================================

def download_all():

    current_year = (
        datetime.now().year
    )

    return download_range(

        CORPORATE_ACTION_START_YEAR,

        current_year

    )


# ============================================================
# INCREMENTAL UPDATE
# ============================================================

def incremental_update():

    current_year = (
        datetime.now().year
    )

    logger.info(
        f"Incremental update "
        f"for {current_year}"
    )

    return download_year(
        current_year
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_storage():

    results = []

    for year in range(

        CORPORATE_ACTION_START_YEAR,

        datetime.now().year + 1

    ):

        csv_file = (
            year_csv_file(
                year
            )
        )

        if not csv_file.exists():

            continue

        valid = (
            is_valid_corporate_action_file(
                csv_file
            )
        )

        results.append({

            "YEAR": year,
            "VALID": valid

        })

    return pd.DataFrame(
        results
    )


# ============================================================
# REFRESH EVERYTHING
# ============================================================

def refresh_all():

    logger.info(
        "Refreshing Corporate "
        "Actions Assets"
    )

    master = (
        refresh_master()
    )

    derived = (
        refresh_derived()
    )

    validation = (
        validate_storage()
    )

    return {

        "master_records":

            (
                len(master)

                if isinstance(
                    master,
                    pd.DataFrame
                )

                else 0
            ),

        "derived_records":

            (
                len(derived)

                if isinstance(
                    derived,
                    pd.DataFrame
                )

                else 0
            ),

        "validated_files":

            (
                len(validation)

                if isinstance(
                    validation,
                    pd.DataFrame
                )

                else 0
            )

    }


# ============================================================
# STATUS
# ============================================================

def get_status():

    years = []

    for year in range(

        CORPORATE_ACTION_START_YEAR,

        datetime.now().year + 1

    ):

        csv_file = (
            year_csv_file(
                year
            )
        )

        if csv_file.exists():

            years.append(
                year
            )

    return {

        "years": len(years),

        "first_year":

            min(years)
            if years
            else None,

        "last_year":

            max(years)
            if years
            else None,

        "master_exists":
            MASTER_CSV.exists(),

        "derived_exists":
            DERIVED_CSV.exists(),

    }


# ============================================================
# CLI
# ============================================================

def main():

    print()

    print(
        "=" * 70
    )

    print(
        "NSE CORPORATE ACTIONS "
        "ACQUISITION ENGINE"
    )

    print(
        "=" * 70
    )

    result = (
        incremental_update()
    )

    print()

    print(
        "=" * 70
    )

    print(
        "ACQUISITION COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        f"Year      : "
        f"{result['year']}"
    )

    print(
        f"Fetched   : "
        f"{result['fetched']}"
    )

    status = (
        get_status()
    )

    print(
        f"Master    : "
        f"{status['master_exists']}"
    )

    print(
        f"Derived   : "
        f"{status['derived_exists']}"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()
"""
Price Adjustment Engine

Creates adjusted historical datasets
without modifying raw bhavcopy files.

Inputs:
    data/NSE/bhavcopy/equity/

    data/NSE/equity_master/
        nse_corporate_actions_derived.csv

Outputs:
    data/NSE/adjusted_equity/

Features:
    Price Adjustment
    Volume Adjustment
    VWAP Recalculation
    Sanity Validation
"""

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common.config import (
    NSE_EQUITY_BHAVCOPY_DIR,
    EQUITY_MASTER_DIR,
    ADJUSTED_EQUITY_DIR,
    WRITE_PARQUET,
    WRITE_CSV,
)

from engines.common.logger import (
    get_logger,
)

from engines.common.progress import (
    progress,
)

logger = get_logger(
    "price_adjustment"
)

# ============================================================
# FILES
# ============================================================

CA_DERIVED_FILE = (

    EQUITY_MASTER_DIR /

    "nse_corporate_actions_derived.csv"

)

SANITY_DIR = (

    ADJUSTED_EQUITY_DIR /

    "sanity"

)

SANITY_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ============================================================
# PRICE COLUMNS
# ============================================================

PRICE_COLS = [

    "OPEN_PRICE",
    "HIGH_PRICE",
    "LOW_PRICE",

    "LAST_PRICE",
    "CLOSE_PRICE",

    "PREV_CLOSE",

    "AVG_PRICE",

]

VOLUME_COLS = [

    "TTL_TRD_QNTY",

]

# ============================================================
# BHAVCOPY NORMALIZATION
# ============================================================

BHAVCOPY_COLUMN_MAP = {

    "OPEN": "OPEN_PRICE",
    "HIGH": "HIGH_PRICE",
    "LOW": "LOW_PRICE",

    "CLOSE": "CLOSE_PRICE",

    "LAST": "LAST_PRICE",

    "PREVCLOSE": "PREV_CLOSE",

    "TOTTRDQTY": "TTL_TRD_QNTY",

}


def normalize_bhavcopy(
    df: pd.DataFrame
):

    df.columns = (

        df.columns

        .str.strip()

        .str.upper()

        .str.replace(
            " ",
            "_"
        )

        .str.replace(
            "-",
            "_"
        )

    )

    df.rename(

        columns=BHAVCOPY_COLUMN_MAP,

        inplace=True

    )

    return df


# ============================================================
# CORPORATE ACTIONS
# ============================================================

def load_corporate_actions():

    if not CA_DERIVED_FILE.exists():

        raise FileNotFoundError(
            CA_DERIVED_FILE
        )

    df = pd.read_csv(
        CA_DERIVED_FILE
    )

    if df.empty:

        raise RuntimeError(
            "Derived corporate "
            "actions file empty"
        )

    df["exDate"] = pd.to_datetime(
        df["exDate"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "adjustment_factor",
            "exDate",
            "symbol",
        ]
    )

    df = df[

        df[
            "adjustment_factor"
        ] > 0

    ].copy()

    return df


# ============================================================
# ADJUSTMENT LOOKUP
# ============================================================

def build_adjustment_lookup():

    logger.info(
        "Building adjustment "
        "lookup"
    )

    ca = load_corporate_actions()

    lookup = (

        ca[

            [

                "symbol",
                "exDate",
                "adjustment_factor",
                "adjustment_type",

            ]

        ]

        .rename(

            columns={

                "symbol":
                    "SYMBOL",

                "exDate":
                    "EX_DT",

                "adjustment_factor":
                    "ADJ_FACTOR",

                "adjustment_type":
                    "ADJ_TYPE",

            }

        )

        .sort_values(

            [

                "SYMBOL",
                "EX_DT",

            ]

        )

        .reset_index(
            drop=True
        )

    )

    logger.info(

        f"Adjustment actions: "
        f"{len(lookup)}"

    )

    return lookup


# ============================================================
# FILE DISCOVERY
# ============================================================

def get_bhavcopy_files():

    return sorted(

        NSE_EQUITY_BHAVCOPY_DIR.glob(
            "*/*.csv"
        )

    )


# ============================================================
# OUTPUT PATH
# ============================================================

def adjusted_output_file(
    raw_file: Path
):

    relative = (
        raw_file.relative_to(
            NSE_EQUITY_BHAVCOPY_DIR
        )
    )

    output = (
        ADJUSTED_EQUITY_DIR /
        relative
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return output
    

# ============================================================
# INCREMENTAL SKIP
# ============================================================

def should_skip_file(
    raw_file: Path,
    adjusted_file: Path
):

    if not adjusted_file.exists():

        return False

    try:

        adjusted_ts = (
            adjusted_file
            .stat()
            .st_mtime
        )

        raw_ts = (
            raw_file
            .stat()
            .st_mtime
        )

        ca_ts = (
            CA_DERIVED_FILE
            .stat()
            .st_mtime
        )

        return (

            adjusted_ts >= raw_ts

            and

            adjusted_ts >= ca_ts

        )

    except Exception:

        return False


# ============================================================
# SANITY CHECKS
# ============================================================

def run_sanity_checks(
    df: pd.DataFrame,
    source_file: Path
):

    sanity = []

    if "CLOSE_PRICE" in df.columns:

        bad_price = (

            df[
                df[
                    "CLOSE_PRICE"
                ] <= 0
            ]

        )

        if not bad_price.empty:

            sanity.append(

                bad_price.assign(
                    ISSUE=
                    "NON_POSITIVE_PRICE"
                )

            )

    if {

        "CLOSE_PRICE",
        "PREV_CLOSE"

    }.issubset(
        df.columns
    ):

        jump = (

            df[
                "CLOSE_PRICE"
            ]

            /

            df[
                "PREV_CLOSE"
            ]

        ).abs()

        bad_jump = df[

            (
                jump > 5
            )

            |

            (
                jump < 0.20
            )

        ]

        if not bad_jump.empty:

            sanity.append(

                bad_jump.assign(
                    ISSUE=
                    "EXTREME_PRICE_JUMP"
                )

            )

    if sanity:

        sanity_df = pd.concat(

            sanity,

            ignore_index=True

        )

        sanity_file = (

            SANITY_DIR /

            f"{source_file.stem}"
            "_sanity.csv"

        )

        sanity_df.to_csv(

            sanity_file,

            index=False

        )


# ============================================================
# VWAP
# ============================================================

def recompute_vwap(
    df: pd.DataFrame
):

    qty_col = None

    if "TTL_TRD_QNTY" in df.columns:

        qty_col = (
            "TTL_TRD_QNTY"
        )

    elif "TOTTRDQTY" in df.columns:

        qty_col = (
            "TOTTRDQTY"
        )

    if qty_col is None:

        return df

    if (
        "TURNOVER_VALUE"
        not in df.columns
    ):

        return df

    df["VWAP"] = (

        df[
            "TURNOVER_VALUE"
        ]

        /

        df[
            qty_col
        ]

    )

    df["VWAP"] = (

        df["VWAP"]

        .replace(
            [
                float("inf"),
                -float("inf")
            ],
            pd.NA
        )

    )

    return df


# ============================================================
# CORE ADJUSTMENT
# ============================================================

def adjust_bhavcopy_file(
    raw_file: Path,
    adjustment_lookup: pd.DataFrame
):

    output_file = (
        adjusted_output_file(
            raw_file
        )
    )

    if should_skip_file(
        raw_file,
        output_file
    ):

        return "skip"

    try:

        df = pd.read_csv(
            raw_file
        )

    except Exception as e:

        logger.exception(
            f"{raw_file.name}: "
            f"{e}"
        )

        return "error"

    df = normalize_bhavcopy(
        df
    )

    # --------------------------------------------------------
    # TRADE DATE
    # --------------------------------------------------------

    if "TRADE_DATE" in df.columns:

        df["TRADE_DATE"] = (
            pd.to_datetime(
                df["TRADE_DATE"],
                errors="coerce"
            )
        )

    elif "DATE1" in df.columns:

        df["TRADE_DATE"] = (
            pd.to_datetime(
                df["DATE1"],
                errors="coerce"
            )
        )

    elif "TIMESTAMP" in df.columns:

        df["TRADE_DATE"] = (
            pd.to_datetime(
                df["TIMESTAMP"],
                errors="coerce",
                dayfirst=True
            )
        )

    else:

        logger.warning(
            f"{raw_file.name}: "
            f"No trade date"
        )

        return "error"

    # --------------------------------------------------------
    # NUMERIC
    # --------------------------------------------------------

    for col in PRICE_COLS:

        if col in df.columns:

            df[col] = pd.to_numeric(

                df[col],

                errors="coerce"

            )

    for col in VOLUME_COLS:

        if col in df.columns:

            df[col] = pd.to_numeric(

                df[col],

                errors="coerce"

            ).astype(
                "float64"
            )

    # --------------------------------------------------------
    # TURNOVER
    # --------------------------------------------------------

    if "TURNOVER_LACS" in df.columns:

        df["TURNOVER_VALUE"] = (

            pd.to_numeric(

                df[
                    "TURNOVER_LACS"
                ],

                errors="coerce"

            )

            *

            100_000

        )

    elif "TOTTRDVAL" in df.columns:

        df["TURNOVER_VALUE"] = (

            pd.to_numeric(

                df[
                    "TOTTRDVAL"
                ],

                errors="coerce"

            )

        )

    # --------------------------------------------------------
    # FACTOR BUILD
    # --------------------------------------------------------

    adj = (

        adjustment_lookup

        .merge(

            df[

                [
                    "SYMBOL",
                    "TRADE_DATE"
                ]

            ],

            on="SYMBOL",

            how="inner"

        )

        .query(
            "EX_DT > TRADE_DATE"
        )

        .groupby(

            [
                "SYMBOL",
                "TRADE_DATE"
            ]

        )["ADJ_FACTOR"]

        .prod()

        .reset_index()

    )

    if not adj.empty:

        df = df.merge(

            adj,

            on=[
                "SYMBOL",
                "TRADE_DATE"
            ],

            how="left"

        )

        mask = (

            df[
                "ADJ_FACTOR"
            ].notna()

        )

        price_cols = [

            c

            for c in PRICE_COLS

            if c in df.columns

        ]

        volume_cols = [

            c

            for c in VOLUME_COLS

            if c in df.columns

        ]

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        df.loc[
            mask,
            price_cols
        ] = (

            df.loc[
                mask,
                price_cols
            ]

            .mul(

                df.loc[
                    mask,
                    "ADJ_FACTOR"
                ],

                axis=0

            )

        )

        # ----------------------------------------------------
        # VOLUME
        # ----------------------------------------------------

        df.loc[
            mask,
            volume_cols
        ] = (

            df.loc[
                mask,
                volume_cols
            ]

            .mul(

                1

                /

                df.loc[
                    mask,
                    "ADJ_FACTOR"
                ],

                axis=0

            )

            .round(0)

        )

        # ----------------------------------------------------
        # VWAP
        # ----------------------------------------------------

        df = recompute_vwap(
            df
        )

        df.drop(

            columns=[
                "ADJ_FACTOR"
            ],

            errors="ignore",

            inplace=True

        )

    df.drop(

        columns=[
            "TURNOVER_VALUE"
        ],

        errors="ignore",

        inplace=True

    )

    run_sanity_checks(
        df,
        raw_file
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    if WRITE_CSV:

        df.to_csv(
            output_file,
            index=False
        )

    if WRITE_PARQUET:

        parquet_file = (
            output_file
            .with_suffix(
                ".parquet"
            )
        )

        df.to_parquet(
            parquet_file,
            index=False
        )

    return "adjusted"
    
    
# ============================================================
# YEAR FILTER
# ============================================================

def get_year_files(
    year: int
):

    year_dir = (
        NSE_EQUITY_BHAVCOPY_DIR /
        str(year)
    )

    if not year_dir.exists():

        return []

    return sorted(
        year_dir.glob(
            "*.csv"
        )
    )


# ============================================================
# VALIDATION REPORT
# ============================================================

def validate_adjusted_storage():

    results = []

    for year_dir in sorted(
        ADJUSTED_EQUITY_DIR.glob("*")
    ):

        if not year_dir.is_dir():
            continue

        csv_count = len(
            list(
                year_dir.glob(
                    "*.csv"
                )
            )
        )

        parquet_count = len(
            list(
                year_dir.glob(
                    "*.parquet"
                )
            )
        )

        results.append({

            "YEAR":
                year_dir.name,

            "CSV_FILES":
                csv_count,

            "PARQUET_FILES":
                parquet_count,

        })

    report = pd.DataFrame(
        results
    )

    report_file = (

        ADJUSTED_EQUITY_DIR /

        "adjusted_equity_validation.csv"

    )

    report.to_csv(
        report_file,
        index=False
    )

    return report


# ============================================================
# ADJUST YEAR
# ============================================================

def adjust_year(
    year: int
):

    files = get_year_files(
        year
    )

    if not files:

        logger.warning(
            f"{year}: "
            f"no files found"
        )

        return {

            "year": year,
            "adjusted": 0,
            "skipped": 0,
            "errors": 0,

        }

    lookup = (
        build_adjustment_lookup()
    )

    adjusted = 0
    skipped = 0
    errors = 0

    for file in progress(
        files,
        desc=f"Adjust {year}"
    ):

        result = (
            adjust_bhavcopy_file(
                file,
                lookup
            )
        )

        if result == "adjusted":

            adjusted += 1

        elif result == "skip":

            skipped += 1

        else:

            errors += 1

    return {

        "year": year,

        "adjusted":
            adjusted,

        "skipped":
            skipped,

        "errors":
            errors,

    }


# ============================================================
# FULL REBUILD
# ============================================================

def adjust_all():

    years = sorted(

        int(
            p.name
        )

        for p in
        NSE_EQUITY_BHAVCOPY_DIR.glob(
            "*"
        )

        if (
            p.is_dir()
            and
            p.name.isdigit()
        )

    )

    results = []

    for year in progress(
        years,
        desc="All Years"
    ):

        results.append(
            adjust_year(
                year
            )
        )

    validate_adjusted_storage()

    return results


# ============================================================
# INCREMENTAL
# ============================================================

def adjust_incremental():

    years = sorted(

        int(
            p.name
        )

        for p in
        NSE_EQUITY_BHAVCOPY_DIR.glob(
            "*"
        )

        if (
            p.is_dir()
            and
            p.name.isdigit()
        )

    )

    if not years:

        return None

    latest_year = max(
        years
    )

    result = (
        adjust_year(
            latest_year
        )
    )

    validate_adjusted_storage()

    return result


# ============================================================
# STATUS
# ============================================================

def get_status():

    adjusted_files = len(

        list(

            ADJUSTED_EQUITY_DIR.glob(
                "*/*.parquet"
            )

        )

    )

    sanity_files = len(

        list(

            SANITY_DIR.glob(
                "*.csv"
            )

        )

    )

    return {

        "adjusted_files":
            adjusted_files,

        "sanity_files":
            sanity_files,

        "derived_exists":
            CA_DERIVED_FILE.exists(),

    }


# ============================================================
# SUMMARY
# ============================================================

def print_summary():

    status = (
        get_status()
    )

    print()

    print(
        "=" * 70
    )

    print(
        "PRICE ADJUSTMENT SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        f"Adjusted Files : "
        f"{status['adjusted_files']}"
    )

    print(
        f"Sanity Files   : "
        f"{status['sanity_files']}"
    )

    print(
        f"Derived Master : "
        f"{status['derived_exists']}"
    )

    print(
        "=" * 70
    )


# ============================================================
# CLI
# ============================================================

def main():

    print()

    print(
        "=" * 70
    )

    print(
        "PRICE ADJUSTMENT ENGINE"
    )

    print(
        "=" * 70
    )

    result = (
        adjust_incremental()
    )

    print()

    print(
        result
    )

    print_summary()


if __name__ == "__main__":

    main()
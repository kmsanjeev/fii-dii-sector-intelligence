"""
NSE Equity Acquisition Engine
Phase-2 Acquisition Foundation

Migrated From:
- run_step1_extract_bhavcopy_zip.py
- run_step1b_hist_bhavcopy_pull.py

Storage:
data/NSE/bhavcopy/equity/YYYY/

Outputs:
bhavcopy_YYYYMMDD.csv
bhavcopy_YYYYMMDD.parquet

Reports:
bhavcopy_registry.csv
bhavcopy_coverage_report.csv
missing_dates_report.csv
integrity_report.csv
"""

import asyncio
from datetime import date
from io import StringIO
from pathlib import Path
from nselib import capital_market

import sys

import aiohttp
import os
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common.config import (
    NSE_EQUITY_BHAVCOPY_DIR,
    BHAVCOPY_DIR,
    NSE_HOLIDAY_FILE,
    NSE_EQUITY_START_YEAR,
    NSE_EQUITY_VALIDATION_YEARS,
    MIN_CONCURRENCY,
    MAX_CONCURRENCY,
    WRITE_CSV,
    WRITE_PARQUET,
)

from engines.common.logger import get_logger
from engines.common.progress import progress
from engines.common.holiday_engine import (
    get_trading_days,
    is_holiday,
)

logger = get_logger("nse_equity_acquisition")


BASE_URL = (
    "https://nsearchives.nseindia.com/products/content"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/csv",
    "Accept-Language": "en-US,en;q=0.9",
}

BHAVCOPY_SCHEMA = {
    "SYMBOL": "string",
    "SERIES": "string",
    "OPEN_PRICE": "float64",
    "HIGH_PRICE": "float64",
    "LOW_PRICE": "float64",
    "CLOSE_PRICE": "float64",
    "TTL_TRD_QNTY": "int64",
    "TRADE_DATE": "datetime64[ns]",
}

def get_optimal_workers():

    cpu_count = os.cpu_count() or 4

    workers = min(
        MAX_CONCURRENCY,
        cpu_count
    )

    workers = max(
        MIN_CONCURRENCY,
        workers
    )

    return workers

def ensure_year_dir(year: int) -> Path:

    year_dir = (
        NSE_EQUITY_BHAVCOPY_DIR /
        str(year)
    )

    year_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return year_dir
    
def compute_validation_range():

    today = date.today()

    start = date(
        today.year -
        NSE_EQUITY_VALIDATION_YEARS,
        1,
        1
    )

    return start, today


def normalize_columns(df: pd.DataFrame):

    df.columns = (
        df.columns
        .str.strip()
        .str.upper()
    )

    df.rename(
        columns={
            "OPEN": "OPEN_PRICE",
            "HIGH": "HIGH_PRICE",
            "LOW": "LOW_PRICE",
            "CLOSE": "CLOSE_PRICE",
            "TOTTRDQTY": "TTL_TRD_QNTY",
            "TOTTRD_QTY": "TTL_TRD_QNTY",
        },
        inplace=True,
    )

    return df


def enforce_schema(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = normalize_columns(df)

    missing = (
        set(BHAVCOPY_SCHEMA)
        - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    df = df[
        list(BHAVCOPY_SCHEMA.keys())
    ].copy()

    return df


def is_valid_bhavcopy(
    file_path: Path
) -> bool:

    try:

        df = pd.read_csv(
            file_path,
            nrows=5
        )

        required = {
            "SYMBOL",
            "SERIES",
            "OPEN_PRICE",
            "HIGH_PRICE",
            "LOW_PRICE",
            "CLOSE_PRICE",
        }

        return required.issubset(
            set(df.columns)
        )

    except Exception:

        return False


def fetch_from_nselib(
    trade_date
):

    try:

        df = capital_market.bhav_copy_equities(
            trade_date.strftime(
                "%d-%m-%Y"
            )
        )

        if df is None:
            return None

        if len(df) == 0:
            return None

        df = normalize_columns(df)

        if "SERIES" in df.columns:

            df["SERIES"] = (
                df["SERIES"]
                .astype(str)
                .str.strip()
            )

            df = df[
                df["SERIES"] == "EQ"
            ].copy()

        if df.empty:
            return None

        df["TRADE_DATE"] = pd.to_datetime(
            trade_date
        )

        return enforce_schema(df)

    except Exception:

        return None


async def fetch_bhavcopy(
    session: aiohttp.ClientSession,
    trade_date: date
):

    filename = (
        f"sec_bhavdata_full_"
        f"{trade_date.strftime('%d%m%Y')}.csv"
    )

    url = f"{BASE_URL}/{filename}"

    async with session.get(
        url
    ) as response:

        if response.status != 200:
            raise FileNotFoundError(
                trade_date
            )

        raw = await response.read()

    if len(raw) < 100:
        raise FileNotFoundError(
            trade_date
        )

    try:

        text = raw.decode(
            "utf-8"
        )

    except UnicodeDecodeError:

        text = raw.decode(
            "latin-1"
        )

    try:

        df = pd.read_csv(
            StringIO(text),
            engine="c",
            on_bad_lines="skip"
        )

    except Exception:

        df = pd.read_csv(
            StringIO(text),
            engine="python",
            on_bad_lines="skip"
        )

    df = normalize_columns(df)

    if "SERIES" not in df.columns:
        raise ValueError(
            "SERIES column missing"
        )

    df["SERIES"] = (
        df["SERIES"]
        .astype(str)
        .str.strip()
    )

    df = df[
        df["SERIES"] == "EQ"
    ].copy()

    if df.empty:
        raise ValueError(
            "No EQ records found"
        )

    df["TRADE_DATE"] = pd.to_datetime(
        trade_date
    )

    return enforce_schema(df)


async def process_day(
    semaphore,
    session,
    trade_date
):

    async with semaphore:

        year_dir = ensure_year_dir(
            trade_date.year
        )

        base_name = (
            f"bhavcopy_"
            f"{trade_date.strftime('%Y%m%d')}"
        )

        csv_file = (
            year_dir /
            f"{base_name}.csv"
        )

        parquet_file = (
            year_dir /
            f"{base_name}.parquet"
        )

        # ---------------------------------
        # VALID FILE EXISTS
        # ---------------------------------

        if (
            csv_file.exists()
            and
            is_valid_bhavcopy(csv_file)
        ):

            if (
                not parquet_file.exists()
            ):

                try:

                    df = pd.read_csv(
                        csv_file
                    )

                    df.to_parquet(
                        parquet_file,
                        index=False
                    )

                except Exception:
                    pass

            return "SKIPPED"

        # ---------------------------------
        # CORRUPT FILE
        # ---------------------------------

        if csv_file.exists():

            try:
                csv_file.unlink()
            except Exception:
                pass

        try:

            # --------------------------------
            # PRIMARY SOURCE
            # NSELib
            # --------------------------------

            df = fetch_from_nselib(
                trade_date
            )

            source = "NSELIB"

            # --------------------------------
            # FALLBACK
            # NSE ARCHIVE
            # --------------------------------

            if df is None:

                df = await fetch_bhavcopy(
                    session,
                    trade_date
                )

                source = "ARCHIVE"

            logger.info(
                f"{trade_date} | {source}"
            )

            df.to_csv(
                csv_file,
                index=False
            )

            try:

                df.to_parquet(
                    parquet_file,
                    index=False
                )

            except Exception:

                logger.exception(
                    "Parquet Write Failed"
                )

            return "DOWNLOADED"

        except Exception:

            return "FAILED"
            

async def _download_dates(
    trade_dates,
    year: int = 0,
):
    from tqdm import tqdm as _tqdm

    WORKERS = get_optimal_workers()
    semaphore = asyncio.Semaphore(WORKERS)
    total = len(trade_dates)
    downloaded = skipped = failed = 0

    desc = f"  {year}" if year else "  Equity"

    with _tqdm(total=total, desc=desc, ncols=100, leave=True, ascii=True) as pbar:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks = [
                process_day(semaphore, session, td)
                for td in trade_dates
            ]
            for task in asyncio.as_completed(tasks):
                result = await task
                if result == "DOWNLOADED":
                    downloaded += 1
                elif result == "SKIPPED":
                    skipped += 1
                else:
                    failed += 1
                pbar.set_postfix(D=downloaded, S=skipped, F=failed, refresh=False)
                pbar.update(1)

    return {
        "downloaded": downloaded,
        "skipped":    skipped,
        "failed":     failed,
    }


def download_date(
    trade_date
):
    return asyncio.run(
        _download_dates([trade_date], year=trade_date.year)
    )


def download_year(year):
    logger.info(f"Downloading {year}")
    dates = pd.date_range(
        start=f"{year}-01-01",
        end=f"{year}-12-31",
        freq="B",
    )
    return asyncio.run(
        _download_dates([d.date() for d in dates], year=year)
    )
    
def download_year_range(
    start_year,
    end_year
):

    total_downloaded = 0
    total_skipped = 0
    total_failed = 0
    total_years = end_year - start_year + 1

    for idx, year in enumerate(range(start_year, end_year + 1), start=1):
        print(f"Year {year} ({idx}/{total_years}) ...", flush=True)
        result = download_year(year)

        total_downloaded += result["downloaded"]
        total_skipped    += result["skipped"]
        total_failed     += result["failed"]

        print(
            f"  {year} done: D={result['downloaded']} S={result['skipped']} F={result['failed']}",
            flush=True,
        )
        logger.info(
            f"{year} | "
            f"D:{result['downloaded']} "
            f"S:{result['skipped']} "
            f"F:{result['failed']}"
        )

    print()

    print(
        "=" * 70
    )

    print(
        "DOWNLOAD SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        f"Downloaded : "
        f"{total_downloaded}"
    )

    print(
        f"Skipped    : "
        f"{total_skipped}"
    )

    print(
        f"Failed     : "
        f"{total_failed}"
    )

    print(
        "=" * 70
    )

    return {

        "downloaded":
            total_downloaded,

        "skipped":
            total_skipped,

        "failed":
            total_failed,

    }


def refresh_registry():

    logger.info(
        "Building Registry"
    )

    rows = []

    start_date, end_date = (
        compute_validation_range()
    )

    files = []

    for year in range(
        start_date.year,
        end_date.year + 1
    ):

        year_dir = (
            NSE_EQUITY_BHAVCOPY_DIR /
            str(year)
        )

        if year_dir.exists():

            files.extend(

                year_dir.glob(
                    "bhavcopy_*.csv"
                )

            )

    files = sorted(files)

    for file in progress(
        files,
        desc="Registry"
    ):

        status = (
            "VALID"
            if is_valid_bhavcopy(
                file
            )
            else "CORRUPT"
        )

        rows.append({

            "TRADE_DATE":

                file.stem.replace(
                    "bhavcopy_",
                    ""
                ),

            "YEAR":

                file.parent.name,

            "FILE_NAME":

                file.name,

            "FILE_PATH":

                str(file),

            "FILE_SIZE_KB":

                round(
                    file.stat().st_size
                    / 1024,
                    2
                ),

            "STATUS":

                status,

        })

    registry_df = pd.DataFrame(
        rows
    )

    registry_file = (

        BHAVCOPY_DIR /
        "bhavcopy_registry.csv"

    )

    registry_df.to_csv(
        registry_file,
        index=False
    )

    return registry_df


def refresh_coverage():

    logger.info(
        "Building Coverage Report"
    )

    rows = []

    available_years = []

    for year_dir in sorted(

        NSE_EQUITY_BHAVCOPY_DIR.glob(
            "*"
        )

    ):

        if not year_dir.is_dir():
            continue

        files = list(

            year_dir.glob(
                "bhavcopy_*.csv"
            )

        )

        total_files = len(
            files
        )

        if total_files == 0:
            continue

        dates = []

        for file in files:

            try:

                trade_date = (
                    file.stem
                    .replace(
                        "bhavcopy_",
                        ""
                    )
                )

                dates.append(
                    trade_date
                )

            except Exception:
                pass

        rows.append({

            "YEAR":

                year_dir.name,

            "TOTAL_FILES":

                total_files,

            "FIRST_DATE":

                min(dates),

            "LAST_DATE":

                max(dates),

            "STATUS":

                "AVAILABLE",

        })

        available_years.append({

            "YEAR":

                year_dir.name,

            "TOTAL_FILES":

                total_files

        })

    coverage_df = pd.DataFrame(
        rows
    )

    available_df = pd.DataFrame(
        available_years
    )

    coverage_df.to_csv(

        BHAVCOPY_DIR /
        "bhavcopy_coverage_report.csv",

        index=False

    )

    available_df.to_csv(

        BHAVCOPY_DIR /
        "available_years.csv",

        index=False

    )

    return coverage_df


def build_integrity_report():

    logger.info(
        "Building Integrity Report"
    )

    rows = []

    start_date, end_date = (
        compute_validation_range()
    )

    files = []

    for year in range(
        start_date.year,
        end_date.year + 1
    ):

        year_dir = (
            NSE_EQUITY_BHAVCOPY_DIR /
            str(year)
        )

        if year_dir.exists():

            files.extend(

                year_dir.glob(
                    "bhavcopy_*.csv"
                )

            )

    for file in progress(
        files,
        desc="Integrity Scan"
    ):

        rows.append({

            "FILE_NAME":

                file.name,

            "YEAR":

                file.parent.name,

            "STATUS":

                (
                    "VALID"
                    if is_valid_bhavcopy(
                        file
                    )
                    else "CORRUPT"
                )

        })

    integrity_df = pd.DataFrame(
        rows
    )

    integrity_df.to_csv(

        BHAVCOPY_DIR /
        "integrity_report.csv",

        index=False

    )

    return integrity_df
    
    
def refresh_missing_dates():

    logger.info(
        "Building Missing Dates Report"
    )

    start_date, end_date = (
        compute_validation_range()
    )

    expected_dates = {

        d.strftime("%Y%m%d")

        for d in get_trading_days(
            start_date,
            end_date
        )

    }

    available_dates = {

        file.stem.replace(
            "bhavcopy_",
            ""
        )

        for file in
        NSE_EQUITY_BHAVCOPY_DIR.rglob(
            "bhavcopy_*.csv"
        )

    }

    missing_dates = sorted(

        expected_dates
        - available_dates

    )

    missing_df = pd.DataFrame({

        "TRADE_DATE":
            missing_dates,

        "STATUS":
            "MISSING"

    })

    missing_df.to_csv(

        BHAVCOPY_DIR /
        "missing_dates_report.csv",

        index=False

    )

    return missing_df


def validate_archive():

    logger.info(
        "=" * 70
    )

    logger.info(
        "VALIDATING EQUITY ARCHIVE"
    )

    logger.info(
        "=" * 70
    )

    refresh_registry()

    refresh_coverage()

    build_integrity_report()

    refresh_missing_dates()

    logger.info(
        "ARCHIVE VALIDATION COMPLETE"
    )


def incremental_update():

    logger.info(
        "Running Incremental Update"
    )

    result = download_date(
        date.today()
    )

    validate_archive()

    return result


def backfill_missing_dates():

    missing_file = BHAVCOPY_DIR / "missing_dates_report.csv"

    if not missing_file.exists():
        refresh_missing_dates()

    missing_df = pd.read_csv(missing_file)

    if missing_df.empty:
        logger.info("No Missing Dates")
        print("No missing dates to backfill.", flush=True)
        return {"downloaded": 0, "skipped": 0, "failed": 0}

    trade_dates = [
        pd.to_datetime(str(d), format="%Y%m%d").date()
        for d in missing_df["TRADE_DATE"]
    ]

    logger.info(f"Backfilling {len(trade_dates)} dates")
    print(f"Backfilling {len(trade_dates)} missing dates ...", flush=True)

    # Group by year so each year gets its own tqdm bar (matches GUI progress regex)
    from collections import defaultdict
    by_year = defaultdict(list)
    for td in trade_dates:
        by_year[td.year].append(td)

    total_downloaded = total_skipped = total_failed = 0
    for year in sorted(by_year):
        result = asyncio.run(_download_dates(by_year[year], year=year))
        total_downloaded += result["downloaded"]
        total_skipped    += result["skipped"]
        total_failed     += result["failed"]
        print(
            f"  {year} done: D={result['downloaded']} S={result['skipped']} F={result['failed']}",
            flush=True,
        )

    return {
        "downloaded": total_downloaded,
        "skipped":    total_skipped,
        "failed":     total_failed,
    }


def print_summary():

    registry_file = (

        BHAVCOPY_DIR /
        "bhavcopy_registry.csv"

    )

    if not registry_file.exists():
        return

    registry = pd.read_csv(
        registry_file
    )

    total_files = len(
        registry
    )

    valid_files = len(

        registry[
            registry["STATUS"]
            == "VALID"
        ]

    )

    corrupt_files = len(

        registry[
            registry["STATUS"]
            == "CORRUPT"
        ]

    )

    print()

    print(
        "=" * 70
    )

    print(
        "NSE EQUITY ACQUISITION SUMMARY"
    )

    print(
        "=" * 70
    )

    print(
        f"Total Files   : "
        f"{total_files}"
    )

    print(
        f"Valid Files   : "
        f"{valid_files}"
    )

    print(
        f"Corrupt Files : "
        f"{corrupt_files}"
    )

    print(
        "=" * 70
    )

    print()


def main():

    print("=" * 60, flush=True)
    print("NSE EQUITY BHAVCOPY ACQUISITION ENGINE", flush=True)
    print("=" * 60, flush=True)

    # Step 1: validate and find missing dates
    validate_archive()

    # Step 2: download all missing dates (grouped by year for progress bars)
    result = backfill_missing_dates()

    # Step 3: re-validate so reports reflect freshly downloaded files
    if result and result.get("downloaded", 0) > 0:
        validate_archive()

    print_summary()


if __name__ == "__main__":
    main()
from pathlib import Path
from datetime import datetime, timedelta
import time
import sys

import pandas as pd
from nselib.derivatives import fno_bhav_copy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger
from engines.common.progress import progress
from engines.common.config import API_DELAY

logger = get_logger("nse_fno_acquisition")

FNO_ROOT = (
    ROOT
    / "data"
    / "NSE"
    / "bhavcopy"
    / "fno"
)

REGISTRY_FILE = (
    FNO_ROOT
    / "fno_registry.csv"
)

COVERAGE_FILE = (
    FNO_ROOT
    / "fno_coverage_report.csv"
)

MISSING_FILE = (
    FNO_ROOT
    / "fno_missing_dates.csv"
)

AVAILABLE_YEARS_FILE = (
    FNO_ROOT
    / "available_years.csv"
)

FNO_ROOT.mkdir(
    parents=True,
    exist_ok=True
)


def get_output_file(trade_date):

    year_dir = (
        FNO_ROOT
        / str(trade_date.year)
    )

    year_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return (
        year_dir
        / f"fo_{trade_date.strftime('%Y%m%d')}.csv"
    )


def save_fno_bhavcopy(
    trade_date,
    overwrite=False
):

    output_file = get_output_file(
        trade_date
    )

    if (
        output_file.exists()
        and not overwrite
    ):

        return "SKIPPED"

    try:

        date_str = trade_date.strftime(
            "%d-%m-%Y"
        )

        df = fno_bhav_copy(
            date_str
        )

        if (
            df is None
            or len(df) == 0
        ):
            return "FAILED"

        df.to_csv(
            output_file,
            index=False
        )

        return "DOWNLOADED"

    except Exception as e:

        logger.warning(
            f"{trade_date} : {e}"
        )

        return "FAILED"


def download_date_range(
    start_date,
    end_date,
    overwrite=False
):

    trading_days = []

    current = start_date

    while current <= end_date:

        if current.weekday() < 5:
            trading_days.append(
                current
            )

        current += timedelta(days=1)

    downloaded = 0
    skipped = 0
    failed = 0

    for trade_date in progress(
        trading_days,
        total=len(trading_days),
        desc="F&O Download"
    ):

        status = save_fno_bhavcopy(
            trade_date,
            overwrite
        )

        if status == "DOWNLOADED":
            downloaded += 1

        elif status == "SKIPPED":
            skipped += 1

        else:
            failed += 1

        time.sleep(API_DELAY)

    print()
    print("=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)
    print(f"Downloaded : {downloaded:,}")
    print(f"Skipped    : {skipped:,}")
    print(f"Failed     : {failed:,}")
    print("=" * 70)

    return {
        "downloaded": downloaded,
        "skipped": skipped,
        "failed": failed
    }


def download_year(
    year,
    overwrite=False
):

    start_date = datetime(
        year,
        1,
        1
    )

    end_date = datetime(
        year,
        12,
        31
    )

    return download_date_range(
        start_date,
        end_date,
        overwrite
    )


def download_year_range(
    start_year,
    end_year,
    overwrite=False
):

    total_downloaded = 0
    total_skipped = 0
    total_failed = 0

    years = list(
        range(
            start_year,
            end_year + 1
        )
    )

    for year in progress(
        years,
        total=len(years),
        desc="Year Backfill"
    ):

        logger.info(
            f"Downloading Year {year}"
        )

        result = download_year(
            year,
            overwrite
        )

        total_downloaded += result[
            "downloaded"
        ]

        total_skipped += result[
            "skipped"
        ]

        total_failed += result[
            "failed"
        ]

    print()
    print("=" * 70)
    print("BACKFILL SUMMARY")
    print("=" * 70)
    print(
        f"Downloaded : {total_downloaded:,}"
    )
    print(
        f"Skipped    : {total_skipped:,}"
    )
    print(
        f"Failed     : {total_failed:,}"
    )
    print("=" * 70)

    refresh_reports()

    return {
        "downloaded": total_downloaded,
        "skipped": total_skipped,
        "failed": total_failed
    }


def build_registry():

    rows = []
    years = []

    for year_dir in sorted(
        FNO_ROOT.iterdir()
    ):

        if not year_dir.is_dir():
            continue

        try:
            years.append(
                int(year_dir.name)
            )
        except Exception:
            continue

        for file in sorted(
            year_dir.glob(
                "fo_*.csv"
            )
        ):

            try:

                trade_date = (
                    datetime.strptime(
                        file.stem.replace(
                            "fo_",
                            ""
                        ),
                        "%Y%m%d"
                    ).date()
                )

                rows.append({

                    "TRADE_DATE":
                    trade_date,

                    "YEAR":
                    trade_date.year,

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
                    "AVAILABLE"
                })

            except Exception:
                continue

    registry = pd.DataFrame(
        rows
    )

    registry.to_csv(
        REGISTRY_FILE,
        index=False
    )

    pd.DataFrame({
        "YEAR": sorted(years)
    }).to_csv(
        AVAILABLE_YEARS_FILE,
        index=False
    )

    return registry


def build_coverage_report(
    registry
):

    if registry.empty:

        pd.DataFrame().to_csv(
            COVERAGE_FILE,
            index=False
        )

        return

    rows = []

    for year in sorted(
        registry["YEAR"].unique()
    ):

        temp = registry[
            registry["YEAR"] == year
        ]

        rows.append({

            "YEAR":
            year,

            "TOTAL_FILES":
            len(temp),

            "FIRST_DATE":
            temp["TRADE_DATE"].min(),

            "LAST_DATE":
            temp["TRADE_DATE"].max()

        })

    pd.DataFrame(
        rows
    ).to_csv(
        COVERAGE_FILE,
        index=False
    )


def build_missing_dates_report(
    registry
):

    if registry.empty:

        pd.DataFrame().to_csv(
            MISSING_FILE,
            index=False
        )

        return

    available_dates = set(
        pd.to_datetime(
            registry["TRADE_DATE"]
        ).dt.date
    )

    start_date = min(
        available_dates
    )

    end_date = max(
        available_dates
    )

    rows = []

    current = start_date

    while current <= end_date:

        if (
            current.weekday() < 5
            and current not in available_dates
        ):

            rows.append({

                "TRADE_DATE":
                current,

                "STATUS":
                "MISSING"

            })

        current += timedelta(days=1)

    pd.DataFrame(
        rows
    ).to_csv(
        MISSING_FILE,
        index=False
    )


def refresh_reports():

    registry = build_registry()

    build_coverage_report(
        registry
    )

    build_missing_dates_report(
        registry
    )

    return registry


def main():

    registry = refresh_reports()

    print()
    print("=" * 70)
    print("NSE F&O ACQUISITION ENGINE")
    print("=" * 70)
    print(
        f"Files : {len(registry):,}"
    )

    print(
        f"Years : "
        f"{registry['YEAR'].nunique() if not registry.empty else 0}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
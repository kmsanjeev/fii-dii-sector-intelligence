from pathlib import Path
from datetime import datetime
import pandas as pd
import re


# ==========================================================
# CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_ROOT = Path(r"D:\Projects\NSE Data")

OUTPUT_DIR = PROJECT_ROOT / "data" / "NSE" / "bhavcopy"

LOG_DIR = PROJECT_ROOT / "logs" / "bhavcopy_import"

REGISTRY_FILE = OUTPUT_DIR / "bhavcopy_registry.csv"
COVERAGE_FILE = OUTPUT_DIR / "bhavcopy_coverage_report.csv"
AVAILABLE_YEARS_FILE = OUTPUT_DIR / "available_years.csv"
MISSING_YEARS_FILE = OUTPUT_DIR / "missing_years_report.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "bhavcopy_import.log"

FILE_PATTERN = re.compile(r"bhavcopy_(\d{8})\.csv$", re.IGNORECASE)


# ==========================================================
# LOGGING
# ==========================================================

def write_log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")


# ==========================================================
# YEAR DISCOVERY
# ==========================================================

def get_available_year_folders():
    years = []

    for item in SOURCE_ROOT.iterdir():

        if not item.is_dir():
            continue

        try:
            year = int(item.name)

            if 1900 <= year <= 2100:
                years.append(year)

        except ValueError:
            continue

    return sorted(years)


# ==========================================================
# FILE REGISTRY
# ==========================================================

def build_registry(years):

    registry_rows = []
    coverage_rows = []
    available_year_rows = []

    for year in years:

        year_folder = SOURCE_ROOT / str(year)

        csv_files = sorted(
            year_folder.glob("bhavcopy_*.csv")
        )

        if not csv_files:
            continue

        dates = []

        for file_path in csv_files:

            match = FILE_PATTERN.match(file_path.name)

            if not match:
                continue

            try:

                trade_date = datetime.strptime(
                    match.group(1),
                    "%Y%m%d"
                ).date()

                file_size_kb = round(
                    file_path.stat().st_size / 1024,
                    2
                )

                registry_rows.append(
                    {
                        "TRADE_DATE": trade_date,
                        "YEAR": year,
                        "FILE_NAME": file_path.name,
                        "FILE_PATH": str(file_path),
                        "FILE_SIZE_KB": file_size_kb,
                        "STATUS": "VALID"
                    }
                )

                dates.append(trade_date)

            except Exception:

                registry_rows.append(
                    {
                        "TRADE_DATE": None,
                        "YEAR": year,
                        "FILE_NAME": file_path.name,
                        "FILE_PATH": str(file_path),
                        "FILE_SIZE_KB": 0,
                        "STATUS": "INVALID"
                    }
                )

        if dates:

            coverage_rows.append(
                {
                    "YEAR": year,
                    "TOTAL_FILES": len(dates),
                    "FIRST_DATE": min(dates),
                    "LAST_DATE": max(dates),
                    "STATUS": "AVAILABLE"
                }
            )

            available_year_rows.append(
                {
                    "YEAR": year,
                    "TOTAL_FILES": len(dates)
                }
            )

    registry_df = pd.DataFrame(registry_rows)

    coverage_df = pd.DataFrame(coverage_rows)

    available_years_df = pd.DataFrame(
        available_year_rows
    )

    return (
        registry_df,
        coverage_df,
        available_years_df
    )


# ==========================================================
# MISSING YEARS REPORT
# ==========================================================

def build_missing_year_report(years):

    if not years:
        return pd.DataFrame()

    min_year = min(years)
    max_year = datetime.now().year

    expected_years = set(
        range(min_year, max_year + 1)
    )

    missing_years = sorted(
        expected_years - set(years)
    )

    rows = []

    for year in missing_years:

        rows.append(
            {
                "YEAR": year,
                "STATUS": "MISSING"
            }
        )

    return pd.DataFrame(rows)


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("\n===================================")
    print("BHAVCOPY IMPORT ENGINE")
    print("===================================\n")

    write_log("START")

    years = get_available_year_folders()

    print(f"Years Discovered : {len(years)}")
    print(
        f"Year Range       : {min(years)} - {max(years)}"
    )

    write_log(
        f"Years Discovered = {years}"
    )

    (
        registry_df,
        coverage_df,
        available_years_df
    ) = build_registry(years)

    missing_years_df = build_missing_year_report(
        years
    )

    registry_df.to_csv(
        REGISTRY_FILE,
        index=False
    )

    coverage_df.to_csv(
        COVERAGE_FILE,
        index=False
    )

    available_years_df.to_csv(
        AVAILABLE_YEARS_FILE,
        index=False
    )

    missing_years_df.to_csv(
        MISSING_YEARS_FILE,
        index=False
    )

    write_log(
        f"Registry Rows = {len(registry_df)}"
    )

    write_log(
        f"Coverage Years = {len(coverage_df)}"
    )

    write_log("COMPLETE")

    print("\nCompleted Successfully\n")

    print(
        f"Registry Rows : {len(registry_df)}"
    )

    print(
        f"Coverage Years : {len(coverage_df)}"
    )

    print(
        f"Missing Years : {len(missing_years_df)}"
    )

    print(
        f"\nOutput : {REGISTRY_FILE}"
    )


if __name__ == "__main__":
    main()
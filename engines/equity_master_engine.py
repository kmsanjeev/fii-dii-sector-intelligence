from pathlib import Path
from datetime import datetime

import pandas as pd
from nselib import capital_market


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = PROJECT_ROOT / "data" / "NSE" / "equity_master"
REPORT_DIR = OUTPUT_DIR / "reports"
LOG_DIR = PROJECT_ROOT / "logs" / "equity_master"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def save_log(message: str):
    log_file = LOG_DIR / "equity_master.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")


def fetch_equity_universe() -> pd.DataFrame:
    print("Fetching NSE equity universe...")

    df = capital_market.equity_list()

    # --------------------------------------------------
    # Normalize NSE column names
    # --------------------------------------------------

    df.columns = [str(col).strip() for col in df.columns]

    save_log(f"Detected Columns: {list(df.columns)}")

    rename_map = {
        "NAME OF COMPANY": "COMPANY_NAME",
        "DATE OF LISTING": "LISTING_DATE",
        "FACE VALUE": "FACE_VALUE",
        "ISIN NUMBER": "ISIN",
    }

    df = df.rename(columns=rename_map)

    if "ISIN" not in df.columns:
        df["ISIN"] = None

    required_columns = [
        "SYMBOL",
        "COMPANY_NAME",
        "SERIES",
        "LISTING_DATE",
        "ISIN",
        "FACE_VALUE",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        save_log(
            f"Missing Columns: {missing_columns}"
        )

        for col in missing_columns:
            df[col] = None

    df = df[required_columns].copy()

    df["LISTING_DATE"] = pd.to_datetime(
        df["LISTING_DATE"],
        format="%d-%b-%Y",
        errors="coerce",
    )

    df["IS_ACTIVE"] = True
    df["DATA_SOURCE"] = "NSELIB"

    return df


def generate_reports(df: pd.DataFrame):

    summary = pd.DataFrame(
        {
            "Metric": [
                "TOTAL_SYMBOLS",
                "ACTIVE_SYMBOLS",
                "UNIQUE_SERIES",
            ],
            "Value": [
                len(df),
                int(df["IS_ACTIVE"].sum()),
                int(df["SERIES"].nunique()),
            ],
        }
    )

    summary.to_csv(
        REPORT_DIR / "mapping_coverage_report.csv",
        index=False,
    )

    series_distribution = (
        df.groupby("SERIES")
        .size()
        .reset_index(name="COUNT")
        .sort_values("COUNT", ascending=False)
    )

    series_distribution.to_csv(
        REPORT_DIR / "series_distribution.csv",
        index=False,
    )


def main():

    df = fetch_equity_universe()

    output_file = (
        OUTPUT_DIR / "equity_master.csv"
    )

    df.to_csv(
        output_file,
        index=False,
    )

    generate_reports(df)

    save_log(
        f"Equity Master Generated | Symbols={len(df)}"
    )

    print("\nDone")
    print(f"Symbols : {len(df)}")
    print(f"Output  : {output_file}")


if __name__ == "__main__":
    main()
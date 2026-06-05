from pathlib import Path
from datetime import datetime

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

EQUITY_MASTER_FILE = (
    PROJECT_ROOT
    / "data"
    / "NSE"
    / "equity_master"
    / "equity_master.csv"
)

CLASSIFICATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "company_classification.csv"
)

REVIEW_QUEUE_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "classification_review_queue.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "cache"
    / "reports"
    / "classification_coverage_report.csv"
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
    / "classification_engine"
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = (
    LOG_DIR
    / "classification_engine.log"
)


def write_log(message):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{timestamp} | {message}\n"
        )


def load_classification():

    if (
        not CLASSIFICATION_FILE.exists()
        or
        CLASSIFICATION_FILE.stat().st_size == 0
    ):

        return pd.DataFrame(
            columns=[
                "SYMBOL",
                "SECTOR_NAME",
                "SOURCE",
                "LAST_UPDATED"
            ]
        )

    return pd.read_csv(
        CLASSIFICATION_FILE
    )


def main():

    print(
        "\nCLASSIFICATION ENGINE\n"
    )

    equity_df = pd.read_csv(
        EQUITY_MASTER_FILE
    )

    class_df = load_classification()

    equity_symbols = set(
        equity_df["SYMBOL"]
    )

    classified_symbols = set(
        class_df["SYMBOL"]
    )

    pending_symbols = (
        equity_symbols
        - classified_symbols
    )

    queue_df = (
        equity_df[
            equity_df["SYMBOL"].isin(
                pending_symbols
            )
        ][
            [
                "SYMBOL",
                "COMPANY_NAME"
            ]
        ]
        .copy()
    )

    queue_df["STATUS"] = (
        "PENDING"
    )

    queue_df = queue_df.sort_values(
        "SYMBOL"
    )

    queue_df.to_csv(
        REVIEW_QUEUE_FILE,
        index=False
    )

    total_symbols = len(
        equity_symbols
    )

    classified_count = len(
        classified_symbols
    )

    pending_count = len(
        pending_symbols
    )

    coverage = round(
        (
            classified_count
            /
            total_symbols
        ) * 100,
        2
    )

    report_df = pd.DataFrame(
        {
            "METRIC": [
                "TOTAL_SYMBOLS",
                "CLASSIFIED_SYMBOLS",
                "PENDING_SYMBOLS",
                "COVERAGE_PERCENT"
            ],
            "VALUE": [
                total_symbols,
                classified_count,
                pending_count,
                coverage
            ]
        }
    )

    report_df.to_csv(
        REPORT_FILE,
        index=False
    )

    write_log(
        f"Total={total_symbols}"
    )

    write_log(
        f"Classified={classified_count}"
    )

    write_log(
        f"Pending={pending_count}"
    )

    print(
        f"Total Symbols      : {total_symbols}"
    )

    print(
        f"Classified Symbols : {classified_count}"
    )

    print(
        f"Pending Symbols    : {pending_count}"
    )

    print(
        f"Coverage %         : {coverage}"
    )


if __name__ == "__main__":
    main()
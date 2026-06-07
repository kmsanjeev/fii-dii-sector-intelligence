from pathlib import Path
from datetime import datetime

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "intelligence"
    / "index_strength.csv"
)

HISTORY_DIR = (
    PROJECT_ROOT
    / "data"
    / "intelligence"
    / "history"
)

SNAPSHOT_FILE = (
    HISTORY_DIR
    / "index_snapshot.csv"
)

REGISTRY_FILE = (
    HISTORY_DIR
    / "snapshot_registry.csv"
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
    / "index_snapshot"
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = (
    LOG_DIR
    / "index_snapshot.log"
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


def validate_input(df):

    required_columns = [
        "INDEX_NAME",
        "CATEGORY",
        "RETURN_30D",
        "RETURN_365D",
        "MOMENTUM_SCORE",
        "RANK"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing Columns: {missing}"
        )

    if len(df) == 0:

        raise ValueError(
            "Input file contains zero rows"
        )


def load_existing_snapshot():

    if SNAPSHOT_FILE.exists():

        try:

            return pd.read_csv(
                SNAPSHOT_FILE
            )

        except Exception:

            return pd.DataFrame()

    return pd.DataFrame()


def load_registry():

    if REGISTRY_FILE.exists():

        try:

            return pd.read_csv(
                REGISTRY_FILE
            )

        except Exception:

            return pd.DataFrame()

    return pd.DataFrame()


def main():

    print(
        "\nINDEX SNAPSHOT ENGINE\n"
    )

    write_log("START")

    if not SOURCE_FILE.exists():

        raise FileNotFoundError(
            f"{SOURCE_FILE} not found"
        )

    snapshot_date = (
        datetime.now()
        .strftime("%Y-%m-%d")
    )

    source_df = pd.read_csv(
        SOURCE_FILE
    )

    validate_input(
        source_df
    )

    write_log(
        f"Snapshot Date={snapshot_date}"
    )

    existing = (
        load_existing_snapshot()
    )

    if (
        not existing.empty
        and "SNAPSHOT_DATE"
        in existing.columns
    ):

        existing_dates = set(
            existing[
                "SNAPSHOT_DATE"
            ]
            .astype(str)
        )

        if snapshot_date in existing_dates:

            print(
                "Snapshot already exists."
            )

            write_log(
                "DUPLICATE_SKIPPED"
            )

            return

    snapshot = source_df.copy()

    snapshot.insert(
        0,
        "SNAPSHOT_DATE",
        snapshot_date
    )

    if existing.empty:

        final_snapshot = snapshot

    else:

        final_snapshot = pd.concat(
            [
                existing,
                snapshot
            ],
            ignore_index=True
        )

    final_snapshot.to_csv(
        SNAPSHOT_FILE,
        index=False
    )

    registry = load_registry()

    registry_row = pd.DataFrame(
        [
            {
                "SNAPSHOT_DATE":
                snapshot_date,

                "ROWS_INSERTED":
                len(snapshot)
            }
        ]
    )

    if registry.empty:

        registry = registry_row

    else:

        registry = pd.concat(
            [
                registry,
                registry_row
            ],
            ignore_index=True
        )

    registry.to_csv(
        REGISTRY_FILE,
        index=False
    )

    write_log(
        f"Rows Added={len(snapshot)}"
    )

    write_log("COMPLETE")

    print(
        f"Snapshot Date : {snapshot_date}"
    )

    print(
        f"Rows Added    : {len(snapshot)}"
    )

    print(
        "\nOutput:"
    )

    print(
        SNAPSHOT_FILE
    )


if __name__ == "__main__":
    main()
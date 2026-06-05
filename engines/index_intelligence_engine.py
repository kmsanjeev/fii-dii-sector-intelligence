from pathlib import Path
from datetime import datetime

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INDEX_FILE = (
    PROJECT_ROOT
    / "data"
    / "NSE"
    / "indices"
    / "MW-All-Indices-05-Jun-2026.csv"
)

INDEX_MASTER_FILE = (
    PROJECT_ROOT
    / "data"
    / "reference"
    / "index_master.csv"
)

INTELLIGENCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "intelligence"
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
    / "index_intelligence"
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = (
    LOG_DIR
    / "index_intelligence.log"
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


def clean_percent(series):

    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("-", "0")
        .astype(float)
    )


def main():

    print("\nINDEX INTELLIGENCE ENGINE\n")

    df = pd.read_csv(INDEX_FILE)

    taxonomy = pd.read_csv(
        INDEX_MASTER_FILE
    )

    df.columns = [
        col.strip()
        for col in df.columns
    ]

    index_col = [
        c for c in df.columns
        if c.startswith("INDEX")
    ][0]

    ret30_col = [
        c for c in df.columns
        if c.startswith("30 D % CHNG")
    ][0]

    ret365_col = [
        c for c in df.columns
        if c.startswith("365 D % CHNG")
    ][0]

    result = pd.DataFrame()

    result["INDEX_NAME"] = df[index_col]

    result["RETURN_30D"] = clean_percent(
        df[ret30_col]
    )

    result["RETURN_365D"] = clean_percent(
        df[ret365_col]
    )

    result["MOMENTUM_SCORE"] = (
        result["RETURN_30D"] * 0.70
        +
        result["RETURN_365D"] * 0.30
    ).round(2)

    result = result.merge(
        taxonomy,
        on="INDEX_NAME",
        how="left"
    )

    result = result.sort_values(
        "MOMENTUM_SCORE",
        ascending=False
    )

    result["RANK"] = range(
        1,
        len(result) + 1
    )

    # -------------------------------------------------
    # MASTER OUTPUTS
    # -------------------------------------------------

    result.to_csv(
        INTELLIGENCE_DIR
        / "index_strength.csv",
        index=False
    )

    result.to_csv(
        INTELLIGENCE_DIR
        / "index_momentum.csv",
        index=False
    )

    # -------------------------------------------------
    # SECTOR ROTATION
    # -------------------------------------------------

    sector_df = result[
        result["CATEGORY"]
        == "SECTOR"
    ].copy()

    sector_df = sector_df.sort_values(
        "MOMENTUM_SCORE",
        ascending=False
    )

    sector_df["RANK"] = range(
        1,
        len(sector_df) + 1
    )

    sector_df.to_csv(
        INTELLIGENCE_DIR
        / "sector_rotation.csv",
        index=False
    )

    # -------------------------------------------------
    # THEME ROTATION
    # -------------------------------------------------

    theme_df = result[
        result["CATEGORY"]
        == "THEME"
    ].copy()

    theme_df = theme_df.sort_values(
        "MOMENTUM_SCORE",
        ascending=False
    )

    theme_df["RANK"] = range(
        1,
        len(theme_df) + 1
    )

    theme_df.to_csv(
        INTELLIGENCE_DIR
        / "theme_rotation.csv",
        index=False
    )

    write_log(
        f"Indices={len(result)}"
    )

    write_log(
        f"Sectors={len(sector_df)}"
    )

    write_log(
        f"Themes={len(theme_df)}"
    )

    print(
        f"Total Indices   : {len(result)}"
    )

    print(
        f"Sector Indices  : {len(sector_df)}"
    )

    print(
        f"Theme Indices   : {len(theme_df)}"
    )

    print("\nOutputs Generated")

    print(
        "index_strength.csv"
    )

    print(
        "index_momentum.csv"
    )

    print(
        "sector_rotation.csv"
    )

    print(
        "theme_rotation.csv"
    )


if __name__ == "__main__":
    main()
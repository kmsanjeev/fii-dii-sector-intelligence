from pathlib import Path
from datetime import datetime
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger

logger = get_logger("industry_master")

FUNDAMENTALS = (
    ROOT
    / "data"
    / "reference"
    / "company_fundamentals_master.csv"
)

CLASSIFICATION = (
    ROOT
    / "data"
    / "reference"
    / "company_classification.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "reference"
    / "industry_master.csv"
)


def normalize_industry(name):

    if pd.isna(name):
        return None

    name = str(name).strip()

    if name == "":
        return None

    return name


def main():

    logger.info("Loading datasets")

    fundamentals = pd.read_csv(FUNDAMENTALS)
    classification = pd.read_csv(CLASSIFICATION)

    if "INDUSTRY" not in fundamentals.columns:
        print(
            "\nERROR: INDUSTRY column not found in "
            "company_fundamentals_master.csv"
        )
        return

    merged = fundamentals.merge(
        classification[
            [
                "SYMBOL",
                "SECTOR"
            ]
        ],
        on="SYMBOL",
        how="left",
        suffixes=("", "_CLASS")
    )

    merged["SECTOR"] = merged["SECTOR"].fillna(
        merged["SECTOR_CLASS"]
    )

    industry_master = (
        merged[
            [
                "INDUSTRY",
                "SECTOR"
            ]
        ]
        .dropna()
        .drop_duplicates()
    )

    industry_master["INDUSTRY"] = (
        industry_master["INDUSTRY"]
        .apply(normalize_industry)
    )

    industry_master = (
        industry_master
        .dropna()
        .copy()
    )

    counts = (
        merged.groupby("INDUSTRY")
        .size()
        .reset_index(name="COMPANY_COUNT")
    )

    industry_master = industry_master.merge(
        counts,
        on="INDUSTRY",
        how="left"
    )

    industry_master["THEME"] = None

    industry_master["SOURCE"] = "FOUNDATION_V1"

    industry_master["LAST_UPDATED"] = (
        datetime.now().strftime("%Y-%m-%d")
    )

    industry_master = industry_master.sort_values(
        [
            "SECTOR",
            "INDUSTRY"
        ]
    )

    industry_master.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print("INDUSTRY MASTER COMPLETE")
    print("=" * 70)
    print(
        f"Industries : {len(industry_master):,}"
    )
    print(
        f"Output     : {OUTPUT_FILE}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
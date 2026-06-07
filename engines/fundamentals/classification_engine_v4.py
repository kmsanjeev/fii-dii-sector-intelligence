from pathlib import Path
from datetime import datetime
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("classification_v4")

MAPPING_FILE = (
    ROOT
    / "data"
    / "reference"
    / "mapping"
    / "company_name_mapping.csv"
)

SCREENER_FILE = (
    ROOT
    / "screener_csv"
    / "master_screener_universe.csv"
)

THEME_MAPPING_FILE = (
    ROOT
    / "data"
    / "reference"
    / "theme_sector_mapping.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "reference"
    / "company_classification_v4.csv"
)

COVERAGE_FILE = (
    ROOT
    / "data"
    / "reference"
    / "classification_v4_coverage.csv"
)


def normalize(text):

    if pd.isna(text):
        return ""

    return (
        str(text)
        .upper()
        .strip()
    )


def clean_theme(sector_file):

    if pd.isna(sector_file):
        return ""

    return (
        str(sector_file)
        .replace("_Companies.csv", "")
        .replace("_", " ")
        .replace("&", "AND")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "")
        .upper()
        .strip()
    )


def main():

    logger.info("Loading Mapping")

    mapping = pd.read_csv(
        MAPPING_FILE,
        dtype=str
    ).fillna("")

    logger.info("Loading Screener")

    screener = pd.read_csv(
        SCREENER_FILE,
        dtype=str
    ).fillna("")

    logger.info("Loading Theme Mapping")

    theme_map = pd.read_csv(
        THEME_MAPPING_FILE,
        dtype=str
    ).fillna("")

    theme_lookup = {}

    for row in theme_map.itertuples(index=False):

        theme_lookup[
            normalize(row.THEME)
        ] = row.SECTOR

    screener_lookup = {}

    for row in screener.itertuples(index=False):

        company = normalize(
            row.Name
        )

        theme = clean_theme(
            row.SectorFile
        )

        screener_lookup[
            company
        ] = theme

    records = []

    classified = 0

    for row in progress(
        mapping.itertuples(index=False),
        total=len(mapping),
        desc="Classification V4"
    ):

        screener_name = normalize(
            row.COMPANY_NAME_SCREENER
        )

        theme = screener_lookup.get(
            screener_name,
            ""
        )

        sector = theme_lookup.get(
            theme,
            "UNCLASSIFIED"
        )

        if sector != "UNCLASSIFIED":
            classified += 1

        records.append({

            "SYMBOL":
                row.SYMBOL,

            "COMPANY_NAME":
                row.COMPANY_NAME_NSE,

            "SECTOR":
                sector,

            "THEME":
                theme,

            "SOURCE":
                "SCREENER_V4",

            "LAST_UPDATED":
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
        })

    output = pd.DataFrame(records)

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    total = len(output)

    coverage = round(
        classified * 100 / total,
        2
    )

    pd.DataFrame([{

        "TOTAL_RECORDS":
            total,

        "CLASSIFIED":
            classified,

        "UNCLASSIFIED":
            total - classified,

        "COVERAGE_PERCENT":
            coverage

    }]).to_csv(
        COVERAGE_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("CLASSIFICATION V4 COMPLETE")
    print("=" * 70)
    print(f"Records      : {total:,}")
    print(f"Classified   : {classified:,}")
    print(f"Coverage     : {coverage}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
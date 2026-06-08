from pathlib import Path
from datetime import datetime
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("theme_master")

SCREENER_DIR = (
    ROOT
    / "screener_csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "reference"
    / "theme_master.csv"
)

COVERAGE_FILE = (
    ROOT
    / "data"
    / "reference"
    / "theme_coverage_report.csv"
)


SECTOR_RULES = {

    "BANK": "BANKING",
    "NBFC": "FINANCIAL_SERVICES",
    "FINANCIAL": "FINANCIAL_SERVICES",
    "INSURANCE": "FINANCIAL_SERVICES",
    "BROKING": "FINANCIAL_SERVICES",

    "PHARMA": "PHARMA",
    "PHARMACEUTICAL": "PHARMA",
    "BIOTECH": "PHARMA",

    "HOSPITAL": "HEALTHCARE",
    "HEALTHCARE": "HEALTHCARE",
    "MEDICAL": "HEALTHCARE",

    "POWER": "POWER",

    "DEFENSE": "DEFENCE",
    "AEROSPACE": "DEFENCE",

    "AUTO": "AUTO",

    "CHEMICAL": "CHEMICALS",
    "FERTILIZER": "CHEMICALS",
    "AGROCHEMICAL": "CHEMICALS",

    "SOFTWARE": "IT",
    "IT ENABLED": "IT",
    "COMPUTER": "IT",
    "TECHNOLOGY": "IT",

    "CEMENT": "CEMENT",

    "STEEL": "METALS",
    "METAL": "METALS",
    "ALUMINIUM": "METALS",
    "COPPER": "METALS",
    "ZINC": "METALS",

    "REAL ESTATE": "REALTY",
    "RESIDENTIAL": "REALTY",

    "LOGISTICS": "LOGISTICS",
    "TRANSPORT": "LOGISTICS",

    "FMCG": "FMCG",
    "FOOD": "FMCG",
    "BEVERAGE": "FMCG",
    "DAIRY": "FMCG",

    "INFRA": "INFRASTRUCTURE",
    "CONSTRUCTION": "INFRASTRUCTURE",

    "RETAIL": "RETAIL"
}


def derive_sector(theme):

    theme_upper = theme.upper()

    for keyword, sector in SECTOR_RULES.items():

        if keyword in theme_upper:
            return sector

    return "UNCLASSIFIED"


def clean_theme(filename):

    theme = filename.replace(
        "_Companies.csv",
        ""
    )

    theme = (
        theme
        .replace("_", " ")
        .replace("&", "AND")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "")
        .upper()
        .strip()
    )

    return theme


def main():

    files = [
        f
        for f in SCREENER_DIR.glob("*.csv")
        if f.name.lower() != "master_screener_universe.csv"
    ]

    records = []

    for file in progress(
        files,
        total=len(files),
        desc="Theme Master"
    ):

        theme = clean_theme(
            file.name
        )

        sector = derive_sector(
            theme
        )

        records.append({

            "THEME": theme,

            "SECTOR": sector,

            "SOURCE_FILE": file.name,

            "LAST_UPDATED":
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
        })

    output = pd.DataFrame(records)

    output = output.sort_values(
        "THEME"
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    total = len(output)

    classified = len(
        output[
            output["SECTOR"]
            !=
            "UNCLASSIFIED"
        ]
    )

    coverage = round(
        classified * 100 / total,
        2
    )

    pd.DataFrame([{

        "TOTAL_THEMES":
            total,

        "CLASSIFIED_THEMES":
            classified,

        "UNCLASSIFIED_THEMES":
            total - classified,

        "COVERAGE_PERCENT":
            coverage

    }]).to_csv(
        COVERAGE_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("THEME MASTER COMPLETE")
    print("=" * 70)
    print(f"Total Themes      : {total:,}")
    print(f"Classified        : {classified:,}")
    print(f"Coverage          : {coverage}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
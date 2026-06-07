from pathlib import Path
from datetime import datetime
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("screener_classification")

EQUITY_MASTER = ROOT / "data" / "NSE" / "equity_master" / "equity_master.csv"
MAPPING_FILE = ROOT / "data" / "reference" / "mapping" / "company_name_mapping.csv"
SCREENER_FILE = ROOT / "screener_csv" / "master_screener_universe.csv"

THEME_MAPPING_FILE = (
    ROOT
    / "data"
    / "reference"
    / "theme_sector_mapping.csv"
)

OUTPUT_FILE = ROOT / "data" / "reference" / "company_classification_v3.csv"
REVIEW_FILE = ROOT / "data" / "reference" / "classification_review_queue.csv"
COVERAGE_FILE = ROOT / "data" / "reference" / "classification_coverage_report.csv"


def clean_theme(sector_file):

    if pd.isna(sector_file):
        return None

    theme = str(sector_file)

    theme = theme.replace(".csv", "")
    theme = theme.replace("_Companies", "")
    theme = theme.replace("_", " ")
    theme = theme.replace("&", "AND")

    return theme.upper().strip()


def main():

    logger.info("Loading datasets")

    equity = pd.read_csv(EQUITY_MASTER)
    mapping = pd.read_csv(MAPPING_FILE)
    screener = pd.read_csv(SCREENER_FILE)
    theme_mapping = pd.read_csv(THEME_MAPPING_FILE)

    theme_lookup = dict(
        zip(
            theme_mapping["THEME"].astype(str).str.upper(),
            theme_mapping["SECTOR"]
        )
    )

    screener_lookup = {}

    for _, row in screener.iterrows():

        screener_lookup[
            str(row["Name"]).strip()
        ] = clean_theme(
            row["SectorFile"]
        )

    map_lookup = (
        mapping
        .set_index("SYMBOL")
        .to_dict("index")
    )

    records = []

    for row in progress(
        equity.itertuples(index=False),
        total=len(equity),
        desc="Classification V3"
    ):

        symbol = row.SYMBOL
        company_name = row.COMPANY_NAME

        theme = None
        sector = "UNCLASSIFIED"

        if symbol in map_lookup:

            screener_name = (
                map_lookup[symbol]
                .get("COMPANY_NAME_SCREENER")
            )

            theme = screener_lookup.get(
                screener_name
            )

            if theme:
                sector = theme_lookup.get(
                    theme.upper(),
                    "UNCLASSIFIED"
                )

        records.append({

            "SYMBOL": symbol,
            "COMPANY_NAME": company_name,
            "SECTOR": sector,
            "THEME": theme,
            "SOURCE": "SCREENER_V3",
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d")
        })

    output = pd.DataFrame(records)

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    review = output[
        output["SECTOR"] == "UNCLASSIFIED"
    ]

    review.to_csv(
        REVIEW_FILE,
        index=False
    )

    total = len(output)

    classified = len(
        output[
            output["SECTOR"] != "UNCLASSIFIED"
        ]
    )

    coverage = pd.DataFrame([{
        "TOTAL_RECORDS": total,
        "CLASSIFIED": classified,
        "UNCLASSIFIED": total - classified,
        "COVERAGE_PERCENT": round(
            (classified / total) * 100,
            2
        )
    }])

    coverage.to_csv(
        COVERAGE_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print("SCREENER CLASSIFICATION V3 COMPLETE")
    print("=" * 70)
    print(f"Records      : {total:,}")
    print(f"Classified   : {classified:,}")
    print(f"Unclassified : {total-classified:,}")
    print(
        f"Coverage     : "
        f"{coverage.iloc[0]['COVERAGE_PERCENT']}%"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
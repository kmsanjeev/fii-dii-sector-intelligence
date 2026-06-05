from pathlib import Path
from datetime import datetime

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INDEX_SOURCE = (
    PROJECT_ROOT
    / "data"
    / "intelligence"
    / "index_strength.csv"
)

REFERENCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "reference"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "NSE"
    / "indices"
    / "reports"
)

LOG_DIR = (
    PROJECT_ROOT
    / "logs"
    / "index_taxonomy"
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = (
    LOG_DIR
    / "index_taxonomy.log"
)


def log(message):

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


def classify_index(name):

    n = str(name).upper()

    # --------------------------------------------------
    # SPECIAL
    # --------------------------------------------------

    if "INDIA VIX" in n:
        return "SPECIAL"

    if "USD" in n:
        return "SPECIAL"

    # --------------------------------------------------
    # INVERSE
    # --------------------------------------------------

    if "INVERSE" in n:
        return "INVERSE"

    # --------------------------------------------------
    # LEVERAGED
    # --------------------------------------------------

    if "LEVERAGE" in n:
        return "LEVERAGED"

    # --------------------------------------------------
    # DIVIDEND
    # --------------------------------------------------

    if "DIVIDEND" in n:
        return "DIVIDEND"

    # --------------------------------------------------
    # FIXED INCOME
    # --------------------------------------------------

    if (
        "G-SEC" in n
        or "BHARAT BOND" in n
    ):
        return "FIXED_INCOME"

    # --------------------------------------------------
    # GOVERNMENT
    # --------------------------------------------------

    government_keywords = [
        "CPSE",
        "PSE"
    ]

    if any(
        k in n
        for k in government_keywords
    ):
        return "GOVERNMENT"

    # --------------------------------------------------
    # CORPORATE GROUP
    # --------------------------------------------------

    corporate_group_keywords = [
        "CORPORATE GROUP",
        "CONGLOMERATE",
        "SELECT 5 CORPORATE GROUPS",
        "TATA GROUP"
    ]

    if any(
        k in n
        for k in corporate_group_keywords
    ):
        return "CORPORATE_GROUP"

    # --------------------------------------------------
    # FACTOR
    # --------------------------------------------------

    factor_keywords = [
        "VALUE",
        "QUALITY",
        "MOMENTUM",
        "ALPHA",
        "LOW VOLATILITY",
        "HIGH BETA",
        "MULTIFACTOR",
        "MQVLV"
    ]

    if any(
        k in n
        for k in factor_keywords
    ):
        return "FACTOR"

    # --------------------------------------------------
    # STRATEGY
    # --------------------------------------------------

    strategy_keywords = [
        "EQUAL WEIGHT",
        "EQUAL-CAP",
        "MULTICAP",
        "ESG",
        "SHARIAH",
        "LIQUID",
        "TOP 10",
        "TOP 15",
        "TOP 20",
        "FPI",
        "SME",
        "MNC",
        "IPO"
    ]

    if any(
        k in n
        for k in strategy_keywords
    ):
        return "STRATEGY"

    # --------------------------------------------------
    # THEME
    # --------------------------------------------------

    theme_keywords = [
        "DEFENCE",
        "DIGITAL",
        "INTERNET",
        "TOURISM",
        "RAILWAYS",
        "RURAL",
        "GROWTH SECTORS",
        "MANUFACTURING",
        "NEW AGE",
        "MOBILITY",
        "HOUSING",
        "CONSUMPTION",
        "INFRASTRUCTURE & LOGISTICS",
        "TRANSPORTATION & LOGISTICS",
        "WAVES"
    ]

    if any(
        k in n
        for k in theme_keywords
    ):
        return "THEME"

    # --------------------------------------------------
    # SECTOR
    # --------------------------------------------------

    sector_keywords = [
        "BANK",
        "FINANCIAL",
        "IT",
        "AUTO",
        "PHARMA",
        "FMCG",
        "REALTY",
        "MEDIA",
        "METAL",
        "OIL & GAS",
        "ENERGY",
        "SERVICES",
        "CONSUMER DURABLES",
        "HEALTHCARE",
        "CHEMICALS",
        "CEMENT",
        "CAPITAL MARKETS",
        "COMMODITIES",
        "INFRASTRUCTURE",
        "NON-CYCLICAL CONSUMER"
    ]

    if any(
        k in n
        for k in sector_keywords
    ):
        return "SECTOR"

    # --------------------------------------------------
    # BROAD MARKET
    # --------------------------------------------------

    broad_keywords = [
        "NIFTY 50",
        "NIFTY 100",
        "NIFTY 200",
        "NIFTY 500",
        "NEXT 50",
        "MIDCAP",
        "SMALLCAP",
        "MICROCAP",
        "TOTAL MARKET",
        "LARGEMIDCAP"
    ]

    if any(
        k in n
        for k in broad_keywords
    ):
        return "BROAD_MARKET"

    return "REVIEW"


def main():

    print("\nINDEX TAXONOMY ENGINE\n")

    df = pd.read_csv(
        INDEX_SOURCE
    )

    result = pd.DataFrame()

    result["INDEX_NAME"] = df["INDEX_NAME"]

    result["CATEGORY"] = result[
        "INDEX_NAME"
    ].apply(
        classify_index
    )

    result.to_csv(
        REFERENCE_DIR
        / "index_master.csv",
        index=False
    )

    result.to_csv(
        REFERENCE_DIR
        / "index_category_mapping.csv",
        index=False
    )

    report = (
        result.groupby(
            "CATEGORY"
        )
        .size()
        .reset_index(
            name="COUNT"
        )
        .sort_values(
            "COUNT",
            ascending=False
        )
    )

    report.to_csv(
        REPORT_DIR
        / "index_taxonomy_report.csv",
        index=False
    )

    review = result[
        result["CATEGORY"]
        == "REVIEW"
    ]

    review.to_csv(
        REPORT_DIR
        / "index_review_queue.csv",
        index=False
    )

    log(
        f"Total={len(result)}"
    )

    log(
        f"Review={len(review)}"
    )

    print(
        f"Total Indices : {len(result)}"
    )

    print(
        f"Review Queue : {len(review)}"
    )


if __name__ == "__main__":
    main()
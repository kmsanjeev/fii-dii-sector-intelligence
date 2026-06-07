from pathlib import Path
from datetime import datetime
import sys

import pandas as pd
from rapidfuzz import process, fuzz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("company_name_mapping")

EQUITY_MASTER = ROOT / "data" / "NSE" / "equity_master" / "equity_master.csv"
SCREENER_MASTER = ROOT / "screener_csv" / "master_screener_universe.csv"

OUTPUT_DIR = ROOT / "data" / "reference" / "mapping"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "company_name_mapping.csv"
REVIEW_FILE = OUTPUT_DIR / "company_name_mapping_review.csv"
COVERAGE_FILE = OUTPUT_DIR / "company_name_mapping_coverage.csv"


def normalize(text):

    if pd.isna(text):
        return ""

    text = str(text).upper()

    remove_words = [
        "LIMITED",
        "LTD",
        "PRIVATE",
        "PVT",
        "COMPANY",
        "CORPORATION",
        "CORP",
        "INDIA",
        "INDUSTRIES",
        "INDUSTRY",
        "SERVICES",
        "SERVICE",
        "TECHNOLOGIES",
        "TECHNOLOGY",
        "ENTERPRISE",
        "ENTERPRISES",
        "HOLDINGS",
        "HOLDING",
        "PROJECTS",
        "PROJECT",
        "AND",
        "&",
        ".",
        ",",
        "-",
        "(",
        ")"
    ]

    for word in remove_words:
        text = text.replace(word, " ")

    return " ".join(text.split())

    for item in replacements:
        text = text.replace(item, " ")

    return " ".join(text.split())


def get_status(score):

    if score >= 90:
        return "EXACT"

    if score >= 70:
        return "HIGH_CONFIDENCE"

    if score >= 55:
        return "REVIEW"

    return "UNMATCHED"


def main():

    logger.info("Loading datasets...")

    nse = pd.read_csv(EQUITY_MASTER)
    screener = pd.read_csv(SCREENER_MASTER)

    nse = nse.fillna("")
    screener = screener.fillna("")

    screener_names = (
        screener["Name"]
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    normalized_lookup = {
        normalize(name): name
        for name in screener_names
    }

    normalized_choices = list(normalized_lookup.keys())

    results = []

    for row in progress(
        nse.itertuples(index=False),
        total=len(nse),
        desc="Company Mapping"
    ):

        symbol = getattr(row, "SYMBOL", "")
        company_name = getattr(row, "COMPANY_NAME", "")
        isin = getattr(row, "ISIN", "")

        normalized_name = normalize(company_name)

        if normalized_name in normalized_lookup:

            matched_name = normalized_lookup[normalized_name]
            match_score = 100

        else:

            match = process.extractOne(
                normalized_name,
                normalized_choices,
                scorer=fuzz.token_sort_ratio
            )

            if match:
                matched_name = normalized_lookup[match[0]]
                match_score = round(match[1], 2)
            else:
                matched_name = ""
                match_score = 0

        results.append({
            "ISIN": isin,
            "SYMBOL": symbol,
            "COMPANY_NAME_NSE": company_name,
            "COMPANY_NAME_SCREENER": matched_name,
            "MATCH_SCORE": match_score,
            "MATCH_STATUS": get_status(match_score),
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d")
        })

    output = pd.DataFrame(results)

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    review = output[
        output["MATCH_STATUS"].isin(
            ["REVIEW", "UNMATCHED"]
        )
    ]

    review.to_csv(
        REVIEW_FILE,
        index=False
    )

    total = len(output)

    exact = len(output[output["MATCH_STATUS"] == "EXACT"])
    high = len(output[output["MATCH_STATUS"] == "HIGH_CONFIDENCE"])
    review_count = len(output[output["MATCH_STATUS"] == "REVIEW"])
    unmatched = len(output[output["MATCH_STATUS"] == "UNMATCHED"])

    coverage = pd.DataFrame([{
        "TOTAL_RECORDS": total,
        "EXACT_MATCHES": exact,
        "HIGH_CONFIDENCE": high,
        "REVIEW_REQUIRED": review_count,
        "UNMATCHED": unmatched,
        "MATCH_PERCENT": round(
            ((exact + high) / total) * 100,
            2
        )
    }])

    coverage.to_csv(
        COVERAGE_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print("COMPANY NAME MAPPING COMPLETE")
    print("=" * 70)
    print(f"Records           : {total:,}")
    print(f"Exact Matches     : {exact:,}")
    print(f"High Confidence   : {high:,}")
    print(f"Review Required   : {review_count:,}")
    print(f"Unmatched         : {unmatched:,}")
    print(f"Match Percent     : {coverage.iloc[0]['MATCH_PERCENT']}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
from pathlib import Path
from datetime import datetime
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("company_fundamentals_master")

EQUITY_MASTER = ROOT / "data" / "NSE" / "equity_master" / "equity_master.csv"
CLASSIFICATION = ROOT / "data" / "reference" / "company_classification.csv"
MAPPING = ROOT / "data" / "reference" / "mapping" / "company_name_mapping.csv"
SCREENER = ROOT / "screener_csv" / "master_screener_universe.csv"

OUTPUT_DIR = ROOT / "data" / "reference"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_FILE = OUTPUT_DIR / "company_fundamentals_master.csv"
REVIEW_FILE = OUTPUT_DIR / "fundamentals_review_queue.csv"
COVERAGE_FILE = OUTPUT_DIR / "fundamentals_coverage_report.csv"


def safe_float(value):

    try:
        if pd.isna(value):
            return None

        value = str(value).replace(",", "").strip()

        if value == "":
            return None

        return float(value)

    except Exception:
        return None


def market_cap_bucket(mcap):

    if mcap is None:
        return "UNKNOWN"

    if mcap >= 100000:
        return "MEGA_CAP"

    if mcap >= 50000:
        return "LARGE_CAP"

    if mcap >= 10000:
        return "MID_CAP"

    if mcap >= 1000:
        return "SMALL_CAP"

    return "MICRO_CAP"


def quality_score(roce):

    if roce is None:
        return "UNKNOWN"

    if roce >= 20:
        return "HIGH"

    if roce >= 12:
        return "MEDIUM"

    return "LOW"


def growth_score(profit_growth, sales_growth):

    profit_growth = profit_growth or 0
    sales_growth = sales_growth or 0

    if profit_growth >= 15 and sales_growth >= 15:
        return "HIGH"

    if profit_growth >= 10 or sales_growth >= 10:
        return "MEDIUM"

    return "LOW"


def main():

    logger.info("Loading datasets")

    equity = pd.read_csv(EQUITY_MASTER)
    classification = pd.read_csv(CLASSIFICATION)
    mapping = pd.read_csv(MAPPING)
    screener = pd.read_csv(SCREENER)

    screener_lookup = {}

    for _, row in screener.iterrows():

        screener_lookup[str(row["Name"]).strip()] = {
            "PE_RATIO": safe_float(row.get("P/E")),
            "MARKET_CAP": safe_float(row.get("Mar CapRs.Cr.")),
            "DIVIDEND_YIELD": safe_float(row.get("Div Yld%")),
            "ROCE": safe_float(row.get("ROCE%")),
            "PROFIT_GROWTH": safe_float(row.get("Qtr Profit Var%")),
            "SALES_GROWTH": safe_float(row.get("Qtr Sales Var%"))
        }

    class_lookup = (
        classification
        .set_index("SYMBOL")
        .to_dict("index")
    )

    mapping_lookup = (
        mapping
        .set_index("SYMBOL")
        .to_dict("index")
    )

    records = []

    for row in progress(
        equity.itertuples(index=False),
        total=len(equity),
        desc="Fundamentals Master"
    ):

        symbol = getattr(row, "SYMBOL", "")
        company_name = getattr(row, "COMPANY_NAME", "")
        isin = getattr(row, "ISIN", "")
        series = getattr(row, "SERIES", "")

        sector = None
        theme = None

        if symbol in class_lookup:
            sector = class_lookup[symbol].get("SECTOR")

        screener_name = None

        if symbol in mapping_lookup:
            screener_name = mapping_lookup[symbol].get(
                "COMPANY_NAME_SCREENER"
            )

        screener_data = {}

        if screener_name in screener_lookup:
            screener_data = screener_lookup[screener_name]

        market_cap = screener_data.get("MARKET_CAP")
        pe_ratio = screener_data.get("PE_RATIO")
        roce = screener_data.get("ROCE")
        dividend_yield = screener_data.get("DIVIDEND_YIELD")
        profit_growth = screener_data.get("PROFIT_GROWTH")
        sales_growth = screener_data.get("SALES_GROWTH")

        records.append({

            "ISIN": isin,
            "SYMBOL": symbol,
            "COMPANY_NAME": company_name,
            "SERIES": series,

            "SECTOR": sector,
            "THEME": theme,

            "MARKET_CAP": market_cap,
            "MARKET_CAP_BUCKET": market_cap_bucket(market_cap),

            "PE_RATIO": pe_ratio,
            "ROCE": roce,
            "DIVIDEND_YIELD": dividend_yield,

            "SALES_GROWTH": sales_growth,
            "PROFIT_GROWTH": profit_growth,

            "QUALITY_SCORE": quality_score(roce),
            "GROWTH_SCORE": growth_score(
                profit_growth,
                sales_growth
            ),

            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d")
        })

    master = pd.DataFrame(records)

    master.to_csv(
        MASTER_FILE,
        index=False
    )

    review = master[
        master["MARKET_CAP"].isna()
    ]

    review.to_csv(
        REVIEW_FILE,
        index=False
    )

    total = len(master)

    complete = len(
        master[
            master["MARKET_CAP"].notna()
        ]
    )

    coverage = pd.DataFrame([{
        "TOTAL_RECORDS": total,
        "COMPLETE_RECORDS": complete,
        "INCOMPLETE_RECORDS": total - complete,
        "COVERAGE_PERCENT": round(
            (complete / total) * 100,
            2
        )
    }])

    coverage.to_csv(
        COVERAGE_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print("COMPANY FUNDAMENTALS MASTER COMPLETE")
    print("=" * 70)
    print(f"Records           : {total:,}")
    print(f"Complete Records  : {complete:,}")
    print(f"Coverage Percent  : {coverage.iloc[0]['COVERAGE_PERCENT']}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
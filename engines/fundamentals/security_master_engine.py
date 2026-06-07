from pathlib import Path
from datetime import datetime
import sys

import pandas as pd
from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("security_master")

NSE_MASTER = (
    ROOT
    / "data"
    / "NSE"
    / "equity_master"
    / "equity_master.csv"
)

BSE_BHAVCOPY_DIR = (
    ROOT
    / "data"
    / "BSE"
    / "bhavcopy"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "reference"
    / "security_master.csv"
)

REVIEW_FILE = (
    ROOT
    / "data"
    / "reference"
    / "security_master_review.csv"
)

COVERAGE_FILE = (
    ROOT
    / "data"
    / "reference"
    / "security_master_coverage.csv"
)


def normalize_name(text):

    if pd.isna(text):
        return ""

    text = str(text).upper()

    remove_words = [
        "LIMITED",
        "LTD",
        "LIMITED.",
        "LTD.",
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
        "HOLDING",
        "HOLDINGS",
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


def symbol_match_flag(nse_symbol, bse_symbol):

    if not nse_symbol or not bse_symbol:
        return "MISSING"

    nse_symbol = str(nse_symbol).upper().strip()
    bse_symbol = str(bse_symbol).upper().strip()

    if nse_symbol == bse_symbol:
        return "EXACT"

    if (
        nse_symbol in bse_symbol
        or
        bse_symbol in nse_symbol
    ):
        return "PARTIAL"

    return "REVIEW"


def name_match_flag(nse_name, bse_name):

    if not nse_name or not bse_name:
        return "MISSING"

    score = fuzz.token_sort_ratio(
        normalize_name(nse_name),
        normalize_name(bse_name)
    )

    if score >= 95:
        return "EXACT"

    if score >= 80:
        return "HIGH"

    if score >= 65:
        return "PARTIAL"

    return "REVIEW"


def load_latest_bse_bhavcopy():

    files = sorted(
        BSE_BHAVCOPY_DIR.glob("*.CSV")
    )

    if not files:
        raise FileNotFoundError(
            "No BSE bhavcopy found."
        )

    latest_file = files[-1]

    logger.info(
        f"Loading BSE file: {latest_file.name}"
    )

    return pd.read_csv(latest_file)


def build_bse_lookups(df):

    symbol_lookup = {}
    isin_lookup = {}

    for row in df.itertuples(index=False):

        symbol = str(
            getattr(row, "TckrSymb", "")
        ).strip()

        isin = str(
            getattr(row, "ISIN", "")
        ).strip()

        if symbol:
            symbol_lookup[symbol] = row

        if isin:
            isin_lookup[isin] = row

    return symbol_lookup, isin_lookup


def main():

    logger.info(
        "Loading NSE Equity Master"
    )

    nse = pd.read_csv(
        NSE_MASTER,
        dtype=str
    ).fillna("")

    logger.info(
        "Loading BSE Bhavcopy"
    )

    bse = load_latest_bse_bhavcopy()

    (
        bse_symbol_lookup,
        bse_isin_lookup
    ) = build_bse_lookups(bse)

    records = []
    review_records = []

    for row in progress(
        nse.itertuples(index=False),
        total=len(nse),
        desc="Security Master"
    ):

        nse_symbol = str(
            row.SYMBOL
        ).strip()

        nse_company = str(
            row.COMPANY_NAME
        ).strip()

        nse_series = str(
            row.SERIES
        ).strip()

        bse_row = bse_symbol_lookup.get(
            nse_symbol
        )

        if bse_row:

            isin = str(
                getattr(
                    bse_row,
                    "ISIN",
                    ""
                )
            ).strip()

            bse_code = str(
                getattr(
                    bse_row,
                    "FinInstrmId",
                    ""
                )
            ).strip()

            bse_symbol = str(
                getattr(
                    bse_row,
                    "TckrSymb",
                    ""
                )
            ).strip()

            bse_company = str(
                getattr(
                    bse_row,
                    "FinInstrmNm",
                    ""
                )
            ).strip()

        else:

            isin = ""
            bse_code = ""
            bse_symbol = ""
            bse_company = ""

        sym_flag = symbol_match_flag(
            nse_symbol,
            bse_symbol
        )

        name_flag = name_match_flag(
            nse_company,
            bse_company
        )

        records.append({

            "ISIN": isin,

            "COMPANY_NAME_NSE":
                nse_company,

            "COMPANY_NAME_BSE":
                bse_company,

            "NSE_SYMBOL":
                nse_symbol,

            "NSE_SERIES":
                nse_series,

            "BSE_CODE":
                bse_code,

            "BSE_SYMBOL":
                bse_symbol,

            "LISTED_NSE":
                True,

            "LISTED_BSE":
                bool(bse_symbol),

            "SYMBOL_MATCH_FLAG":
                sym_flag,

            "NAME_MATCH_FLAG":
                name_flag,

            "LAST_UPDATED":
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
        })

        if (
            sym_flag == "REVIEW"
            or
            name_flag == "REVIEW"
            or
            not bse_symbol
        ):

            review_records.append({

                "NSE_SYMBOL":
                    nse_symbol,

                "NSE_COMPANY":
                    nse_company,

                "BSE_SYMBOL":
                    bse_symbol,

                "BSE_COMPANY":
                    bse_company,

                "ISIN":
                    isin,

                "REASON":
                    (
                        f"SYMBOL={sym_flag};"
                        f"NAME={name_flag}"
                    )
            })

    output = pd.DataFrame(records)

    review = pd.DataFrame(
        review_records
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False
    )

    review.to_csv(
        REVIEW_FILE,
        index=False
    )

    total = len(output)

    matched = len(
        output[
            output["BSE_SYMBOL"] != ""
        ]
    )

    coverage = round(
        matched * 100 / total,
        2
    )

    pd.DataFrame([{

        "TOTAL_NSE":
            total,

        "MATCHED_BSE":
            matched,

        "UNMATCHED":
            total - matched,

        "COVERAGE_PERCENT":
            coverage

    }]).to_csv(
        COVERAGE_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("SECURITY MASTER COMPLETE")
    print("=" * 70)
    print(f"NSE Records      : {total:,}")
    print(f"BSE Matched      : {matched:,}")
    print(f"Coverage         : {coverage}%")
    print(f"Review Queue     : {len(review):,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
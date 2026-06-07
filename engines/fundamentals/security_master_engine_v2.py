from pathlib import Path
from datetime import datetime
import sys

import pandas as pd
from rapidfuzz import fuzz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger("security_master_v2")

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
    / "security_master_v2.csv"
)

REVIEW_FILE = (
    ROOT
    / "data"
    / "reference"
    / "security_master_v2_review.csv"
)

COVERAGE_FILE = (
    ROOT
    / "data"
    / "reference"
    / "security_master_v2_coverage.csv"
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

    return pd.read_csv(
        latest_file,
        dtype=str
    ).fillna("")


def build_symbol_lookup(df):

    lookup = {}

    for row in df.itertuples(index=False):

        symbol = str(
            getattr(row, "TckrSymb", "")
        ).strip().upper()

        if symbol:
            lookup[symbol] = row

    return lookup


def build_name_lookup(df):

    lookup = {}

    for row in df.itertuples(index=False):

        name = normalize_name(
            getattr(row, "FinInstrmNm", "")
        )

        if name:
            lookup[name] = row

    return lookup


def get_match_details(row):

    return {
        "ISIN": str(
            getattr(row, "ISIN", "")
        ).strip(),

        "BSE_CODE": str(
            getattr(row, "FinInstrmId", "")
        ).strip(),

        "BSE_SYMBOL": str(
            getattr(row, "TckrSymb", "")
        ).strip(),

        "BSE_COMPANY": str(
            getattr(row, "FinInstrmNm", "")
        ).strip()
    }


def find_fuzzy_match(
    nse_company,
    bse_df,
    threshold=95
):

    normalized_nse = normalize_name(
        nse_company
    )

    best_row = None
    best_score = 0

    first_word = ""

    if normalized_nse:
        first_word = normalized_nse.split()[0]

    candidates = []

    for row in bse_df.itertuples(index=False):

        bse_name = getattr(
            row,
            "NORMALIZED_NAME",
            ""
        )

        if (
            first_word
            and
            first_word in bse_name
        ):
            candidates.append(row)

    if not candidates:

        candidates = list(
            bse_df.itertuples(index=False)
        )

    for row in candidates:

        score = fuzz.token_sort_ratio(
            normalized_nse,
            getattr(
                row,
                "NORMALIZED_NAME",
                ""
            )
        )

        if score > best_score:
            best_score = score
            best_row = row

    if best_score >= threshold:
        return best_row, best_score

    return None, best_score


def main():

    logger.info(
        "Loading NSE Master"
    )

    nse = pd.read_csv(
        NSE_MASTER,
        dtype=str
    ).fillna("")

    logger.info(
        "Loading BSE Bhavcopy"
    )

    bse = load_latest_bse_bhavcopy()

    bse["NORMALIZED_NAME"] = (
        bse["FinInstrmNm"]
        .astype(str)
        .apply(normalize_name)
    )

    symbol_lookup = build_symbol_lookup(
        bse
    )

    name_lookup = build_name_lookup(
        bse
    )

    records = []
    review_records = []

    for row in progress(
        nse.itertuples(index=False),
        total=len(nse),
        desc="Security Master V2"
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

        normalized_nse = normalize_name(
            nse_company
        )

        bse_row = None
        match_method = "UNMATCHED"
        confidence = 0

        #
        # PASS-1
        # SYMBOL MATCH
        #

        bse_row = symbol_lookup.get(
            nse_symbol.upper()
        )

        if bse_row:
            match_method = "SYMBOL"
            confidence = 100

        #
        # PASS-2
        # NORMALIZED NAME
        #

        if not bse_row:

            bse_row = name_lookup.get(
                normalized_nse
            )

            if bse_row:
                match_method = "NAME"
                confidence = 100

        #
        # PASS-3
        # FUZZY 95
        #

        if not bse_row:

            bse_row, score = find_fuzzy_match(
                nse_company,
                bse,
                threshold=95
            )

            if bse_row:
                match_method = "FUZZY95"
                confidence = score

        #
        # PASS-4
        # FUZZY 90
        #

        if not bse_row:

            bse_row, score = find_fuzzy_match(
                nse_company,
                bse,
                threshold=90
            )

            if bse_row:
                match_method = "FUZZY90"
                confidence = score

        if bse_row:

            details = get_match_details(
                bse_row
            )

        else:

            details = {
                "ISIN": "",
                "BSE_CODE": "",
                "BSE_SYMBOL": "",
                "BSE_COMPANY": ""
            }

        records.append({

            "ISIN":
                details["ISIN"],

            "COMPANY_NAME_NSE":
                nse_company,

            "COMPANY_NAME_BSE":
                details["BSE_COMPANY"],

            "NSE_SYMBOL":
                nse_symbol,

            "NSE_SERIES":
                nse_series,

            "BSE_CODE":
                details["BSE_CODE"],

            "BSE_SYMBOL":
                details["BSE_SYMBOL"],

            "MATCH_METHOD":
                match_method,

            "MATCH_CONFIDENCE":
                confidence,

            "LISTED_NSE":
                True,

            "LISTED_BSE":
                bool(
                    details["BSE_SYMBOL"]
                ),

            "LAST_UPDATED":
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
        })

        if (
            match_method == "UNMATCHED"
            or
            match_method == "FUZZY90"
        ):

            review_records.append({

                "NSE_SYMBOL":
                    nse_symbol,

                "NSE_COMPANY":
                    nse_company,

                "BSE_SYMBOL":
                    details["BSE_SYMBOL"],

                "BSE_COMPANY":
                    details["BSE_COMPANY"],

                "ISIN":
                    details["ISIN"],

                "MATCH_METHOD":
                    match_method,

                "MATCH_CONFIDENCE":
                    confidence
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
    print("SECURITY MASTER V2 COMPLETE")
    print("=" * 70)
    print(f"NSE Records      : {total:,}")
    print(f"BSE Matched      : {matched:,}")
    print(f"Coverage         : {coverage}%")
    print(f"Review Queue     : {len(review):,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
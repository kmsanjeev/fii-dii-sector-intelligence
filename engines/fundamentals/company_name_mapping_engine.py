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

SECURITY_MASTER = (
    ROOT
    / "data"
    / "reference"
    / "security_master.csv"
)

SCREENER_MASTER = (
    ROOT
    / "screener_csv"
    / "master_screener_universe.csv"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "reference"
    / "mapping"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "company_name_mapping.csv"
)

REVIEW_FILE = (
    OUTPUT_DIR
    / "company_name_mapping_review.csv"
)

COVERAGE_FILE = (
    OUTPUT_DIR
    / "company_name_mapping_coverage.csv"
)


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
        "HOLDING",
        "HOLDINGS",
        "PROJECT",
        "PROJECTS",
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


def generate_symbols(company):

    words = normalize(company).split()

    candidates = set()

    if not words:
        return candidates

    acronym = "".join(
        word[0]
        for word in words
        if word
    )

    if 1 <= len(acronym) <= 10:
        candidates.add(acronym)

    if len(words) == 1:

        sym = words[0][:10]

        if sym:
            candidates.add(sym)

    elif len(words) == 2:

        sym = (
            words[0][:5]
            + words[1][:5]
        )[:10]

        candidates.add(sym)

        sym = (
            words[0][:4]
            + words[1][:4]
        )[:10]

        candidates.add(sym)

    else:

        sym = (
            words[0][:4]
            + words[1][:3]
            + words[2][:3]
        )[:10]

        candidates.add(sym)

        sym = (
            words[0][:5]
            + words[1][:5]
        )[:10]

        candidates.add(sym)

    return {
        x.upper()
        for x in candidates
        if x and len(x) <= 10
    }


def get_status(score):

    if score >= 90:
        return "EXACT"

    if score >= 70:
        return "HIGH_CONFIDENCE"

    if score >= 55:
        return "REVIEW"

    return "UNMATCHED"


def main():

    logger.info(
        "Loading datasets"
    )

    security = pd.read_csv(
        SECURITY_MASTER,
        dtype=str
    ).fillna("")

    screener = pd.read_csv(
        SCREENER_MASTER,
        dtype=str
    ).fillna("")

    screener_names = (
        screener["Name"]
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    normalized_lookup = {
        normalize(x): x
        for x in screener_names
    }

    normalized_choices = (
        list(
            normalized_lookup.keys()
        )
    )

    screener_symbol_map = {}

    for name in screener_names:

        for sym in generate_symbols(name):

            screener_symbol_map.setdefault(
                sym,
                name
            )

    results = []

    for row in progress(
        security.itertuples(index=False),
        total=len(security),
        desc="Company Mapping"
    ):

        nse_symbol = str(
            getattr(
                row,
                "NSE_SYMBOL",
                ""
            )
        ).strip().upper()

        bse_symbol = str(
            getattr(
                row,
                "BSE_SYMBOL",
                ""
            )
        ).strip().upper()

        company_name = str(
            getattr(
                row,
                "COMPANY_NAME",
                ""
            )
        ).strip()

        isin = str(
            getattr(
                row,
                "ISIN",
                ""
            )
        ).strip()

        matched_name = ""
        match_score = 0

        if (
            nse_symbol
            and
            nse_symbol in screener_symbol_map
        ):

            matched_name = (
                screener_symbol_map[
                    nse_symbol
                ]
            )

            match_score = 100

        elif (
            bse_symbol
            and
            bse_symbol in screener_symbol_map
        ):

            matched_name = (
                screener_symbol_map[
                    bse_symbol
                ]
            )

            match_score = 100

        else:

            normalized_name = normalize(
                company_name
            )

            if (
                normalized_name
                in
                normalized_lookup
            ):

                matched_name = (
                    normalized_lookup[
                        normalized_name
                    ]
                )

                match_score = 100

            else:

                match = process.extractOne(
                    normalized_name,
                    normalized_choices,
                    scorer=fuzz.token_sort_ratio
                )

                if match:

                    matched_name = (
                        normalized_lookup[
                            match[0]
                        ]
                    )

                    match_score = round(
                        match[1],
                        2
                    )

        results.append({

            "ISIN":
                isin,

            "SYMBOL":
                (
                    nse_symbol
                    or
                    bse_symbol
                ),

            "COMPANY_NAME_NSE":
                company_name,

            "COMPANY_NAME_SCREENER":
                matched_name,

            "MATCH_SCORE":
                match_score,

            "MATCH_STATUS":
                get_status(
                    match_score
                ),

            "LAST_UPDATED":
                datetime.now().strftime(
                    "%Y-%m-%d"
                )
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

    exact = len(
        output[
            output["MATCH_STATUS"] == "EXACT"
        ]
    )

    high = len(
        output[
            output["MATCH_STATUS"]
            ==
            "HIGH_CONFIDENCE"
        ]
    )

    review_count = len(
        output[
            output["MATCH_STATUS"]
            ==
            "REVIEW"
        ]
    )

    unmatched = len(
        output[
            output["MATCH_STATUS"]
            ==
            "UNMATCHED"
        ]
    )

    match_percent = round(
        (
            (exact + high)
            / total
        ) * 100,
        2
    )

    pd.DataFrame([{

        "TOTAL_RECORDS":
            total,

        "EXACT_MATCHES":
            exact,

        "HIGH_CONFIDENCE":
            high,

        "REVIEW_REQUIRED":
            review_count,

        "UNMATCHED":
            unmatched,

        "MATCH_PERCENT":
            match_percent

    }]).to_csv(
        COVERAGE_FILE,
        index=False
    )

    print()
    print("=" * 70)
    print("COMPANY NAME MAPPING COMPLETE")
    print("=" * 70)
    print(f"Records         : {total:,}")
    print(f"Exact Matches   : {exact:,}")
    print(f"High Confidence : {high:,}")
    print(f"Review Required : {review_count:,}")
    print(f"Unmatched       : {unmatched:,}")
    print(f"Match Percent   : {match_percent}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
import pandas as pd
from datetime import datetime
from pathlib import Path

from utils.logger import logger


BASE_PATH = Path(
    "data/historical/fii_dii"
)

BASE_PATH.mkdir(
    parents=True,
    exist_ok=True
)


def get_existing_dates():

    file_path = (
        BASE_PATH /
        "fii_dii_history.csv"
    )

    if not file_path.exists():

        return set()

    df = pd.read_csv(
        file_path
    )

    return set(
        df["Date"].astype(str)
    )


def generate_required_dates():

    end_date = datetime.now()

    start_date = datetime(
        end_date.year - 10,
        end_date.month,
        end_date.day
    )

    dates = pd.bdate_range(
        start=start_date,
        end=end_date
    )

    return set(
        dates.strftime(
            "%Y-%m-%d"
        )
    )


def get_missing_dates():

    existing = (
        get_existing_dates()
    )

    required = (
        generate_required_dates()
    )

    missing = sorted(
        list(
            required - existing
        )
    )

    logger.info(
        f"Missing dates:{len(missing)}"
    )

    return missing
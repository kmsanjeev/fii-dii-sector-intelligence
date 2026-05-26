import pandas as pd
from pathlib import Path
from datetime import datetime

from utils.logger import logger


DATA_DIR = Path(
    "data/historical/fii_dii"
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

CSV_FILE = (
    DATA_DIR /
    "fii_dii_history.csv"
)

BATCH_SIZE = 500


def create_file_if_missing():

    if not CSV_FILE.exists():

        df = pd.DataFrame(
            columns=[
                "Date",
                "FII_Buy",
                "FII_Sell",
                "FII_Net",
                "DII_Buy",
                "DII_Sell",
                "DII_Net",
                "Source"
            ]
        )

        df.to_csv(
            CSV_FILE,
            index=False
        )

        logger.info(
            "Created empty CSV"
        )


def load_history():

    create_file_if_missing()

    return pd.read_csv(
        CSV_FILE
    )


def get_missing_dates():

    history = load_history()

    existing_dates = set(
        history["Date"]
        .astype(str)
    )

    end_date = datetime.now()

    start_date = datetime(
        end_date.year - 10,
        end_date.month,
        end_date.day
    )

    required_dates = pd.bdate_range(
        start=start_date,
        end=end_date
    )

    required_dates = set(
        required_dates.strftime(
            "%Y-%m-%d"
        )
    )

    missing = sorted(
        list(
            required_dates -
            existing_dates
        )
    )

    logger.info(
        f"Missing dates:{len(missing)}"
    )

    return missing[
        :BATCH_SIZE
    ]


def save_data(df):

    history = load_history()

    history = pd.concat(
        [
            history,
            df
        ],
        ignore_index=True
    )

    history = (
        history
        .drop_duplicates(
            subset=["Date"]
        )
        .sort_values(
            by="Date"
        )
    )

    history.to_csv(
        CSV_FILE,
        index=False
    )

    logger.info(
        f"Total rows:{len(history)}"
    )
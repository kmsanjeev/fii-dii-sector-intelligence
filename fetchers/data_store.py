import pandas as pd
from pathlib import Path

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


def save_fii_dii(df):

    if CSV_FILE.exists():

        history = pd.read_csv(
            CSV_FILE
        )

    else:

        history = pd.DataFrame()

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
        f"CSV updated: {len(history)} rows"
    )
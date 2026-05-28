import os
import pandas as pd

from utils.logger import logger


SAVE_DIR = (
    "data/historical/fii_dii/"
)

SAVE_FILE = (
    SAVE_DIR
    +
    "historical_fii_dii.csv"
)


def ensure_directory():

    os.makedirs(

        SAVE_DIR,

        exist_ok=True

    )


def initialize_file():

    ensure_directory()

    if not os.path.exists(
        SAVE_FILE
    ):

        columns = [

            "Date",

            "FII_Buy",
            "FII_Sell",
            "FII_Net",

            "DII_Buy",
            "DII_Sell",
            "DII_Net"

        ]

        pd.DataFrame(
            columns=columns
        ).to_csv(

            SAVE_FILE,

            index=False

        )

        logger.info(
            "Historical FII/DII file created"
        )


def append_historical_data(df):

    try:

        initialize_file()

        if df.empty:

            logger.warning(
                "No FII/DII data to archive"
            )

            return

        existing = pd.read_csv(
            SAVE_FILE
        )

        combined = pd.concat(

            [
                existing,
                df
            ],

            ignore_index=True

        )

        combined = combined.drop_duplicates(

            subset=["Date"],

            keep="last"

        )

        combined = combined.sort_values(
            by="Date"
        )

        combined.to_csv(

            SAVE_FILE,

            index=False

        )

        logger.info(

            f"Historical FII/DII updated: "
            f"{len(combined)} rows"

        )

    except Exception as e:

        logger.error(
            f"Historical archive error: {e}"
        )
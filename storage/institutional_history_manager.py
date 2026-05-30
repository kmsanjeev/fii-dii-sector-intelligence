import os
import pandas as pd

from utils.logger import logger


SAVE_DIR = (
    "data/historical/institutional/"
)

SAVE_FILE = (
    SAVE_DIR
    +
    "institutional_positioning_history.csv"
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

            "FII_OI_Net",
            "DII_OI_Net",
            "PRO_OI_Net",
            "CLIENT_OI_Net",

            "FII_Volume_Net",
            "DII_Volume_Net",
            "PRO_Volume_Net",
            "CLIENT_Volume_Net",

            "FII_Derivatives_Net",

            "FII_OI_Score",
            "DII_OI_Score",
            "PRO_OI_Score",
            "CLIENT_OI_Score",

            "FII_Volume_Score",
            "DII_Volume_Score",
            "PRO_Volume_Score",
            "CLIENT_Volume_Score",

            "FII_Derivatives_Score",

            "Institutional_Score",
            "Regime"

        ]

        pd.DataFrame(
            columns=columns
        ).to_csv(

            SAVE_FILE,

            index=False

        )

        logger.info(
            "Institutional history file created"
        )


def load_history():

    initialize_file()

    return pd.read_csv(
        SAVE_FILE
    )


def get_existing_dates():

    history = load_history()

    if history.empty:

        return set()

    return set(

        history["Date"]
        .astype(str)

    )


def append_historical_data(df):

    try:

        initialize_file()

        if df.empty:

            logger.warning(
                "No institutional data to archive"
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

            f"Institutional history updated: "
            f"{len(combined)} rows"

        )

    except Exception as e:

        logger.error(

            f"Institutional history error: "
            f"{e}"

        )
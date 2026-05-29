import os
import pandas as pd
import yfinance as yf

from utils.logger import logger


SAVE_PATH = (
    "data/historical/thematic/"
)

SAVE_FILE = (
    SAVE_PATH
    +
    "thematic_history.csv"
)


THEMATIC_MAP = {

    "NIFTY INFRA":
    "^CNXINFRA",

    "NIFTY ENERGY":
    "^CNXENERGY",

    "NIFTY PSE":
    "^CNXPSE",

    "NIFTY MNC":
    "^CNXMNC"

}


def fetch_thematic_history():

    try:

        if os.path.exists(
            SAVE_FILE
        ):

            logger.info(
                "Using cached thematic history"
            )

            return pd.read_csv(
                SAVE_FILE
            )

        os.makedirs(
            SAVE_PATH,
            exist_ok=True
        )

        combined = []

        for theme, ticker in THEMATIC_MAP.items():

            logger.info(
                f"Downloading Theme: {theme}"
            )

            df = yf.download(

                ticker,

                period="10y",

                progress=False,

                auto_adjust=True

            )

            if df.empty:

                continue

            df = df.reset_index()

            if isinstance(
                df.columns,
                pd.MultiIndex
            ):

                df.columns = [

                    col[0]

                    for col in df.columns

                ]

            df["Theme"] = theme

            combined.append(

                df[[

                    "Date",
                    "Theme",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"

                ]]

            )

        final_df = pd.concat(

            combined,

            ignore_index=True

        )

        final_df.to_csv(

            SAVE_FILE,

            index=False

        )

        logger.info(

            f"Thematic history saved: "
            f"{len(final_df)} rows"

        )

        return final_df

    except Exception as e:

        logger.error(
            f"Thematic history error: {e}"
        )

        return pd.DataFrame()
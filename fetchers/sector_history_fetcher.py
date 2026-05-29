import os
import pandas as pd
import yfinance as yf

from utils.logger import logger


SAVE_PATH = (
    "data/historical/sectors/"
)

SAVE_FILE = (
    SAVE_PATH
    +
    "sector_history.csv"
)


SECTOR_MAP = {

    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY IT": "^CNXIT",
    "NIFTY MEDIA": "^CNXMEDIA",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY PSU BANK": "^CNXPSUBANK",
    "NIFTY REALTY": "^CNXREALTY"

}


def fetch_sector_history():

    try:

        if os.path.exists(
            SAVE_FILE
        ):

            logger.info(
                "Using cached sector history"
            )

            return pd.read_csv(
                SAVE_FILE
            )

        os.makedirs(
            SAVE_PATH,
            exist_ok=True
        )

        combined = []

        for sector, ticker in SECTOR_MAP.items():

            logger.info(
                f"Downloading: {sector}"
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

            df["Sector"] = sector

            combined.append(

                df[[

                    "Date",
                    "Sector",
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

            f"Sector history saved: "
            f"{len(final_df)} rows"

        )

        return final_df

    except Exception as e:

        logger.error(
            f"Sector history error: {e}"
        )

        return pd.DataFrame()
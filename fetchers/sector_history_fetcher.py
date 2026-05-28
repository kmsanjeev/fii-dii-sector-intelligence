import os
import yfinance as yf
import pandas as pd

from utils.logger import logger


SECTOR_MAP = {

    "NIFTY AUTO":
    "^CNXAUTO",

    "NIFTY BANK":
    "^NSEBANK",

    "NIFTY FMCG":
    "^CNXFMCG",

    "NIFTY IT":
    "^CNXIT",

    "NIFTY MEDIA":
    "^CNXMEDIA",

    "NIFTY METAL":
    "^CNXMETAL",

    "NIFTY PHARMA":
    "^CNXPHARMA",

    "NIFTY PSU BANK":
    "^CNXPSUBANK",

    "NIFTY REALTY":
    "^CNXREALTY",

    "NIFTY HEALTHCARE":
    "^CNXHEALTHCARE"

}


SAVE_PATH = (
    "data/historical/sectors/"
)


def ensure_directory():

    os.makedirs(

        SAVE_PATH,

        exist_ok=True

    )


def fetch_sector_history():

    try:

        ensure_directory()

        combined = []

        for sector, ticker in SECTOR_MAP.items():

            logger.info(
                f"Downloading: {sector}"
            )

            df = yf.download(

                ticker,

                period="10y",

                interval="1d",

                auto_adjust=True,

                progress=False

            )

            if df.empty:

                logger.warning(
                    f"No data: {sector}"
                )

                continue

            df = df.reset_index()

            df["Sector"] = sector

            df["Daily_Change"] = (

                (
                    df["Close"]
                    -
                    df["Open"]
                )

                /

                df["Open"]

                * 100

            ).round(2)

            combined.append(df)

        if not combined:

            logger.error(
                "No sector data downloaded"
            )

            return pd.DataFrame()

        final_df = pd.concat(

            combined,

            ignore_index=True

        )

        final_df = final_df[[

            "Date",
            "Sector",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
            "Daily_Change"

        ]]

        save_file = (

            SAVE_PATH
            +
            "sector_history.csv"
        )

        final_df.to_csv(

            save_file,

            index=False

        )

        logger.info(
            f"Sector history saved: {len(final_df)} rows"
        )

        return final_df

    except Exception as e:

        logger.error(
            f"Sector history error: {e}"
        )

        return pd.DataFrame()
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
    "^CNXREALTY"

}


SAVE_PATH = (
    "data/historical/sectors/"
)


def ensure_directory():

    os.makedirs(

        SAVE_PATH,

        exist_ok=True

    )


def normalize_columns(df):

    # Flatten MultiIndex if present

    if isinstance(
        df.columns,
        pd.MultiIndex
    ):

        df.columns = [

            col[0]

            for col in df.columns

        ]

    return df


def fetch_sector_history():

    try:

        ensure_directory()

        combined = []

        for sector, ticker in SECTOR_MAP.items():

            try:

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

                df = normalize_columns(df)

                df = df.reset_index()

                # Safety rename

                if "index" in df.columns:

                    df.rename(

                        columns={
                            "index":
                            "Date"
                        },

                        inplace=True

                    )

                if "Date" not in df.columns:

                    logger.warning(
                        f"Date column missing: {sector}"
                    )

                    continue

                required = [

                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"

                ]

                missing = [

                    x for x in required

                    if x not in df.columns

                ]

                if missing:

                    logger.warning(
                        f"Missing columns {missing}: {sector}"
                    )

                    continue

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

                combined.append(

                    df[[

                        "Date",
                        "Sector",
                        "Open",
                        "High",
                        "Low",
                        "Close",
                        "Volume",
                        "Daily_Change"

                    ]]

                )

            except Exception as sector_error:

                logger.error(
                    f"{sector} error: {sector_error}"
                )

        if not combined:

            logger.error(
                "No sector data downloaded"
            )

            return pd.DataFrame()

        final_df = pd.concat(

            combined,

            ignore_index=True

        )

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
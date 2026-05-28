import os
import yfinance as yf
import pandas as pd

from utils.logger import logger


THEMATIC_MAP = {

    "NIFTY CPSE":
    "^CNXCPSE",

    "NIFTY INFRA":
    "^CNXINFRA",

    "NIFTY ENERGY":
    "^CNXENERGY",

    "NIFTY PSE":
    "^CNXPSE",

    "NIFTY CONSUMPTION":
    "^CNXCONSUMPTION",

    "NIFTY MNC":
    "^CNXMNC",

    "NIFTY COMMODITIES":
    "^CNXCOMMODITIES"

}


SAVE_PATH = (
    "data/historical/thematic/"
)


def ensure_directory():

    os.makedirs(

        SAVE_PATH,

        exist_ok=True

    )


def normalize_columns(df):

    if isinstance(
        df.columns,
        pd.MultiIndex
    ):

        df.columns = [

            col[0]

            for col in df.columns

        ]

    return df


def fetch_thematic_history():

    try:

        ensure_directory()

        combined = []

        for theme, ticker in THEMATIC_MAP.items():

            try:

                logger.info(
                    f"Downloading Theme: {theme}"
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
                        f"No theme data: {theme}"
                    )

                    continue

                df = normalize_columns(df)

                df = df.reset_index()

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
                        f"Date missing: {theme}"
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
                        f"Missing columns {missing}: {theme}"
                    )

                    continue

                df["Theme"] = theme

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
                        "Theme",
                        "Open",
                        "High",
                        "Low",
                        "Close",
                        "Volume",
                        "Daily_Change"

                    ]]

                )

            except Exception as theme_error:

                logger.error(
                    f"{theme} error: {theme_error}"
                )

        if not combined:

            logger.error(
                "No thematic data downloaded"
            )

            return pd.DataFrame()

        final_df = pd.concat(

            combined,

            ignore_index=True

        )

        save_file = (

            SAVE_PATH
            +
            "thematic_history.csv"
        )

        final_df.to_csv(

            save_file,

            index=False

        )

        logger.info(
            f"Thematic history saved: {len(final_df)} rows"
        )

        return final_df

    except Exception as e:

        logger.error(
            f"Thematic history error: {e}"
        )

        return pd.DataFrame()
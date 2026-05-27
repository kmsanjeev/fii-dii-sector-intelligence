import yfinance as yf
import pandas as pd

from utils.logger import logger


SECTOR_MAP = {

    "NIFTY IT":[
        "TCS.NS",
        "INFY.NS",
        "HCLTECH.NS",
        "WIPRO.NS",
        "TECHM.NS"
    ],

    "NIFTY BANK":[
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "AXISBANK.NS",
        "KOTAKBANK.NS"
    ],

    "NIFTY AUTO":[
        "MARUTI.NS",
        "M&M.NS",
        "TATAMOTORS.NS",
        "BAJAJ-AUTO.NS",
        "EICHERMOT.NS"
    ],

    "NIFTY PHARMA":[
        "SUNPHARMA.NS",
        "DRREDDY.NS",
        "CIPLA.NS",
        "DIVISLAB.NS",
        "LUPIN.NS"
    ],

    "NIFTY METAL":[
        "TATASTEEL.NS",
        "JSWSTEEL.NS",
        "HINDALCO.NS",
        "JINDALSTEL.NS",
        "SAIL.NS"
    ],

    "NIFTY MEDIA":[
        "ZEEL.NS",
        "SUNTV.NS",
        "PVRINOX.NS",
        "SAREGAMA.NS",
        "NETWORK18.NS"
    ]

}


def fetch_sector_leaders(
    sector_name
):

    try:

        if sector_name not in SECTOR_MAP:

            logger.warning(
                f"{sector_name} not mapped"
            )

            return pd.DataFrame()

        stocks = SECTOR_MAP[
            sector_name
        ]

        logger.info(
            f"Fetching leaders for {sector_name}"
        )

        data = yf.download(

            tickers=stocks,

            period="2d",

            interval="1d",

            auto_adjust=True,

            progress=False

        )

        close_df = data["Close"]

        pct_change = (

            (

                close_df.iloc[-1]
                -
                close_df.iloc[-2]

            )

            /

            close_df.iloc[-2]

            *100

        )

        df = pd.DataFrame({

            "symbol":
            pct_change.index,

            "change":
            pct_change.values

        })

        df = (

            df
            .dropna()

            .sort_values(
                by="change",
                ascending=False
            )

            .head(3)

        )

        logger.info(
            f"Sector leaders fetched: {len(df)}"
        )

        return df


    except Exception as e:

        logger.error(
            f"Sector leaders error: {e}"
        )

        return pd.DataFrame()
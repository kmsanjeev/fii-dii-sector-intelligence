import os
import yfinance as yf
import pandas as pd

from utils.logger import logger


CACHE_DIR="/tmp/yfinance_cache"

os.makedirs(
    CACHE_DIR,
    exist_ok=True
)

try:

    yf.set_tz_cache_location(
        CACHE_DIR
    )

except:

    pass


NIFTY50=[

    "RELIANCE.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "INFY.NS",
    "TCS.NS",
    "SBIN.NS",
    "BHARTIARTL.NS",
    "LT.NS",
    "ITC.NS",
    "HINDUNILVR.NS",
    "KOTAKBANK.NS",
    "AXISBANK.NS",
    "BAJFINANCE.NS",
    "MARUTI.NS",
    "SUNPHARMA.NS",
    "TITAN.NS",
    "ULTRACEMCO.NS",
    "NTPC.NS",
    "POWERGRID.NS",
    "M&M.NS"

]


def fetch_top_movers():

    try:

        logger.info(
            "Trying NSE movers..."
        )

        raise Exception(
            "Fallback enabled"
        )

    except Exception as e:

        logger.warning(
            f"NSE failed: {e}"
        )

    try:

        logger.info(
            "Trying yFinance fallback..."
        )

        data=yf.download(

            tickers=NIFTY50,

            period="5d",

            interval="1d",

            auto_adjust=True,

            progress=False

        )

        close_df=data["Close"]

        if len(close_df)<2:

            logger.warning(
                "Insufficient price history"
            )

            return (

                pd.DataFrame(),
                pd.DataFrame()

            )

        latest=close_df.iloc[-1]
        previous=close_df.iloc[-2]

        pct_change=(

            (
                latest
                -
                previous
            )

            /

            previous

            *100

        )

        df=pd.DataFrame({

            "symbol":
            pct_change.index,

            "percentChange":
            pct_change.values

        })

        df=(

            df
            .dropna()

        )

        gainers=(

            df

            .sort_values(
                by="percentChange",
                ascending=False
            )

            [["symbol","percentChange"]]

            .head(3)

        )

        losers=(

            df

            .sort_values(
                by="percentChange",
                ascending=True
            )

            [["symbol","percentChange"]]

            .head(3)

        )

        logger.info(
            "Movers fetched"
        )

        return (

            gainers,
            losers

        )

    except Exception as e:

        logger.error(
            f"Movers error: {e}"
        )

        return (

            pd.DataFrame(),
            pd.DataFrame()

        )
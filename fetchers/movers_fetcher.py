import os
import requests
import yfinance as yf
import pandas as pd

from utils.logger import logger


# Prevent yfinance cache warnings
CACHE_DIR = "/tmp/yfinance_cache"

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


HEADERS = {
    "User-Agent":"Mozilla/5.0"
}


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

        # Placeholder until NSE parsing is rebuilt

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

            period="2d",

            interval="1d",

            auto_adjust=True,

            progress=False

        )

        close_df=data["Close"]

        pct_change=(

            (

                close_df.iloc[-1]

                -

                close_df.iloc[-2]

            )

            /

            close_df.iloc[-2]

            *100

        )

        df=pd.DataFrame({

            "symbol":
            pct_change.index,

            "percentChange":
            pct_change.values

        })

        df=df.dropna()

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
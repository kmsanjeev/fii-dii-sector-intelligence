import os
import requests
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


HEADERS={

    "User-Agent":
    "Mozilla/5.0",

    "Accept":
    "application/json",

    "Referer":
    "https://www.nseindia.com/",

    "Connection":
    "keep-alive"

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


def fetch_from_nse():

    try:

        logger.info(
            "Trying NSE movers..."
        )

        session=requests.Session()

        session.headers.update(
            HEADERS
        )

        # Initialize cookies

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        response=session.get(

            "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050",

            timeout=30

        )

        response.raise_for_status()

        data=response.json()

        if "data" not in data:

            raise Exception(
                "No NSE data found"
            )

        df=pd.DataFrame(
            data["data"]
        )

        if df.empty:

            raise Exception(
                "Empty NSE dataframe"
            )

        required_cols=[
            "symbol",
            "pChange"
        ]

        for col in required_cols:

            if col not in df.columns:

                raise Exception(
                    f"Missing column: {col}"
                )

        df["pChange"]=pd.to_numeric(

            df["pChange"],
            errors="coerce"

        )

        df=df.dropna(
            subset=["pChange"]
        )

        gainers=(

            df

            .sort_values(
                by="pChange",
                ascending=False
            )

            [["symbol","pChange"]]

            .head(3)

            .rename(
                columns={
                    "pChange":
                    "percentChange"
                }
            )

        )

        losers=(

            df

            .sort_values(
                by="pChange",
                ascending=True
            )

            [["symbol","pChange"]]

            .head(3)

            .rename(
                columns={
                    "pChange":
                    "percentChange"
                }
            )

        )

        logger.info(
            "NSE movers fetched"
        )

        return (
            gainers,
            losers
        )

    except Exception as e:

        logger.warning(
            f"NSE failed: {e}"
        )

        return None, None


def fetch_from_yfinance():

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

            raise Exception(
                "Insufficient yFinance history"
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
            "yFinance movers fetched"
        )

        return (
            gainers,
            losers
        )

    except Exception as e:

        logger.error(
            f"yFinance failed: {e}"
        )

        return (

            pd.DataFrame(),
            pd.DataFrame()

        )


def fetch_top_movers():

    gainers, losers = (
        fetch_from_nse()
    )

    if gainers is not None:

        return (
            gainers,
            losers
        )

    logger.info(
        "Switching to fallback source"
    )

    return fetch_from_yfinance()
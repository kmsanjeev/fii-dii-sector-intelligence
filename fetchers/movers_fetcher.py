import requests
import yfinance as yf
import pandas as pd

from utils.logger import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


NIFTY50 = [

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

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        response = session.get(
            "https://www.nseindia.com/api/live-analysis-variations?index=gainers",
            timeout=30
        )

        response.raise_for_status()

        gainers_data = response.json()

        response = session.get(
            "https://www.nseindia.com/api/live-analysis-variations?index=losers",
            timeout=30
        )

        response.raise_for_status()

        losers_data = response.json()

        gainers = pd.DataFrame(
            gainers_data
        )

        losers = pd.DataFrame(
            losers_data
        )

        if gainers.empty or losers.empty:

            raise Exception(
                "Empty NSE response"
            )

        gainers["percentChange"] = pd.to_numeric(
            gainers["percentChange"],
            errors="coerce"
        )

        losers["percentChange"] = pd.to_numeric(
            losers["percentChange"],
            errors="coerce"
        )

        gainers = (

            gainers

            [["symbol","percentChange"]]

            .dropna()

            .head(3)

        )

        losers = (

            losers

            [["symbol","percentChange"]]

            .dropna()

            .head(3)

        )

        logger.info(
            "NSE movers fetched"
        )

        return gainers, losers

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

        data = yf.download(

            tickers=NIFTY50,

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

            * 100

        )

        df = pd.DataFrame({

            "symbol":
            pct_change.index,

            "percentChange":
            pct_change.values

        })

        df = (

            df
            .dropna()

        )

        gainers = (

            df

            .sort_values(
                by="percentChange",
                ascending=False
            )

            [["symbol","percentChange"]]

            .head(3)

        )

        losers = (

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

        return gainers, losers

    except Exception as e:

        logger.error(
            f"yFinance failed: {e}"
        )

        return (

            pd.DataFrame(),
            pd.DataFrame()

        )


def fetch_top_movers():

    gainers, losers = fetch_from_nse()

    if gainers is not None:

        return gainers, losers

    logger.info(
        "Switching to fallback source"
    )

    return fetch_from_yfinance()
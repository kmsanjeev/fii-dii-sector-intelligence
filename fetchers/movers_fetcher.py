import requests
import pandas as pd

from utils.logger import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_top_movers():

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        # Warm-up request for NSE cookies

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        response = session.get(
            "https://www.nseindia.com/api/live-analysis-variations?index=nifty50",
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        logger.info(
            f"Movers response type: {type(data)}"
        )

        # Response returns list directly

        if isinstance(
            data,
            list
        ):

            df = pd.DataFrame(
                data
            )

        elif isinstance(
            data,
            dict
        ):

            df = pd.DataFrame(
                data.get(
                    "data",
                    []
                )
            )

        else:

            logger.warning(
                "Unknown movers structure"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        if df.empty:

            logger.warning(
                "Movers dataframe empty"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        logger.info(
            f"Movers columns: {list(df.columns)}"
        )

        df["percentChange"] = pd.to_numeric(
            df["percentChange"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["percentChange"]
        )

        gainers = (

            df.sort_values(
                by="percentChange",
                ascending=False
            )

            [["symbol", "percentChange"]]

            .head(3)

        )

        losers = (

            df.sort_values(
                by="percentChange",
                ascending=True
            )

            [["symbol", "percentChange"]]

            .head(3)

        )

        logger.info(
            f"Movers fetched: {len(df)}"
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
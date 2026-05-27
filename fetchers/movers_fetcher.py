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

        # NSE warm-up
        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        response = session.get(
            "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050",
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        logger.info(
            f"Response keys: {list(data.keys())}"
        )

        df = pd.DataFrame(
            data.get(
                "data",
                []
            )
        )

        logger.info(
            f"Columns: {list(df.columns)}"
        )

        logger.info(
            f"\n{df.head(5)}"
        )

        if df.empty:

            logger.warning(
                "Movers dataframe empty"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        if "pChange" not in df.columns:

            logger.warning(
                "pChange missing"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        df["pChange"] = pd.to_numeric(
            df["pChange"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["pChange"]
        )

        gainers = (

            df.sort_values(
                by="pChange",
                ascending=False
            )

            [["symbol","pChange"]]

            .head(3)

        )

        losers = (

            df.sort_values(
                by="pChange",
                ascending=True
            )

            [["symbol","pChange"]]

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
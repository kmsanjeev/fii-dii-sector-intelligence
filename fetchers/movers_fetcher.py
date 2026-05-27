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

        # NSE cookie initialization
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
            f"Response keys: {list(data.keys())}"
        )

        # Extract nested structure safely

        raw_data = None

        for key, value in data.items():

            logger.info(
                f"{key}: {type(value)}"
            )

            if isinstance(
                value,
                list
            ):

                raw_data = value
                break

        if raw_data is None:

            logger.warning(
                "No list found in response"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        df = pd.DataFrame(
            raw_data
        )

        logger.info(
            f"Columns: {list(df.columns)}"
        )

        if df.empty:

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        if "percentChange" not in df.columns:

            logger.warning(
                "percentChange missing"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
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
            "Movers fetched successfully"
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
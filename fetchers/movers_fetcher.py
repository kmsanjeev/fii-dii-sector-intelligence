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

        # Initialize NSE session/cookies
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

        if "data" not in data:

            logger.warning(
                "No data key present"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        records = data["data"]

        if not isinstance(
            records,
            list
        ):

            logger.warning(
                f"Unexpected records type: {type(records)}"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        df = pd.DataFrame(
            records
        )

        logger.info(
            f"Movers columns: {list(df.columns)}"
        )

        required_columns = [
            "symbol",
            "pChange"
        ]

        for col in required_columns:

            if col not in df.columns:

                logger.warning(
                    f"Missing column: {col}"
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

            df
            .sort_values(
                by="pChange",
                ascending=False
            )

            [["symbol", "pChange"]]

            .head(3)

        )

        losers = (

            df
            .sort_values(
                by="pChange",
                ascending=True
            )

            [["symbol", "pChange"]]

            .head(3)

        )

        logger.info(
            f"Movers fetched: {len(df)} stocks"
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
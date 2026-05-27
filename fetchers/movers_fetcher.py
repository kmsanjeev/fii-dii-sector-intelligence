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

        # Warm-up request
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

        df = pd.DataFrame(
            data["data"]
        )

        if df.empty:

            logger.warning(
                "No movers data returned"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
            )

        # Convert to numeric
        df["pChange"] = (
            pd.to_numeric(
                df["pChange"],
                errors="coerce"
            )
        )

        df = (
            df.dropna(
                subset=["pChange"]
            )
        )

        gainers = (

            df.sort_values(
                by="pChange",
                ascending=False
            )

            [["symbol", "pChange"]]

            .head(3)

        )

        losers = (

            df.sort_values(
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
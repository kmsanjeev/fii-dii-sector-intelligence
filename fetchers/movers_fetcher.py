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

        # NSE warm-up request
        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        response = session.get(
            "https://www.nseindia.com/api/live-analysis-variations?index=gainers",
            timeout=30
        )

        response.raise_for_status()

        gainers_data = (
            response.json()
        )

        gainers = pd.DataFrame(
            gainers_data.get(
                "data",
                []
            )
        )

        response = session.get(
            "https://www.nseindia.com/api/live-analysis-variations?index=losers",
            timeout=30
        )

        response.raise_for_status()

        losers_data = (
            response.json()
        )

        losers = pd.DataFrame(
            losers_data.get(
                "data",
                []
            )
        )

        if gainers.empty or losers.empty:

            logger.warning(
                "Movers data empty"
            )

            return (
                pd.DataFrame(),
                pd.DataFrame()
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
            .dropna(
                subset=["percentChange"]
            )

            [["symbol","percentChange"]]

            .head(3)

        )

        losers = (

            losers
            .dropna(
                subset=["percentChange"]
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
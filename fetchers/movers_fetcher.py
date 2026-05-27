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

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        url = (
            "https://www.nseindia.com/api/live-analysis-variations?index=gainers"
        )

        response = session.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        df = pd.DataFrame(
            data["data"]
        )

        gainers = (
            df[
                ["symbol", "percentChange"]
            ]
            .head(3)
        )

        url = (
            "https://www.nseindia.com/api/live-analysis-variations?index=losers"
        )

        response = session.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        df = pd.DataFrame(
            data["data"]
        )

        losers = (
            df[
                ["symbol", "percentChange"]
            ]
            .head(3)
        )

        logger.info(
            "Movers fetched"
        )

        return gainers, losers

    except Exception as e:

        logger.error(
            f"Movers error:{e}"
        )

        return pd.DataFrame(), pd.DataFrame()
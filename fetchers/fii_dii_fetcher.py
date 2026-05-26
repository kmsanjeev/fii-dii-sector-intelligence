import requests
import pandas as pd

from utils.logger import logger


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0"
    )
}


def fetch_fii_dii():

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        # Warm-up request required by NSE

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        url = (
            "https://www.nseindia.com/api/fiidiiTradeReact"
        )

        response = session.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        logger.info(
            "FII/DII data fetched"
        )

        return pd.DataFrame(
            data
        )

    except Exception as e:

        logger.error(
            f"Fetch Error: {e}"
        )

        return pd.DataFrame()
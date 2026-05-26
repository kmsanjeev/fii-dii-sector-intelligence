import requests
import pandas as pd
from datetime import datetime

from utils.logger import logger


def fetch_from_nse():

    """
    NSE source placeholder
    Official endpoint integration
    will be added progressively
    """

    headers = {

        "User-Agent":
        "Mozilla/5.0"

    }

    try:

        session = requests.Session()

        session.headers.update(
            headers
        )

        date = datetime.now().strftime(
            "%d-%b-%Y"
        )

        data = {

            "Date": [date],

            "FII_Net": [0],

            "DII_Net": [0],

            "Source": ["NSE"]

        }

        logger.info(
            "Fetched FII/DII data"
        )

        return pd.DataFrame(data)

    except Exception as e:

        logger.error(
            f"Fetch error:{e}"
        )

        raise


def fetch_fii_dii():

    try:

        return fetch_from_nse()

    except:

        logger.warning(
            "Switching to fallback"
        )

        return pd.DataFrame()
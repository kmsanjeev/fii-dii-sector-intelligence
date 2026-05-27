import requests
import pandas as pd

from utils.logger import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_sectors():

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
            "https://www.nseindia.com/api/allIndices"
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

        sector_keywords = [

            "NIFTY AUTO",
            "NIFTY BANK",
            "NIFTY FMCG",
            "NIFTY IT",
            "NIFTY MEDIA",
            "NIFTY METAL",
            "NIFTY PHARMA",
            "NIFTY PSU BANK",
            "NIFTY REALTY",
            "NIFTY HEALTHCARE"

        ]

        df = df[
            df["index"].isin(
                sector_keywords
            )
        ]

        logger.info(
            f"Sectors fetched: {len(df)}"
        )

        return df

    except Exception as e:

        logger.error(
            f"Sector error:{e}"
        )

        return pd.DataFrame()
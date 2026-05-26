import pandas as pd
import requests
from bs4 import BeautifulSoup

from fetchers.historical_backfill import (
    get_dates_for_current_run
)

from utils.logger import logger


HEADERS = {
    "User-Agent":
    "Mozilla/5.0"
}


def fetch_single_date_data(date):

    """
    Phase 1:
    Retrieve official data structure and normalize.

    If retrieval fails, return None and
    allow fallback logic later.
    """

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        # NSE warmup request
        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        # Placeholder for official parsing layer
        # Structure validation first

        record = {

            "Date": date,

            "FII_Buy": None,
            "FII_Sell": None,
            "FII_Net": None,

            "DII_Buy": None,
            "DII_Sell": None,
            "DII_Net": None,

            "Source": "Official"

        }

        return record

    except Exception as e:

        logger.warning(
            f"{date} fetch failed : {e}"
        )

        return None


def fetch_fii_dii_history():

    dates = (
        get_dates_for_current_run()
    )

    if not dates:

        logger.info(
            "Backfill complete"
        )

        return pd.DataFrame()

    records = []

    for date in dates:

        row = (
            fetch_single_date_data(
                date
            )
        )

        if row:

            records.append(
                row
            )

    logger.info(
        f"Fetched {len(records)} records"
    )

    return pd.DataFrame(
        records
    )
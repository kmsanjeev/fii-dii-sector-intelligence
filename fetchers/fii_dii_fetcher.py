import pandas as pd
import requests

from fetchers.historical_backfill import (
    get_dates_for_current_run
)

from utils.logger import logger


HEADERS = {
    "User-Agent":
    "Mozilla/5.0"
}


def fetch_single_date_data(date):

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

        # Temporary placeholder until
        # actual NSE parser is connected

        record = {

            "Date": date,

            "FII_Buy": 0,
            "FII_Sell": 0,
            "FII_Net": 0,

            "DII_Buy": 0,
            "DII_Sell": 0,
            "DII_Net": 0,

            "Source": "Pending_Official"

        }

        return record

    except Exception as e:

        logger.warning(
            f"{date} fetch failed: {e}"
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
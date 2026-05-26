import pandas as pd
import requests

from fetchers.historical_backfill import (
    get_dates_for_current_run
)

from utils.logger import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_single_date_data(date):

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        # Placeholder only
        # Real parser comes next phase

        record = {

            "Date": date,

            "FII_Buy": "",
            "FII_Sell": "",
            "FII_Net": "",

            "DII_Buy": "",
            "DII_Sell": "",
            "DII_Net": "",

            "Source": "Placeholder"

        }

        return record

    except Exception as e:

        logger.warning(
            f"{date} failed:{e}"
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

        row = fetch_single_date_data(
            date
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
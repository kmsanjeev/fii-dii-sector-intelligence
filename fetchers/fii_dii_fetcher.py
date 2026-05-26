import pandas as pd

from fetchers.historical_backfill import (
    get_dates_for_current_run
)

from utils.logger import logger


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

        records.append({

            "Date": date,

            "FII_Net": 0,

            "DII_Net": 0,

            "Source": "Historical"

        })

    logger.info(
        f"Fetched {len(records)} dates"
    )

    return pd.DataFrame(
        records
    )
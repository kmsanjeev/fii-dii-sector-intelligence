import pandas as pd

from fetchers.historical_backfill import (
    get_missing_dates
)

from utils.logger import logger


def fetch_fii_dii():

    dates = (
        get_missing_dates()
    )

    if not dates:

        return pd.DataFrame()

    rows = []

    for date in dates:

        rows.append({

            "Date": date,

            "FII_Buy": "",
            "FII_Sell": "",
            "FII_Net": "",

            "DII_Buy": "",
            "DII_Sell": "",
            "DII_Net": "",

            "Source": "Placeholder"

        })

    logger.info(
        f"Fetched:{len(rows)}"
    )

    return pd.DataFrame(
        rows
    )
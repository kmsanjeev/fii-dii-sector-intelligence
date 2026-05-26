import pandas as pd
from datetime import datetime
from pathlib import Path

from utils.logger import logger


BASE_PATH = Path(
    "data/historical/fii_dii"
)

BASE_PATH.mkdir(
    parents=True,
    exist_ok=True
)

FILE_PATH = (
    BASE_PATH /
    "fii_dii_history.csv"
)

BACKFILL_BATCH_SIZE = 500


def get_existing_dates():

    if not FILE_PATH.exists():

        return set()

    df = pd.read_csv(
        FILE_PATH
    )

    completed_dates = set()

    for _, row in df.iterrows():

        fii_net = row.get(
            "FII_Net"
        )

        dii_net = row.get(
            "DII_Net"
        )

        source = row.get(
            "Source"
        )

        is_complete = (

             source == "Official"

        )

        if is_complete:

            completed_dates.add(
                str(
                    row["Date"]
                )
            )

    return completed_dates


def generate_required_dates():

    end_date = datetime.now()

    start_date = datetime(
        end_date.year - 10,
        end_date.month,
        end_date.day
    )

    dates = pd.bdate_range(
        start=start_date,
        end=end_date
    )

    return sorted(
        dates.strftime(
            "%Y-%m-%d"
        )
    )


def get_missing_dates():

    existing_dates = (
        get_existing_dates()
    )

    required_dates = (
        generate_required_dates()
    )

    missing = [

        d for d in required_dates

        if d not in existing_dates

    ]

    logger.info(
        f"Missing dates:{len(missing)}"
    )

    return missing


def get_dates_for_current_run():

    missing = (
        get_missing_dates()
    )

    return missing[
        :BACKFILL_BATCH_SIZE
    ]


def save_historical_data(
        dataframe
):

    if FILE_PATH.exists():

        existing_df = pd.read_csv(
            FILE_PATH
        )

        dataframe = pd.concat(
            [
                existing_df,
                dataframe
            ]
        )

        dataframe = (
            dataframe
            .drop_duplicates(
                subset=["Date"]
            )
        )

    dataframe.to_csv(
        FILE_PATH,
        index=False
    )

    logger.info(
        "Historical file updated"
    )
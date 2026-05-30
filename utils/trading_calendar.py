import os
import pandas as pd

from datetime import datetime


HOLIDAY_FILE = (
    "data/reference/"
    "nse_holidays.csv"
)


def load_holidays():

    if not os.path.exists(
        HOLIDAY_FILE
    ):

        return set()

    df = pd.read_csv(
        HOLIDAY_FILE
    )

    date_column = df.columns[0]

    return set(

        pd.to_datetime(

            df[
                date_column
            ]

        )
        .dt.strftime(
            "%Y-%m-%d"
        )

    )


def is_nse_holiday(date_value):

    holiday_set = (
        load_holidays()
    )

    date_str = (

        pd.to_datetime(
            date_value
        )
        .strftime(
            "%Y-%m-%d"
        )

    )

    return (
        date_str
        in holiday_set
    )


def is_trading_day(date_value):

    date_obj = pd.to_datetime(
        date_value
    )

    if date_obj.weekday() >= 5:

        return False

    if is_nse_holiday(
        date_obj
    ):

        return False

    return True
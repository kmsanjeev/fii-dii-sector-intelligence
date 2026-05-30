import os
import pandas as pd

from nselib import trading_holiday_calendar

from utils.logger import logger


SAVE_FILE = (
    "data/reference/"
    "nse_holidays.csv"
)


def update_nse_holidays():

    try:

        os.makedirs(
            "data/reference",
            exist_ok=True
        )

        holiday_df = (
            trading_holiday_calendar()
        )

        if holiday_df.empty:

            logger.warning(
                "No NSE holidays returned"
            )

            return pd.DataFrame()

        holiday_df.columns = (

            holiday_df.columns
            .astype(str)
            .str.strip()

        )

        holiday_df.to_csv(

            SAVE_FILE,

            index=False

        )

        logger.info(

            f"NSE holidays saved: "
            f"{len(holiday_df)}"

        )

        return holiday_df

    except Exception as e:

        logger.error(
            f"NSE holiday error: {e}"
        )

        return pd.DataFrame()
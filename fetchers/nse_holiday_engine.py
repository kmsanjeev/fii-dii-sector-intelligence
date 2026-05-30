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

        holiday_df = (
            trading_holiday_calendar()
        )

        if holiday_df.empty:

            logger.warning(
                "No NSE holidays returned"
            )

            return

        # =====================
        # Equities Only
        # =====================

        holiday_df = holiday_df[

            holiday_df[
                "Product"
            ]
            .astype(str)
            .str.strip()
            .eq("Equities")

        ]

        # =====================
        # Required Columns Only
        # =====================

        holiday_df = holiday_df[[

            "tradingDate",
            "description"

        ]]

        holiday_df.columns = [

            "Date",
            "Holiday"

        ]

        # =====================
        # Standard Date Format
        # =====================

        holiday_df["Date"] = pd.to_datetime(

            holiday_df["Date"],
            dayfirst=True

        ).dt.strftime(
            "%Y-%m-%d"
        )

        # =====================
        # Remove Duplicates
        # =====================

        holiday_df = (

            holiday_df

            .drop_duplicates(
                subset=["Date"]
            )

            .sort_values(
                by="Date"
            )

            .reset_index(
                drop=True
            )

        )

        os.makedirs(

            "data/reference",

            exist_ok=True

        )

        holiday_df.to_csv(

            SAVE_FILE,

            index=False

        )

        logger.info(

            f"NSE Equity Holidays saved: "
            f"{len(holiday_df)}"

        )

    except Exception as e:

        logger.error(
            f"NSE holiday update error: {e}"
        )
import os
import pandas as pd

from datetime import datetime

from nselib import trading_holiday_calendar

from utils.logger import logger


SAVE_FILE = (
    "data/reference/"
    "nse_holidays.csv"
)


def update_nse_holidays():

    try:

        current_year = (
            datetime.now().year
        )

        # =====================
        # Load Existing History
        # =====================

        if os.path.exists(
            SAVE_FILE
        ):

            existing_df = (
                pd.read_csv(
                    SAVE_FILE
                )
            )

        else:

            existing_df = (
                pd.DataFrame(
                    columns=[
                        "Date",
                        "Year",
                        "Holiday"
                    ]
                )
            )

        # =====================
        # Skip Refresh
        # If Current Year Exists
        # =====================

        if (
            not existing_df.empty
            and
            "Year" in existing_df.columns
            and
            current_year in set(
                existing_df["Year"]
            )
        ):

            logger.info(
                f"NSE holidays already available "
                f"for {current_year}"
            )

            return

        # =====================
        # Fetch NSE Holidays
        # =====================

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

        holiday_df = holiday_df[[

            "tradingDate",
            "description"

        ]]

        holiday_df.columns = [

            "Date",
            "Holiday"

        ]

        holiday_df["Date"] = pd.to_datetime(

            holiday_df["Date"],
            dayfirst=True

        )

        holiday_df["Year"] = (
            holiday_df["Date"]
            .dt.year
        )

        holiday_df["Date"] = (

            holiday_df["Date"]
            .dt.strftime(
                "%Y-%m-%d"
            )

        )

        # =====================
        # Merge With History
        # =====================

        combined = pd.concat(

            [
                existing_df,
                holiday_df
            ],

            ignore_index=True

        )

        combined = (

            combined

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

        combined.to_csv(

            SAVE_FILE,

            index=False

        )

        logger.info(

            f"NSE holidays stored: "
            f"{len(combined)}"

        )

    except Exception as e:

        logger.error(
            f"NSE holiday update error: {e}"
        )
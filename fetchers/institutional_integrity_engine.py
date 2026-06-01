import os
import pandas as pd

from datetime import datetime
from datetime import timedelta

from utils.logger import logger
from utils.trading_calendar import (
    is_nse_holiday
)
from utils.institutional_availability import (
    is_known_unavailable
)


HISTORY_FILE = (
    "data/historical/institutional/"
    "institutional_positioning_history.csv"
)

REPORT_FILE = (
    "data/intelligence/"
    "institutional_integrity_report.csv"
)

MISSING_FILE = (
    "data/intelligence/"
    "institutional_missing_dates.csv"
)

UNAVAILABLE_FILE = (
    "data/reference/"
    "institutional_unavailable_dates.csv"
)


def generate_institutional_integrity_report():

    try:

        if not os.path.exists(
            HISTORY_FILE
        ):

            logger.warning(
                "Institutional history not found"
            )

            return

        df = pd.read_csv(
            HISTORY_FILE
        )

        existing_dates = set(

            pd.to_datetime(
                df["Date"]
            ).dt.strftime(
                "%Y-%m-%d"
            )

        )

        start_date = datetime(
            2016,
            1,
            1
        )

        end_date = datetime.now()

        expected_dates = []
        missing_dates = []

        current = start_date

        while current <= end_date:

            date_str = current.strftime(
                "%Y-%m-%d"
            )

            if current.weekday() >= 5:

                current += timedelta(
                    days=1
                )

                continue

            if is_nse_holiday(
                date_str
            ):

                current += timedelta(
                    days=1
                )

                continue

            if is_known_unavailable(
                date_str
            ):

                current += timedelta(
                    days=1
                )

                continue

            expected_dates.append(
                date_str
            )

            if (
                date_str
                not in existing_dates
            ):

                missing_dates.append(
                    date_str
                )

            current += timedelta(
                days=1
            )

        expected_count = len(
            expected_dates
        )

        actual_count = len(
            existing_dates
        )

        missing_count = len(
            missing_dates
        )

        unavailable_count = 0

        if os.path.exists(
            UNAVAILABLE_FILE
        ):

            unavailable_count = len(

                pd.read_csv(
                    UNAVAILABLE_FILE
                )

            )

        coverage_pct = round(

            (
                (
                    expected_count
                    -
                    missing_count
                )
                /
                expected_count
            ) * 100,

            2

        )

        if missing_count == 0:

            integrity_pct = 100.0

        else:

            integrity_pct = (
                coverage_pct
            )

        report_df = pd.DataFrame([{

            "Start_Date":
            min(existing_dates),

            "End_Date":
            max(existing_dates),

            "Expected_Trading_Days":
            expected_count,

            "Actual_Records":
            actual_count,

            "Missing_Dates":
            missing_count,

            "Unavailable_Dates":
            unavailable_count,

            "Coverage_Pct":
            coverage_pct,

            "Integrity_Pct":
            integrity_pct

        }])

        os.makedirs(
            "data/intelligence",
            exist_ok=True
        )

        report_df.to_csv(

            REPORT_FILE,

            index=False

        )

        pd.DataFrame({

            "Date":
            missing_dates

        }).to_csv(

            MISSING_FILE,

            index=False

        )

        logger.info(

            f"Coverage: "
            f"{coverage_pct}%"

        )

        logger.info(

            f"Integrity: "
            f"{integrity_pct}%"

        )

        logger.info(

            f"Missing Dates: "
            f"{missing_count}"

        )

    except Exception as e:

        logger.error(

            f"Institutional Integrity "
            f"Error: {e}"

        )
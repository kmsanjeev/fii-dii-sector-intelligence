import pandas as pd

from fetchers.sector_history_fetcher import (
    fetch_sector_history
)

from fetchers.thematic_history_fetcher import (
    fetch_thematic_history
)

from utils.logger import logger


def run_historical_engine():

    try:

        logger.info(
            "Historical Data Engine Started"
        )

        sector_history = (
            fetch_sector_history()
        )

        thematic_history = (
            fetch_thematic_history()
        )

        logger.info(
            "Historical Data Engine Completed"
        )

        return {

            "sector_history":
            sector_history,

            "thematic_history":
            thematic_history

        }

    except Exception as e:

        logger.error(
            f"Historical engine error: {e}"
        )

        return {

            "sector_history":
            pd.DataFrame(),

            "thematic_history":
            pd.DataFrame()

        }
from alerts.telegram_bot import (
    send_message
)

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii
)

from sheets.google_sheet_updater import (

    connect_sheet,
    create_sheet_if_missing,
    append_unique_dataframe

)

from utils.logger import logger

from fetchers.historical_backfill import (
    get_missing_dates
)


def main():

    logger.info(
        "Engine Started"
    )

    spreadsheet = connect_sheet()

    raw_sheet = create_sheet_if_missing(
        spreadsheet,
        "Raw_FII_DII"
    )

    df = fetch_fii_dii()

    append_unique_dataframe(
        raw_sheet,
        df
    )

    missing_dates = (
        get_missing_dates()
    )

    logger.info(
        f"Need to fetch "
        f"{len(missing_dates)} dates"
    )

    send_message(
        "📊 FII/DII test data updated"
    )


if __name__ == "__main__":

    main()
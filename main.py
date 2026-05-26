from alerts.telegram_bot import (
    send_message
)

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii_history
)

from fetchers.historical_backfill import (
    save_historical_data,
    get_missing_dates
)

from utils.logger import logger


def main():

    logger.info(
        "Engine Started"
    )

    # Get historical data for current batch

    df = (
        fetch_fii_dii_history()
    )

    # Backfill completed

    if df.empty:

        send_message(
"""
🎉 Historical Backfill Complete

Remaining Dates: 0

Status:
✅ Historical dataset fully loaded
"""
        )

        logger.info(
            "Backfill completed"
        )

        return

    # Save historical records

    save_historical_data(
        df
    )

    # Check remaining dates

    remaining_dates = len(
        get_missing_dates()
    )

    # Telegram summary

    message = f"""
📊 Historical Backfill Status

Records Loaded: {len(df)}
Fetched This Run: {len(df)}

Source: Official NSE/NSDL
Remaining Dates: {remaining_dates}

Status:
✅ Historical file updated
"""

    send_message(
        message
    )

    logger.info(
        f"Loaded {len(df)} records"
    )


if __name__ == "__main__":

    main()
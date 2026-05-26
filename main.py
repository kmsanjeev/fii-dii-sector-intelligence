from alerts.telegram_bot import send_message

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii
)

from fetchers.historical_backfill import (
    save_data,
    load_history,
    get_missing_dates
)

from utils.logger import logger


def main():

    logger.info(
        "Engine Started"
    )

    df = fetch_fii_dii()

    if not df.empty:

        save_data(df)

    history = load_history()

    total_rows = len(history)

    remaining = len(
        get_missing_dates()
    )

    message = f"""
📊 Historical Backfill Status

Records Loaded: {len(df)}
Fetched This Run: {len(df)}

Historical Records: {total_rows}

Remaining Dates: {remaining}

Source: Placeholder Framework

Status:
✅ Historical file updated
"""

    send_message(
        message
    )


if __name__ == "__main__":
    main()
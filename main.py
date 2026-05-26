from alerts.telegram_bot import (
    send_message
)

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii
)

from fetchers.historical_backfill import (
    save_data,
    load_history
)

from utils.logger import logger


def main():

    logger.info(
        "Engine Started"
    )

    df = fetch_fii_dii()

    if not df.empty:

        save_data(
            df
        )

    total_rows = len(
        load_history()
    )

    message = f"""
📊 Historical Backfill Status

Records Loaded: {len(df)}

Historical Records: {total_rows}

Fetched This Run: {len(df)}

Source: Placeholder Framework

Status:
✅ Historical file updated
"""

    send_message(
        message
    )


if __name__ == "__main__":
    main()
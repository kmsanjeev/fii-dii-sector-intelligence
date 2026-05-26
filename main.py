from alerts.telegram_bot import (
    send_message
)

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii_history
)

from fetchers.historical_backfill import (
    save_historical_data
)

from utils.logger import logger


def main():

    logger.info(
        "Engine Started"
    )

    df = (
        fetch_fii_dii_history()
    )

    if not df.empty:

        save_historical_data(
            df
        )

        send_message(

            f"📊 Historical records loaded: {len(df)}"

        )

    else:

        send_message(

            "✅ Historical backfill complete"

        )


if __name__ == "__main__":

    main()
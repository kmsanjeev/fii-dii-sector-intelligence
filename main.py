from alerts.telegram_bot import (
    send_message
)

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii
)

from utils.logger import logger


def main():

    logger.info(
        "Engine Started"
    )

    df = fetch_fii_dii()

    if df.empty:

        send_message(
"""
❌ FII/DII Fetch Failed
"""
        )

        return

    logger.info(
        f"Rows fetched: {len(df)}"
    )

    message = f"""
📊 Daily FII/DII Update

Rows fetched: {len(df)}

Status:
✅ Official source connected
"""

    send_message(
        message
    )


if __name__ == "__main__":
    main()
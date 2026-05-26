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
            "❌ FII/DII Fetch Failed"
        )

        return

    logger.info(
        f"Columns: {list(df.columns)}"
    )

    logger.info(
        f"\n{df.head()}"
    )

    preview = df.head().to_string()

    message = f"""
📊 FII/DII Structure Check

Rows fetched: {len(df)}

Columns:
{', '.join(df.columns)}

Preview:

{preview[:1000]}
"""

    send_message(
        message
    )


if __name__ == "__main__":
    main()
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

    row = df.iloc[0]

    message = f"""
📊 Daily FII/DII Update

Date: {row['Date']}

FII:
Buy: ₹{row['FII_Buy']} Cr
Sell: ₹{row['FII_Sell']} Cr
Net: ₹{row['FII_Net']} Cr

DII:
Buy: ₹{row['DII_Buy']} Cr
Sell: ₹{row['DII_Sell']} Cr
Net: ₹{row['DII_Net']} Cr

Source:
NSE
"""

    send_message(
        message
    )

    logger.info(
        "Telegram update sent"
    )


if __name__ == "__main__":
    main()
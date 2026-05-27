from alerts.telegram_bot import (
    send_message
)

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii
)

from fetchers.data_store import (
    save_fii_dii
)

from sheets.google_sheet_updater import (
    connect_sheet,
    create_sheet_if_missing,
    append_unique_dataframe
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

    # Save CSV

    save_fii_dii(
        df
    )

    # Google Sheet update

    spreadsheet = (
        connect_sheet()
    )

    if spreadsheet:

        worksheet = (
            create_sheet_if_missing(
                spreadsheet,
                "Raw_FII_DII"
            )
        )

        append_unique_dataframe(
            worksheet,
            df
        )

    row = df.iloc[0]

    message = f"""
📊 Daily FII/DII Update

Date: {row['Date']}

FII Net:
₹{row['FII_Net']} Cr

DII Net:
₹{row['DII_Net']} Cr

Net Difference:
₹{row['Net_Difference']} Cr

Sentiment:
{row['Market_Sentiment']}

Status:
✅ CSV updated
✅ Google Sheet updated
"""

    send_message(
        message
    )

    logger.info(
        "Completed"
    )


if __name__ == "__main__":

    main()
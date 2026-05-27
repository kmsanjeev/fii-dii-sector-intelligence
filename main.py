from alerts.telegram_bot import (
    send_message
)

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii
)

from fetchers.sector_fetcher import (
    fetch_sectors
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

    # ====================
    # FII / DII Processing
    # ====================

    df = fetch_fii_dii()

    if df.empty:

        send_message(
            "❌ FII/DII Fetch Failed"
        )

        return

    save_fii_dii(
        df
    )

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

    fii_message = f"""
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
        fii_message
    )

    # ====================
    # Sector Processing
    # ====================

    sector_df = fetch_sectors()

    if not sector_df.empty:

        top_sector = (

            sector_df
            .sort_values(
                by="percentChange",
                ascending=False
            )
            .iloc[0]

        )

        sector_message = f"""
🔥 Strongest Sector

Sector:
{top_sector['index']}

Change:
{top_sector['percentChange']}%
"""

        send_message(
            sector_message
        )

        logger.info(
            "Sector update sent"
        )

    logger.info(
        "Completed"
    )


if __name__ == "__main__":

    main()
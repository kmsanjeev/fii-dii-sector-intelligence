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

    # ====================
    # Sector Processing
    # ====================

    top_sector_text = "N/A"
    bottom_sector_text = "N/A"

    sector_df = fetch_sectors()

    if not sector_df.empty:

        sector_df["percentChange"] = (
            sector_df["percentChange"]
            .astype(float)
        )

        top3 = (

            sector_df
            .sort_values(
                by="percentChange",
                ascending=False
            )
            .head(3)

        )

        bottom3 = (

            sector_df
            .sort_values(
                by="percentChange",
                ascending=True
            )
            .head(3)

        )

        top_sector_text = "\n".join([

            f"{i+1}. {row['index']} : {row['percentChange']}%"

            for i, (_, row)

            in enumerate(
                top3.iterrows()
            )

        ])

        bottom_sector_text = "\n".join([

            f"{i+1}. {row['index']} : {row['percentChange']}%"

            for i, (_, row)

            in enumerate(
                bottom3.iterrows()
            )

        ])

    # ====================
    # Final Telegram Report
    # ====================

    message = f"""
📊 Market Intelligence Report

Date: {row['Date']}

━━━━━━━━━━━━━━

💰 FII / DII Flow

FII Net: ₹{row['FII_Net']} Cr
DII Net: ₹{row['DII_Net']} Cr
Net Difference: ₹{row['Net_Difference']} Cr

Sentiment: {row['Market_Sentiment']}

━━━━━━━━━━━━━━

🔥 Top 3 Sectors

{top_sector_text}

📉 Bottom 3 Sectors

{bottom_sector_text}

━━━━━━━━━━━━━━

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
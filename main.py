from alerts.telegram_bot import (
    send_message
)

from fetchers.fii_dii_fetcher import (
    fetch_fii_dii
)

from fetchers.sector_fetcher import (
    fetch_sectors
)

from fetchers.movers_fetcher import (
    fetch_top_movers
)

from fetchers.sector_stock_mapper import (
    fetch_sector_leaders
)

from storage.fii_dii_history_manager import (
    append_historical_data
)

from fetchers.signal_engine import (
    generate_signals
)

from fetchers.data_store import (
    save_fii_dii
)

from fetchers.sector_history_fetcher import (
    fetch_sector_history
)

from sheets.google_sheet_updater import (
    connect_sheet,
    create_sheet_if_missing,
    append_unique_dataframe
)

from sheets.signal_sheet_updater import (
    save_signals_to_sheet
)

from utils.logger import logger


def main():

    logger.info(
        "Engine Started"
    )

    # ====================
    # Sector Historical Data
    # ====================

    sector_history = (
        fetch_sector_history()
    )

    # ====================
    # Daily FII/DII Fetch
    # ====================

    df = fetch_fii_dii()

    if df.empty:

        send_message(
            "❌ FII/DII Fetch Failed"
        )

        return

    # ====================
    # Historical FII/DII Archive
    # ====================

    append_historical_data(
        df
    )

    # ====================
    # Save Latest CSV
    # ====================

    save_fii_dii(df)

    # ====================
    # Google Sheets
    # ====================

    spreadsheet = connect_sheet()

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

    top_sector_text = "N/A"
    bottom_sector_text = "N/A"

    strongest_sector = None
    weakest_sector = None

    # ====================
    # Sector Fetch
    # ====================

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
                by="percentChange"
            )
            .head(3)

        )

        strongest_sector = (
            top3.iloc[0]["index"]
        )

        weakest_sector = (
            bottom3.iloc[0]["index"]
        )

        top_sector_text = "\n".join([

            f"{i+1}. {r['index']}: {round(r['percentChange'],2)}%"

            for i, (_, r)

            in enumerate(
                top3.iterrows()
            )

        ])

        bottom_sector_text = "\n".join([

            f"{i+1}. {r['index']}: {round(r['percentChange'],2)}%"

            for i, (_, r)

            in enumerate(
                bottom3.iterrows()
            )

        ])

    # ====================
    # Sector Leaders
    # ====================

    sector_leader_text = "N/A"

    if strongest_sector:

        leaders = fetch_sector_leaders(
            strongest_sector
        )

        if not leaders.empty:

            sector_leader_text = "\n".join([

                f"{i+1}. {r['symbol']}: +{round(r['change'],2)}%"

                for i, (_, r)

                in enumerate(
                    leaders.iterrows()
                )

            ])

    # ====================
    # Movers
    # ====================

    gainers, losers = (
        fetch_top_movers()
    )

    # ====================
    # Signal Generation
    # ====================

    signals = generate_signals(

        row["Date"],

        gainers,
        losers,

        strongest_sector,
        weakest_sector,

        round(
            float(
                top3.iloc[0]["percentChange"]
            ),
            2
        ),

        round(
            float(
                bottom3.iloc[0]["percentChange"]
            ),
            2
        ),

        row["Combined_Net_Flow"]

    )

    # ====================
    # Save Signals
    # ====================

    if spreadsheet:

        save_signals_to_sheet(

            spreadsheet,
            signals

        )

    # ====================
    # Telegram Message
    # ====================

    message = f"""
📊 Market Intelligence Report

Date: {row['Date']}

━━━━━━━━━━━━━━

💰 FII / DII Flow

FII Net: ₹{row['FII_Net']} Cr
DII Net: ₹{row['DII_Net']} Cr
Combined Net Flow: ₹{row['Combined_Net_Flow']} Cr

Sentiment: {row['Market_Sentiment']}

━━━━━━━━━━━━━━

🔥 Top 3 Sectors

{top_sector_text}

📉 Bottom 3 Sectors

{bottom_sector_text}

━━━━━━━━━━━━━━

🚀 Leaders in {strongest_sector}

{sector_leader_text}

━━━━━━━━━━━━━━

Status:

✅ CSV updated
✅ Google Sheet updated
✅ Historical archive updated
"""

    send_message(message)

    logger.info(
        "Completed"
    )


if __name__ == "__main__":
    main()
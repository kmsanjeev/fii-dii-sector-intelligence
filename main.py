from fetchers.sector_stock_mapper import (
    fetch_sector_leaders
)

# keep all your previous imports unchanged


def main():

    logger.info(
        "Engine Started"
    )

    # Existing code unchanged above...

    strongest_sector = None

    if not sector_df.empty:

        strongest_sector = (
            top3.iloc[0]["index"]
        )

    sector_leader_text = "N/A"

    if strongest_sector:

        leaders = (

            fetch_sector_leaders(
                strongest_sector
            )

        )

        if not leaders.empty:

            sector_leader_text = "\n".join([

                f"{i+1}. {r['symbol']}: +{round(r['change'],2)}%"

                for i,(_,r)

                in enumerate(
                    leaders.iterrows()
                )

            ])

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

📈 Top Gainers

{gainers_text}

📉 Top Losers

{losers_text}

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
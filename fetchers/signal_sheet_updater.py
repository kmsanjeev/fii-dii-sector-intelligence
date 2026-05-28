import pandas as pd

from utils.logger import logger


def save_signals_to_sheet(
    spreadsheet,
    signals
):

    try:

        try:

            worksheet = spreadsheet.worksheet(
                "Momentum_Signals"
            )

            logger.info(
                "Momentum_Signals exists"
            )

        except:

            worksheet = spreadsheet.add_worksheet(

                title="Momentum_Signals",

                rows=1000,

                cols=10

            )

            worksheet.append_row([

                "Date",
                "Signal",
                "Stock",
                "Sector",
                "Strength"

            ])

            logger.info(
                "Momentum_Signals created"
            )

        if signals.empty:

            logger.info(
                "No signals to insert"
            )

            return

        existing = (
            worksheet.get_all_records()
        )

        existing_keys = {

            (
                str(x["Date"]),
                str(x["Stock"])
            )

            for x in existing

        }

        rows=[]

        for _,r in signals.iterrows():

            key=(

                str(
                    r["Date"]
                ),

                str(
                    r["Stock"]
                )

            )

            if key not in existing_keys:

                rows.append([

                    r["Date"],
                    r["Signal"],
                    r["Stock"],
                    r["Sector"],
                    r["Strength"]

                ])

        if rows:

            worksheet.append_rows(
                rows
            )

            logger.info(
                f"Added {len(rows)} signals"
            )

        else:

            logger.info(
                "No new signals"
            )

    except Exception as e:

        logger.error(
            f"Signal sheet error: {e}"
        )
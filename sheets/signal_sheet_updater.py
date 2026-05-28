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

                rows=5000,

                cols=20

            )

            worksheet.append_row([

                "Date",
                "Signal",
                "Stock",
                "Sector",
                "Strength",
                "Score",
                "Stock_Change",
                "Sector_Change",
                "Flow_Bias",
                "Last_Updated"

            ])

            logger.info(
                "Momentum_Signals created"
            )

        if signals.empty:

            logger.info(
                "No signals to process"
            )

            return

        existing = (
            worksheet.get_all_records()
        )

        existing_map = {}

        for idx, row in enumerate(existing):

            key = (

                str(row["Date"]),
                str(row["Stock"])

            )

            # +2 because sheets are 1-indexed
            # and row 1 is header

            existing_map[key] = idx + 2

        added = 0
        updated = 0

        for _, r in signals.iterrows():

            key = (

                str(r["Date"]),
                str(r["Stock"])

            )

            row_values = [

                r["Date"],
                r["Signal"],
                r["Stock"],
                r["Sector"],
                r["Strength"],
                r["Score"],
                r["Stock_Change"],
                r["Sector_Change"],
                r["Flow_Bias"],
                pd.Timestamp.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            ]

            # ====================
            # UPDATE EXISTING
            # ====================

            if key in existing_map:

                row_number = (
                    existing_map[key]
                )

                worksheet.update(

                    f"A{row_number}:J{row_number}",

                    [row_values]

                )

                updated += 1

            # ====================
            # INSERT NEW
            # ====================

            else:

                worksheet.append_row(
                    row_values
                )

                added += 1

        logger.info(
            f"Signals Added: {added}"
        )

        logger.info(
            f"Signals Updated: {updated}"
        )

    except Exception as e:

        logger.error(
            f"Signal sheet error: {e}"
        )
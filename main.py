from alerts.telegram_bot import (
    send_message
)

from sheets.google_sheet_updater import (
    connect_sheet,
    create_sheet_if_missing
)

from utils.logger import logger


def main():

    logger.info(
        "Engine Started"
    )

    spreadsheet = connect_sheet()

    if spreadsheet:

        sheet_names = [

            "Raw_FII_DII",
            "Sector_Data",
            "Stock_Movers",
            "Signals",
            "Dashboard"

        ]

        for sheet in sheet_names:

            create_sheet_if_missing(
                spreadsheet,
                sheet
            )

        send_message(
            "✅ Google Sheet Connected Successfully"
        )

    else:

        send_message(
            "❌ Google Sheet Connection Failed"
        )


if __name__ == "__main__":

    main()
import gspread

from google.oauth2.service_account import (
    Credentials
)

from config import (
    GOOGLE_CREDS,
    SHEET_NAME
)

from utils.logger import logger


SCOPES = [

    "https://www.googleapis.com/auth/spreadsheets",

    "https://www.googleapis.com/auth/drive"

]


def connect_sheet():

    try:

        credentials = Credentials.from_service_account_info(
            GOOGLE_CREDS,
            scopes=SCOPES
        )

        client = gspread.authorize(
            credentials
        )

        spreadsheet = client.open(
            SHEET_NAME
        )

        logger.info(
            "Google Sheet connected"
        )

        return spreadsheet

    except Exception as e:

        logger.error(
            f"Google connection error: {e}"
        )

        return None


def create_sheet_if_missing(
        spreadsheet,
        sheet_name
):

    try:

        worksheet = spreadsheet.worksheet(
            sheet_name
        )

        logger.info(
            f"{sheet_name} exists"
        )

    except:

        worksheet = spreadsheet.add_worksheet(

            title=sheet_name,

            rows=1000,

            cols=20

        )

        logger.info(
            f"{sheet_name} created"
        )

    return worksheet


def append_unique_dataframe(
        worksheet,
        dataframe
):

    values = worksheet.get_all_values()

    headers = dataframe.columns.tolist()

    # Header handling

    if (

        len(values) == 0

        or

        len(values[0]) == 0

        or

        values[0] != headers

    ):

        worksheet.clear()

        worksheet.append_row(
            headers
        )

        values = worksheet.get_all_values()

        logger.info(
            "Headers created"
        )

    existing_dates = set()

    if len(values) > 1:

        date_index = headers.index(
            "Date"
        )

        for row in values[1:]:

            if len(row) > date_index:

                existing_dates.add(
                    row[
                        date_index
                    ]
                )

    rows = []

    for _, row in dataframe.iterrows():

        if str(
            row["Date"]
        ) not in existing_dates:

            rows.append(
                row.tolist()
            )

    if rows:

        worksheet.append_rows(
            rows
        )

        logger.info(
            f"Added {len(rows)} rows"
        )

    else:

        logger.info(
            "No new rows"
        )
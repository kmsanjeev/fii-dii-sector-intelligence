import gspread
from google.oauth2.service_account import Credentials

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
            f"Google Sheet Error: {e}"
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

def append_dataframe(
        worksheet,
        dataframe
):

    values = dataframe.values.tolist()

    if worksheet.row_count == 0:

        worksheet.append_row(
            dataframe.columns.tolist()
        )

    worksheet.append_rows(
        values
    )

    def append_unique_dataframe(
        worksheet,
        dataframe,
        key_column=0
):

    existing_values = worksheet.get_all_values()

    existing_keys = set()

    if len(existing_values) > 1:

        for row in existing_values[1:]:

            if len(row) > key_column:

                existing_keys.add(
                    row[key_column]
                )

    new_rows = []

    for _, row in dataframe.iterrows():

        key = str(
            row.iloc[key_column]
        )

        if key not in existing_keys:

            new_rows.append(
                row.tolist()
            )

    if len(existing_values) == 0:

        worksheet.append_row(
            dataframe.columns.tolist()
        )

    if new_rows:

        worksheet.append_rows(
            new_rows
        )
import os
import json

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID"
)

GOOGLE_CREDS = json.loads(
    os.getenv("GOOGLE_CREDENTIALS")
)

SHEET_NAME = (
    "NSE_FII_DII_Sector_Intelligence"
)

TIMEZONE = "Asia/Kolkata"
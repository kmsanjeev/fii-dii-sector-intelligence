import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID
)

from utils.logger import logger


def send_message(message):

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}"
        f"/sendMessage"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:

        response = requests.post(
            url,
            data=payload,
            timeout=30
        )

        response.raise_for_status()

        logger.info(
            "Telegram message sent"
        )

    except Exception as e:

        logger.error(
            f"Telegram Error: {e}"
        )
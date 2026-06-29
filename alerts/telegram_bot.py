"""
Telegram Bot — Phase 9C
Sends formatted alerts via Telegram Bot API.
Credentials always from environment — NEVER hardcoded.
"""

import os
import time
import requests
from typing import Optional

from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Config (from environment) ─────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID:   Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

SEND_DELAY_S = 0.1      # 100ms between messages to respect Telegram rate limit
MAX_MSG_LEN  = 4096     # Telegram message character limit
API_TIMEOUT  = 30


def _check_credentials() -> bool:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("[TelegramBot] TELEGRAM_BOT_TOKEN not set in environment")
        return False
    if not TELEGRAM_CHAT_ID:
        logger.error("[TelegramBot] TELEGRAM_CHAT_ID not set in environment")
        return False
    return True


def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a single Telegram message. Returns True on success."""
    if not _check_credentials():
        return False

    text = text[:MAX_MSG_LEN]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=API_TIMEOUT)
        resp.raise_for_status()
        logger.info("[TelegramBot] Message sent")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"[TelegramBot] HTTP error: {e} | response: {resp.text[:200]}")
        return False
    except Exception as e:
        logger.error(f"[TelegramBot] Send failed: {e}")
        return False


def send_alerts(alerts: list) -> int:
    """
    Send a list of Alert objects. Returns count of successfully sent messages.
    Respects 100ms delay between sends (Telegram 30msg/s limit).
    """
    if not alerts:
        return 0

    sent = 0
    for alert in alerts:
        text = _format_alert(alert)
        if send_message(text):
            sent += 1
        time.sleep(SEND_DELAY_S)

    logger.info(f"[TelegramBot] Sent {sent}/{len(alerts)} alerts")
    return sent


def _format_alert(alert) -> str:
    """Format an Alert object as Telegram HTML text."""
    priority_emoji = {1: "[!!]", 2: "[**]", 3: "[>>]", 4: "[$$]", 5: "[CO]", 6: "[~~]", 7: "[DG]"}
    icon = priority_emoji.get(alert.priority, "[  ]")

    lines = [
        f"<b>{icon} {alert.title}</b>",
        "",
        alert.body,
    ]
    if alert.score is not None:
        lines.append(f"Score: <b>{alert.score:.1f}</b>")
    if alert.data_date:
        lines.append(f"Data date: {alert.data_date}")
    lines.append(f"<i>Generated: {alert.created_at}</i>")

    return "\n".join(lines)


def send_raw(text: str) -> bool:
    """Send raw pre-formatted text (used by daily_digest)."""
    return send_message(text)


def test_connection() -> bool:
    """Verify bot token and chat ID work by sending a test ping."""
    return send_message(
        "<b>Capital Flow Intelligence Platform</b>\nAlert system connected successfully."
    )

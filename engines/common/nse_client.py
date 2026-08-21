import logging
import time

import requests

from engines.common.config import API_TIMEOUT, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    # Avoid intermittent Brotli decode failures in the installed requests stack.
    "Accept-Encoding": "identity",
    "Referer": "https://www.nseindia.com/",
}


def create_session(origin_url="https://www.nseindia.com/"):
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get(origin_url, timeout=API_TIMEOUT)
    except requests.RequestException as exc:
        logger.debug("NSE session bootstrap failed: %s", exc)
    return session


def get(session, url):
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=API_TIMEOUT)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            logger.debug("NSE request attempt %s failed: %s", attempt + 1, exc)
            if attempt + 1 < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None

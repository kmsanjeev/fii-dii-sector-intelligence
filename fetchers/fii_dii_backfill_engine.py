import requests
from bs4 import BeautifulSoup

from utils.logger import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


ARCHIVE_URL = (
    "https://www.nseindia.com/"
    "static/all-reports/"
    "historical-equities-fii-fpi-dii-trading-activity"
)


def discover_archive_links():

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        response = session.get(
            ARCHIVE_URL,
            timeout=30
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        links = []

        for tag in soup.find_all("a"):

            href = tag.get("href")

            if not href:
                continue

            if any(
                ext in href.lower()
                for ext in [
                    ".csv",
                    ".xls",
                    ".xlsx",
                    ".zip"
                ]
            ):

                links.append(href)

        links = list(
            set(links)
        )

        logger.info(
            f"Archive files found: "
            f"{len(links)}"
        )

        for link in links:

            logger.info(
                f"Archive: {link}"
            )

        return links

    except Exception as e:

        logger.error(
            f"Backfill discovery error: {e}"
        )

        return []


def run_backfill_discovery():

    logger.info(
        "Starting FII/DII archive discovery"
    )

    links = (
        discover_archive_links()
    )

    logger.info(
        f"Discovery completed. "
        f"Files found: {len(links)}"
    )

    return links
import requests
import json

from utils.logger import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


TEST_ENDPOINTS = [

    "https://www.nseindia.com/api/fiidiiTradeReact",

    "https://www.nseindia.com/api/reports-fiidii",

    "https://www.nseindia.com/api/historical/fiidii",

    "https://www.nseindia.com/api/fiiDiiTradeHistory"

]


TEST_DATES = [

    "01-01-2025",
    "01-01-2024",
    "01-01-2023"

]


def test_endpoint(
    session,
    url
):

    try:

        response = session.get(
            url,
            timeout=30
        )

        logger.info(
            f"Endpoint: {url}"
        )

        logger.info(
            f"Status: "
            f"{response.status_code}"
        )

        if response.status_code == 200:

            logger.info(
                f"Content-Type: "
                f"{response.headers.get('Content-Type')}"
            )

            text = response.text[:500]

            logger.info(
                f"Preview: {text}"
            )

        return response.status_code

    except Exception as e:

        logger.warning(
            f"Failed: {url}"
        )

        logger.warning(
            str(e)
        )

        return None


def test_date_parameter(
    session,
    base_url
):

    for date in TEST_DATES:

        try:

            response = session.get(

                base_url,

                params={
                    "date": date
                },

                timeout=30

            )

            logger.info(
                f"Date Test: "
                f"{date}"
            )

            logger.info(
                f"Status: "
                f"{response.status_code}"
            )

            if response.status_code == 200:

                logger.info(
                    response.text[:300]
                )

        except Exception as e:

            logger.warning(
                f"Date test failed: "
                f"{e}"
            )


def run_api_recon():

    logger.info(
        "NSE API Recon Started"
    )

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        for endpoint in TEST_ENDPOINTS:

            status = test_endpoint(
                session,
                endpoint
            )

            if status == 200:

                test_date_parameter(
                    session,
                    endpoint
                )

        logger.info(
            "NSE API Recon Completed"
        )

    except Exception as e:

        logger.error(
            f"Recon error: {e}"
        )
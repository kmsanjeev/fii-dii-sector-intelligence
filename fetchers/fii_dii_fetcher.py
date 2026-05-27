import requests
import pandas as pd

from utils.logger import logger


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_fii_dii():

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        url = (
            "https://www.nseindia.com/api/fiidiiTradeReact"
        )

        response = session.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        raw = response.json()

        fii = next(
            x for x in raw
            if x["category"] == "FII/FPI"
        )

        dii = next(
            x for x in raw
            if x["category"] == "DII"
        )

        final = pd.DataFrame([{

            "Date":
            fii["date"],

            "FII_Buy":
            fii["buyValue"],

            "FII_Sell":
            fii["sellValue"],

            "FII_Net":
            fii["netValue"],

            "DII_Buy":
            dii["buyValue"],

            "DII_Sell":
            dii["sellValue"],

            "DII_Net":
            dii["netValue"],

            "Net_Difference":
            round(
                dii["netValue"]
                -
                fii["netValue"],
                2
            ),

            "Market_Sentiment":

            "Bullish"

            if fii["netValue"] > 1000

            else

            "Bearish"

            if fii["netValue"] < -1000

            else

            "Neutral",

            "Source":
            "NSE"

        }])

        logger.info(
            "Normalized FII/DII data"
        )

        return final

    except Exception as e:

        logger.error(
            f"Fetch Error:{e}"
        )

        return pd.DataFrame()
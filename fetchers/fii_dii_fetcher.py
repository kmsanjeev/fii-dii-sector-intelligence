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

        # Convert strings to float

        fii_buy = float(
            fii["buyValue"]
        )

        fii_sell = float(
            fii["sellValue"]
        )

        fii_net = float(
            fii["netValue"]
        )

        dii_buy = float(
            dii["buyValue"]
        )

        dii_sell = float(
            dii["sellValue"]
        )

        dii_net = float(
            dii["netValue"]
        )

        net_difference = round(
            dii_net - fii_net,
            2
        )

        sentiment = (

            "Bullish"

            if fii_net > 1000

            else

            "Bearish"

            if fii_net < -1000

            else

            "Neutral"

        )

        final = pd.DataFrame([{

            "Date":
            fii["date"],

            "FII_Buy":
            fii_buy,

            "FII_Sell":
            fii_sell,

            "FII_Net":
            fii_net,

            "DII_Buy":
            dii_buy,

            "DII_Sell":
            dii_sell,

            "DII_Net":
            dii_net,

            "Net_Difference":
            net_difference,

            "Market_Sentiment":
            sentiment,

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
import requests
import pandas as pd

from utils.logger import logger


HEADERS = {
    "User-Agent":"Mozilla/5.0"
}


def fetch_top_movers():

    try:

        session=requests.Session()

        session.headers.update(
            HEADERS
        )

        session.get(
            "https://www.nseindia.com",
            timeout=30
        )

        response=session.get(
            "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050",
            timeout=30
        )

        response.raise_for_status()

        data=response.json()

        df=pd.DataFrame(
            data["data"]
        )

        df["pChange"]=df[
            "pChange"
        ].astype(float)

        gainers=(

            df.sort_values(
                by="pChange",
                ascending=False
            )

            [["symbol","pChange"]]

            .head(3)

        )

        losers=(

            df.sort_values(
                by="pChange"
            )

            [["symbol","pChange"]]

            .head(3)

        )

        logger.info(
            "Movers fetched"
        )

        return gainers,losers

    except Exception as e:

        logger.error(
            f"Movers error:{e}"
        )

        return pd.DataFrame(),pd.DataFrame()
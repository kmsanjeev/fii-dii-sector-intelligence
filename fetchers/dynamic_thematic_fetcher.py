import requests
import pandas as pd

from bs4 import BeautifulSoup

from utils.logger import logger


URL = (
    "https://www.niftyindices.com/"
    "indices/equity/thematic-indices"
)


HEADERS = {

    "User-Agent":
    "Mozilla/5.0"

}


def fetch_dynamic_thematic_indices():

    try:

        logger.info(
            "Fetching official thematic indices"
        )

        response = requests.get(

            URL,

            headers=HEADERS,

            timeout=30

        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        tables = soup.find_all("table")

        if not tables:

            logger.warning(
                "No thematic tables found"
            )

            return pd.DataFrame()

        thematic_data = []

        for table in tables:

            rows = table.find_all("tr")

            for row in rows[1:]:

                cols = row.find_all("td")

                if len(cols) < 1:

                    continue

                theme_name = (
                    cols[0]
                    .get_text(strip=True)
                )

                if not theme_name:

                    continue

                thematic_data.append({

                    "Theme":
                    theme_name

                })

        if not thematic_data:

            logger.warning(
                "No thematic indices discovered"
            )

            return pd.DataFrame()

        df = pd.DataFrame(
            thematic_data
        )

        df = df.drop_duplicates()

        logger.info(

            f"Thematic indices discovered: "
            f"{len(df)}"

        )

        return df

    except Exception as e:

        logger.error(
            f"Dynamic thematic fetch error: {e}"
        )

        return pd.DataFrame()
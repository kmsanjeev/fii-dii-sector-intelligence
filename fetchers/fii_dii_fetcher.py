import pandas as pd
from datetime import datetime


def fetch_fii_dii():

    """
    Temporary test data.
    NSE integration will replace this later.
    """

    data = {

        "Date": [
            datetime.now().strftime(
                "%d-%b-%Y"
            )
        ],

        "FII_Net": [5000],

        "DII_Net": [2500]

    }

    return pd.DataFrame(data)
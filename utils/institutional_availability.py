import os
import pandas as pd


CACHE_FILE = (
    "data/reference/"
    "institutional_unavailable_dates.csv"
)


def initialize_cache():

    if not os.path.exists(
        CACHE_FILE
    ):

        pd.DataFrame(

            columns=[

                "Date",
                "Reason",
                "First_Seen"

            ]

        ).to_csv(

            CACHE_FILE,
            index=False

        )


def is_known_unavailable(
    date_str
):

    initialize_cache()

    df = pd.read_csv(
        CACHE_FILE
    )

    return (
        date_str
        in df["Date"]
        .astype(str)
        .values
    )


def add_unavailable_date(
    date_str,
    reason
):

    initialize_cache()

    df = pd.read_csv(
        CACHE_FILE
    )

    if (
        date_str
        in df["Date"]
        .astype(str)
        .values
    ):

        return

    new_row = pd.DataFrame([{

        "Date":
        date_str,

        "Reason":
        reason,

        "First_Seen":
        pd.Timestamp.today()
        .strftime(
            "%Y-%m-%d"
        )

    }])

    df = pd.concat(

        [df, new_row],

        ignore_index=True

    )

    df.to_csv(

        CACHE_FILE,

        index=False

    )
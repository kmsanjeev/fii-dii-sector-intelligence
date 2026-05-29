import os
import pandas as pd

from utils.logger import logger


TRACKING_FILE = (
    "data/intelligence/"
    "leadership_tracking.csv"
)

OUTPUT_FILE = (
    "data/intelligence/"
    "sector_leadership_duration.csv"
)


def classify(days):

    if days >= 20:
        return "DOMINANT LEADER"

    if days >= 10:
        return "ESTABLISHED LEADER"

    if days >= 5:
        return "EMERGING LEADER"

    if days >= 1:
        return "NEW LEADER"

    return "NON LEADER"


def generate_leadership_duration():

    try:

        persistence = pd.read_csv(
            "data/intelligence/"
            "sector_persistence_scores.csv"
        )

        leaders = persistence[
            persistence[
                "Persistence_Score"
            ] >= 70
        ][["Sector"]]

        if os.path.exists(
            TRACKING_FILE
        ):

            tracking = pd.read_csv(
                TRACKING_FILE
            )

        else:

            tracking = pd.DataFrame(
                columns=[
                    "Sector",
                    "Leadership_Duration"
                ]
            )

        updated = []

        sectors = persistence[
            "Sector"
        ].tolist()

        for sector in sectors:

            previous = 0

            if not tracking.empty:

                existing = tracking[

                    tracking[
                        "Sector"
                    ] == sector

                ]

                if not existing.empty:

                    previous = int(

                        existing.iloc[0][
                            "Leadership_Duration"
                        ]

                    )

            if sector in leaders[
                "Sector"
            ].values:

                duration = (
                    previous + 1
                )

            else:

                duration = 0

            updated.append({

                "Sector": sector,

                "Leadership_Duration":
                duration

            })

        result = pd.DataFrame(
            updated
        )

        result.to_csv(
            TRACKING_FILE,
            index=False
        )

        output = result.copy()

        output[
            "Leadership_Status"
        ] = output[
            "Leadership_Duration"
        ].apply(
            classify
        )

        output.to_csv(
            OUTPUT_FILE,
            index=False
        )

        logger.info(
            "Leadership duration generated"
        )

    except Exception as e:

        logger.error(
            f"Leadership error: {e}"
        )
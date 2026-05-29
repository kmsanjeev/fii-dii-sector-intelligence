import os
import pandas as pd

from utils.logger import logger


AGGREGATED_PATH = (
    "data/aggregated/"
)

OUTPUT_PATH = (
    "data/intelligence/"
)


def ensure_directory():

    os.makedirs(
        OUTPUT_PATH,
        exist_ok=True
    )


def classify_score(score):

    if score >= 85:
        return "LEADER"

    if score >= 70:
        return "STRONG"

    if score >= 55:
        return "IMPROVING"

    if score >= 40:
        return "NEUTRAL"

    return "WEAK"


def normalize_score(
    value,
    min_value,
    max_value
):

    if max_value == min_value:
        return 50

    return round(

        (
            (
                value
                -
                min_value
            )

            /

            (
                max_value
                -
                min_value
            )
        )

        * 100,

        2

    )


def generate_entity_scores(

    weekly_df,
    biweekly_df,
    monthly_df,
    entity_column

):

    merged = (

        monthly_df[[

            entity_column,
            "Return_%"

        ]]

        .rename(

            columns={
                "Return_%":
                "Monthly_Return"
            }

        )

    )

    merged = merged.merge(

        biweekly_df[[

            entity_column,
            "Return_%"

        ]]

        .rename(

            columns={
                "Return_%":
                "Biweekly_Return"
            }

        ),

        on=entity_column

    )

    merged = merged.merge(

        weekly_df[[

            entity_column,
            "Return_%"

        ]]

        .rename(

            columns={
                "Return_%":
                "Weekly_Return"
            }

        ),

        on=entity_column

    )

    merged[
        "Raw_Score"
    ] = (

        merged[
            "Weekly_Return"
        ] * 0.30

        +

        merged[
            "Biweekly_Return"
        ] * 0.30

        +

        merged[
            "Monthly_Return"
        ] * 0.40

    )

    min_score = (
        merged[
            "Raw_Score"
        ].min()
    )

    max_score = (
        merged[
            "Raw_Score"
        ].max()
    )

    merged[
        "Persistence_Score"
    ] = merged[
        "Raw_Score"
    ].apply(

        lambda x:
        normalize_score(
            x,
            min_score,
            max_score
        )

    )

    merged[
        "Status"
    ] = merged[
        "Persistence_Score"
    ].apply(
        classify_score
    )

    merged = (

        merged
        .sort_values(
            by=
            "Persistence_Score",
            ascending=False
        )

        .reset_index(
            drop=True
        )

    )

    return merged


def generate_persistence_scores():

    try:

        ensure_directory()

        # ==================
        # Sector Scores
        # ==================

        sector_weekly = pd.read_csv(

            AGGREGATED_PATH +
            "sector_weekly_heatmap.csv"

        )

        sector_biweekly = pd.read_csv(

            AGGREGATED_PATH +
            "sector_biweekly_heatmap.csv"

        )

        sector_monthly = pd.read_csv(

            AGGREGATED_PATH +
            "sector_monthly_heatmap.csv"

        )

        sector_scores = (

            generate_entity_scores(

                sector_weekly,
                sector_biweekly,
                sector_monthly,

                "Sector"

            )

        )

        sector_scores.to_csv(

            OUTPUT_PATH +
            "sector_persistence_scores.csv",

            index=False

        )

        logger.info(
            "Sector persistence generated"
        )

        # ==================
        # Theme Scores
        # ==================

        theme_weekly = pd.read_csv(

            AGGREGATED_PATH +
            "theme_weekly_heatmap.csv"

        )

        theme_biweekly = pd.read_csv(

            AGGREGATED_PATH +
            "theme_biweekly_heatmap.csv"

        )

        theme_monthly = pd.read_csv(

            AGGREGATED_PATH +
            "theme_monthly_heatmap.csv"

        )

        theme_scores = (

            generate_entity_scores(

                theme_weekly,
                theme_biweekly,
                theme_monthly,

                "Theme"

            )

        )

        theme_scores.to_csv(

            OUTPUT_PATH +
            "theme_persistence_scores.csv",

            index=False

        )

        logger.info(
            "Theme persistence generated"
        )

    except Exception as e:

        logger.error(
            f"Persistence engine error: {e}"
        )
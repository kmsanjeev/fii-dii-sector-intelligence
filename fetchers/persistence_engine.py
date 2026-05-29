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


def calculate_score(
    weekly_rank,
    biweekly_rank,
    monthly_rank,
    total_items
):

    weekly_score = (

        (
            total_items
            -
            weekly_rank
            +
            1
        )

        /

        total_items

    ) * 30

    biweekly_score = (

        (
            total_items
            -
            biweekly_rank
            +
            1
        )

        /

        total_items

    ) * 30

    monthly_score = (

        (
            total_items
            -
            monthly_rank
            +
            1
        )

        /

        total_items

    ) * 40

    return round(

        weekly_score
        +
        biweekly_score
        +
        monthly_score,

        2

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


def generate_persistence_scores():

    try:

        ensure_directory()

        # ======================
        # Sector Scores
        # ======================

        sector_weekly = pd.read_csv(

            AGGREGATED_PATH
            +
            "sector_weekly_heatmap.csv"

        )

        sector_biweekly = pd.read_csv(

            AGGREGATED_PATH
            +
            "sector_biweekly_heatmap.csv"

        )

        sector_monthly = pd.read_csv(

            AGGREGATED_PATH
            +
            "sector_monthly_heatmap.csv"

        )

        sector_results = []

        total = len(
            sector_monthly
        )

        for sector in sector_monthly[
            "Sector"
        ].unique():

            weekly_rank = int(

                sector_weekly[
                    sector_weekly[
                        "Sector"
                    ] == sector
                ][
                    "Rank"
                ].iloc[0]

            )

            biweekly_rank = int(

                sector_biweekly[
                    sector_biweekly[
                        "Sector"
                    ] == sector
                ][
                    "Rank"
                ].iloc[0]

            )

            monthly_rank = int(

                sector_monthly[
                    sector_monthly[
                        "Sector"
                    ] == sector
                ][
                    "Rank"
                ].iloc[0]

            )

            score = calculate_score(

                weekly_rank,
                biweekly_rank,
                monthly_rank,
                total

            )

            sector_results.append({

                "Sector":
                sector,

                "Persistence_Score":
                score,

                "Status":
                classify_score(
                    score
                )

            })

        sector_df = pd.DataFrame(
            sector_results
        )

        sector_df = (

            sector_df
            .sort_values(
                by="Persistence_Score",
                ascending=False
            )
            .reset_index(
                drop=True
            )

        )

        sector_df.to_csv(

            OUTPUT_PATH
            +
            "sector_persistence_scores.csv",

            index=False

        )

        logger.info(
            "Sector persistence generated"
        )

        # ======================
        # Theme Scores
        # ======================

        theme_weekly = pd.read_csv(

            AGGREGATED_PATH
            +
            "theme_weekly_heatmap.csv"

        )

        theme_biweekly = pd.read_csv(

            AGGREGATED_PATH
            +
            "theme_biweekly_heatmap.csv"

        )

        theme_monthly = pd.read_csv(

            AGGREGATED_PATH
            +
            "theme_monthly_heatmap.csv"

        )

        theme_results = []

        total = len(
            theme_monthly
        )

        for theme in theme_monthly[
            "Theme"
        ].unique():

            weekly_rank = int(

                theme_weekly[
                    theme_weekly[
                        "Theme"
                    ] == theme
                ][
                    "Rank"
                ].iloc[0]

            )

            biweekly_rank = int(

                theme_biweekly[
                    theme_biweekly[
                        "Theme"
                    ] == theme
                ][
                    "Rank"
                ].iloc[0]

            )

            monthly_rank = int(

                theme_monthly[
                    theme_monthly[
                        "Theme"
                    ] == theme
                ][
                    "Rank"
                ].iloc[0]

            )

            score = calculate_score(

                weekly_rank,
                biweekly_rank,
                monthly_rank,
                total

            )

            theme_results.append({

                "Theme":
                theme,

                "Persistence_Score":
                score,

                "Status":
                classify_score(
                    score
                )

            })

        theme_df = pd.DataFrame(
            theme_results
        )

        theme_df = (

            theme_df
            .sort_values(
                by="Persistence_Score",
                ascending=False
            )
            .reset_index(
                drop=True
            )

        )

        theme_df.to_csv(

            OUTPUT_PATH
            +
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
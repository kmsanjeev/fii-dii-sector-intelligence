import pandas as pd

from utils.logger import logger


SECTOR_FILE = (
    "data/intelligence/"
    "sector_persistence_scores.csv"
)

THEME_FILE = (
    "data/intelligence/"
    "theme_persistence_scores.csv"
)


def classify(score):

    if score >= 85:
        return "HIGH CONVICTION"

    if score >= 70:
        return "STRONG"

    if score >= 55:
        return "WATCHLIST"

    return "AVOID"


def build_conviction(
    df,
    name_column
):

    max_monthly = (
        df["Monthly_Return"]
        .max()
    )

    max_biweekly = (
        df["Biweekly_Return"]
        .max()
    )

    max_weekly = (
        df["Weekly_Return"]
        .max()
    )

    df["Monthly_Score"] = (
        df["Monthly_Return"]
        /
        max_monthly
        * 100
    )

    df["Biweekly_Score"] = (
        df["Biweekly_Return"]
        /
        max_biweekly
        * 100
    )

    df["Weekly_Score"] = (
        df["Weekly_Return"]
        /
        max_weekly
        * 100
    )

    df["Conviction_Score"] = (

        df["Persistence_Score"] * 0.40 +

        df["Monthly_Score"] * 0.30 +

        df["Biweekly_Score"] * 0.20 +

        df["Weekly_Score"] * 0.10

    )

    df["Conviction_Score"] = (
        df["Conviction_Score"]
        .round(2)
    )

    df["Conviction"] = (

        df["Conviction_Score"]
        .apply(classify)

    )

    return (

        df[[
            name_column,
            "Conviction_Score",
            "Conviction"
        ]]

        .sort_values(
            by="Conviction_Score",
            ascending=False
        )

    )


def generate_conviction_scores():

    try:

        sector_df = pd.read_csv(
            SECTOR_FILE
        )

        theme_df = pd.read_csv(
            THEME_FILE
        )

        sector_result = (
            build_conviction(
                sector_df,
                "Sector"
            )
        )

        theme_result = (
            build_conviction(
                theme_df,
                "Theme"
            )
        )

        sector_result.to_csv(

            "data/intelligence/"
            "sector_conviction_scores.csv",

            index=False

        )

        theme_result.to_csv(

            "data/intelligence/"
            "theme_conviction_scores.csv",

            index=False

        )

        logger.info(
            "Conviction scores generated"
        )

    except Exception as e:

        logger.error(
            f"Conviction error: {e}"
        )
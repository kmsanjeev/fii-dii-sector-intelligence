import os
import pandas as pd

from utils.logger import logger


OUTPUT_DIR = (
    "data/aggregated/"
)


def ensure_directory():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


def classify_trend(value):

    if value >= 10:
        return "STRONG"

    if value >= 5:
        return "IMPROVING"

    if value >= 0:
        return "NEUTRAL"

    if value >= -5:
        return "WEAKENING"

    return "WEAK"


def calculate_period_return(df, group_col, days):

    latest_date = df["Date"].max()

    start_date = (
        latest_date -
        pd.Timedelta(days=days)
    )

    filtered = df[
        df["Date"] >= start_date
    ]

    results = []

    for name, group in filtered.groupby(group_col):

        group = (
            group
            .sort_values("Date")
        )

        if len(group) < 2:
            continue

        start_close = (
            group.iloc[0]["Close"]
        )

        end_close = (
            group.iloc[-1]["Close"]
        )

        change = round(

            (
                (
                    end_close
                    -
                    start_close
                )
                /
                start_close
            )
            * 100,

            2

        )

        results.append({

            group_col:
            name,

            "Return_%":
            change,

            "Trend":
            classify_trend(
                change
            )

        })

    result_df = pd.DataFrame(
        results
    )

    if not result_df.empty:

        result_df = (

            result_df
            .sort_values(
                by="Return_%",
                ascending=False
            )
            .reset_index(
                drop=True
            )

        )

        result_df["Rank"] = (
            result_df.index + 1
        )

    return result_df


def save_heatmap(df, filename):

    file_path = (
        OUTPUT_DIR
        +
        filename
    )

    df.to_csv(
        file_path,
        index=False
    )

    logger.info(
        f"Saved: {filename}"
    )


def generate_sector_heatmaps(
    sector_history
):

    try:

        ensure_directory()

        sector_history[
            "Date"
        ] = pd.to_datetime(

            sector_history["Date"]

        )

        weekly = (
            calculate_period_return(
                sector_history,
                "Sector",
                7
            )
        )

        biweekly = (
            calculate_period_return(
                sector_history,
                "Sector",
                14
            )
        )

        monthly = (
            calculate_period_return(
                sector_history,
                "Sector",
                30
            )
        )

        save_heatmap(

            weekly,

            "sector_weekly_heatmap.csv"

        )

        save_heatmap(

            biweekly,

            "sector_biweekly_heatmap.csv"

        )

        save_heatmap(

            monthly,

            "sector_monthly_heatmap.csv"

        )

        logger.info(
            "Sector heatmaps generated"
        )

    except Exception as e:

        logger.error(
            f"Sector aggregation error: {e}"
        )


def generate_theme_heatmaps(
    theme_history
):

    try:

        ensure_directory()

        theme_history[
            "Date"
        ] = pd.to_datetime(

            theme_history["Date"]

        )

        weekly = (
            calculate_period_return(
                theme_history,
                "Theme",
                7
            )
        )

        biweekly = (
            calculate_period_return(
                theme_history,
                "Theme",
                14
            )
        )

        monthly = (
            calculate_period_return(
                theme_history,
                "Theme",
                30
            )
        )

        save_heatmap(

            weekly,

            "theme_weekly_heatmap.csv"

        )

        save_heatmap(

            biweekly,

            "theme_biweekly_heatmap.csv"

        )

        save_heatmap(

            monthly,

            "theme_monthly_heatmap.csv"

        )

        logger.info(
            "Theme heatmaps generated"
        )

    except Exception as e:

        logger.error(
            f"Theme aggregation error: {e}"
        )
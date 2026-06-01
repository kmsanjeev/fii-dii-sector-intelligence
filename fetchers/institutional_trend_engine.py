import os
import pandas as pd

from utils.logger import logger


INPUT_FILE = (
    "data/historical/institutional/"
    "institutional_positioning_history.csv"
)

OUTPUT_FILE = (
    "data/intelligence/"
    "institutional_trend.csv"
)


def generate_institutional_trend():

    try:

        if not os.path.exists(
            INPUT_FILE
        ):

            logger.warning(
                "Institutional history not found"
            )

            return

        df = pd.read_csv(
            INPUT_FILE
        )

        if df.empty:

            logger.warning(
                "Institutional history empty"
            )

            return

        df = df.sort_values(
            by="Date"
        ).reset_index(
            drop=True
        )

        # =====================
        # Trend Windows
        # =====================

        df["Trend_Daily"] = (

            df[
                "Institutional_Score"
            ]

            -

            df[
                "Institutional_Score"
            ].shift(1)

        )

        df["Trend_Weekly"] = (

            df[
                "Institutional_Score"
            ]

            -

            df[
                "Institutional_Score"
            ]
            .rolling(5)
            .mean()

        )

        df["Trend_BiWeekly"] = (

            df[
                "Institutional_Score"
            ]

            -

            df[
                "Institutional_Score"
            ]
            .rolling(10)
            .mean()

        )

        df["Trend_Monthly"] = (

            df[
                "Institutional_Score"
            ]

            -

            df[
                "Institutional_Score"
            ]
            .rolling(21)
            .mean()

        )

        df["Trend_Quarterly"] = (

            df[
                "Institutional_Score"
            ]

            -

            df[
                "Institutional_Score"
            ]
            .rolling(63)
            .mean()

        )

        df["Trend_HalfYearly"] = (

            df[
                "Institutional_Score"
            ]

            -

            df[
                "Institutional_Score"
            ]
            .rolling(126)
            .mean()

        )

        df["Trend_Yearly"] = (

            df[
                "Institutional_Score"
            ]

            -

            df[
                "Institutional_Score"
            ]
            .rolling(252)
            .mean()

        )

        # =====================
        # Fill Initial NaNs
        # =====================

        trend_cols = [

            "Trend_Daily",
            "Trend_Weekly",
            "Trend_BiWeekly",
            "Trend_Monthly",
            "Trend_Quarterly",
            "Trend_HalfYearly",
            "Trend_Yearly"

        ]

        df[
            trend_cols
        ] = df[
            trend_cols
        ].fillna(0)

        # =====================
        # Trend Strength
        # =====================

        df["Trend_Strength"] = (

            df["Trend_Daily"]      * 0.10 +

            df["Trend_Weekly"]     * 0.15 +

            df["Trend_BiWeekly"]   * 0.15 +

            df["Trend_Monthly"]    * 0.25 +

            df["Trend_Quarterly"]  * 0.15 +

            df["Trend_HalfYearly"] * 0.10 +

            df["Trend_Yearly"]     * 0.10

        )

        # =====================
        # Trend Acceleration
        # =====================

        df["Trend_Acceleration"] = (

            df[
                "Trend_Strength"
            ]

            -

            df[
                "Trend_Strength"
            ].shift(1)

        )

        df[
            "Trend_Acceleration"
        ] = df[
            "Trend_Acceleration"
        ].fillna(0)

        # =====================
        # Trend State
        # =====================

        trend_states = []

        for _, row in df.iterrows():

            daily = row[
                "Trend_Daily"
            ]

            weekly = row[
                "Trend_Weekly"
            ]

            biweekly = row[
                "Trend_BiWeekly"
            ]

            monthly = row[
                "Trend_Monthly"
            ]

            # -----------------

            if (

                daily > 0

                and

                weekly < 0

                and

                biweekly < 0

                and

                monthly < 0

            ):

                state = (
                    "EARLY_ACCUMULATION"
                )

            elif (

                daily > 0

                and

                weekly > 0

                and

                biweekly > 0

                and

                monthly <= 0

            ):

                state = (
                    "ACCUMULATION"
                )

            elif (

                daily > 0

                and

                weekly > 0

                and

                biweekly > 0

                and

                monthly > 0

            ):

                state = (
                    "STRONG_ACCUMULATION"
                )

            elif (

                daily < 0

                and

                weekly > 0

                and

                biweekly > 0

                and

                monthly > 0

            ):

                state = (
                    "EARLY_DISTRIBUTION"
                )

            elif (

                daily < 0

                and

                weekly < 0

                and

                biweekly < 0

                and

                monthly >= 0

            ):

                state = (
                    "DISTRIBUTION"
                )

            elif (

                daily < 0

                and

                weekly < 0

                and

                biweekly < 0

                and

                monthly < 0

            ):

                state = (
                    "STRONG_DISTRIBUTION"
                )

            else:

                state = (
                    "NEUTRAL"
                )

            trend_states.append(
                state
            )

        df["Trend_State"] = (
            trend_states
        )

        # =====================
        # Output
        # =====================

        output_df = df[[

            "Date",

            "Institutional_Score",

            "Trend_Daily",
            "Trend_Weekly",
            "Trend_BiWeekly",
            "Trend_Monthly",
            "Trend_Quarterly",
            "Trend_HalfYearly",
            "Trend_Yearly",

            "Trend_State",

            "Trend_Strength",

            "Trend_Acceleration"

        ]]

        os.makedirs(

            "data/intelligence",

            exist_ok=True

        )

        output_df.to_csv(

            OUTPUT_FILE,

            index=False

        )

        logger.info(
            "Institutional trend generated"
        )

    except Exception as e:

        logger.error(
            f"Institutional Trend Error: "
            f"{e}"
        )
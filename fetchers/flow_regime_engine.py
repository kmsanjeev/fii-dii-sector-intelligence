import os
import pandas as pd

from utils.logger import logger


INPUT_FILE = (
    "data/historical/fii_dii/"
    "historical_fii_dii.csv"
)

OUTPUT_DIR = (
    "data/intelligence/"
)

OUTPUT_FILE = (
    OUTPUT_DIR +
    "institutional_flow_regime.csv"
)


def ensure_directory():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


def classify_regime(score):

    if score >= 3000:
        return "ACCUMULATION"

    if score >= 1000:
        return "BUILDUP"

    if score >= -1000:
        return "SIDEWAYS"

    if score >= -3000:
        return "DISTRIBUTION"

    return "LIQUIDATION"


def generate_flow_regime():

    try:

        ensure_directory()

        df = pd.read_csv(
            INPUT_FILE
        )

        df["Date"] = pd.to_datetime(
            df["Date"]
        )

        flow_column = (
            "Combined_Net_Flow"
        )

        if flow_column not in df.columns:

            logger.error(
                "Combined_Net_Flow missing"
            )

            return pd.DataFrame()

        df = (
            df
            .sort_values("Date")
            .reset_index(
                drop=True
            )
        )

        df["Flow_5D"] = (

            df[
                flow_column
            ]

            .rolling(5)
            .mean()

        )

        df["Flow_10D"] = (

            df[
                flow_column
            ]

            .rolling(10)
            .mean()

        )

        df["Flow_20D"] = (

            df[
                flow_column
            ]

            .rolling(20)
            .mean()

        )

        df["Flow_Score"] = (

            df["Flow_5D"] * 0.30

            +

            df["Flow_10D"] * 0.30

            +

            df["Flow_20D"] * 0.40

        )

        df["Regime"] = (

            df["Flow_Score"]
            .apply(
                classify_regime
            )

        )

        output = df[[

            "Date",

            "Flow_5D",
            "Flow_10D",
            "Flow_20D",

            "Flow_Score",

            "Regime"

        ]]

        output.to_csv(

            OUTPUT_FILE,

            index=False

        )

        latest = output.iloc[-1]

        logger.info(

            f"Flow Regime: "
            f"{latest['Regime']}"

        )

        logger.info(
            "Institutional flow "
            "regime generated"
        )

        return output

    except Exception as e:

        logger.error(
            f"Flow regime error: {e}"
        )

        return pd.DataFrame()
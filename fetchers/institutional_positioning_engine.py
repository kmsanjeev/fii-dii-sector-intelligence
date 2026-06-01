import os
import pandas as pd

from datetime import datetime
from datetime import timedelta

from nselib import derivatives

from utils.logger import logger


SAVE_FILE = (
    "data/intelligence/"
    "institutional_positioning.csv"
)


def get_latest_trading_day():

    trade_date = datetime.now()

    while trade_date.weekday() >= 5:

        trade_date = (
            trade_date -
            timedelta(days=1)
        )

    return trade_date.strftime(
        "%d-%m-%Y"
    )


def normalize_dataframe(df):

    df.columns = (

        df.columns
        .astype(str)
        .str.strip()

    )

    # =====================
    # Legacy NSE Schema Fix
    # =====================

    if (

        "Client Type"
        not in df.columns

        and

        "Client"
        in df.columns

    ):

        df = df.rename(

            columns={

                "Client":
                "Client Type"

            }

        )

    # =====================
    # Remove commas
    # =====================

    for col in df.columns:

        df[col] = (

            df[col]
            .astype(str)
            .str.replace(
                ",",
                "",
                regex=False
            )

        )

    return df


def _safe_float(value):

    try:

        return float(

            str(value)
            .replace(",", "")
            .strip()

        )

    except:

        return 0.0


def _net_position(row):

    row.index = (

        row.index
        .astype(str)
        .str.strip()

    )

    return (

        _safe_float(
            row["Future Index Long"]
        )

        +

        _safe_float(
            row["Future Stock Long"]
        )

        -

        _safe_float(
            row["Future Index Short"]
        )

        -

        _safe_float(
            row["Future Stock Short"]
        )

    )


def calculate_regime(
    institutional_score
):

    if institutional_score > 0:

        return "ACCUMULATION"

    elif institutional_score < 0:

        return "DISTRIBUTION"

    return "NEUTRAL"


def calculate_score(

    fii_oi_score,
    dii_oi_score,
    pro_oi_score,

    fii_volume_score,
    dii_volume_score,
    pro_volume_score,

    fii_derivatives_score

):

    return round(

        (fii_oi_score * 0.35)

        +

        (dii_oi_score * 0.20)

        +

        (pro_oi_score * 0.15)

        +

        (fii_volume_score * 0.15)

        +

        (dii_volume_score * 0.05)

        +

        (pro_volume_score * 0.05)

        +

        (fii_derivatives_score * 0.05),

        2

    )


def generate_institutional_positioning():

    try:

        trade_date = (
            get_latest_trading_day()
        )

        oi_df = (
            derivatives
            .participant_wise_open_interest(
                trade_date=trade_date
            )
        )

        volume_df = (
            derivatives
            .participant_wise_trading_volume(
                trade_date=trade_date
            )
        )

        fii_derivatives = (
            derivatives
            .fii_derivatives_statistics(
                trade_date=trade_date
            )
        )

        oi_df = normalize_dataframe(
            oi_df
        )

        volume_df = normalize_dataframe(
            volume_df
        )

        fii_oi = oi_df[
            oi_df["Client Type"] == "FII"
        ].iloc[0]

        dii_oi = oi_df[
            oi_df["Client Type"] == "DII"
        ].iloc[0]

        pro_oi = oi_df[
            oi_df["Client Type"] == "Pro"
        ].iloc[0]

        client_oi = oi_df[
            oi_df["Client Type"] == "Client"
        ].iloc[0]

        fii_vol = volume_df[
            volume_df["Client Type"] == "FII"
        ].iloc[0]

        dii_vol = volume_df[
            volume_df["Client Type"] == "DII"
        ].iloc[0]

        pro_vol = volume_df[
            volume_df["Client Type"] == "Pro"
        ].iloc[0]

        client_vol = volume_df[
            volume_df["Client Type"] == "Client"
        ].iloc[0]

        fii_oi_score = _net_position(
            fii_oi
        )

        dii_oi_score = _net_position(
            dii_oi
        )

        pro_oi_score = _net_position(
            pro_oi
        )

        client_oi_score = _net_position(
            client_oi
        )

        fii_volume_score = _net_position(
            fii_vol
        )

        dii_volume_score = _net_position(
            dii_vol
        )

        pro_volume_score = _net_position(
            pro_vol
        )

        client_volume_score = _net_position(
            client_vol
        )

        futures_rows = fii_derivatives[
            fii_derivatives[
                "fii_derivatives"
            ].str.contains(
                "FUTURES",
                na=False
            )
        ]

        fii_derivatives_score = (

            futures_rows[
                "buy_contracts"
            ].sum()

            -

            futures_rows[
                "sell_contracts"
            ].sum()

        )

        institutional_score = (
            calculate_score(

                fii_oi_score,
                dii_oi_score,
                pro_oi_score,

                fii_volume_score,
                dii_volume_score,
                pro_volume_score,

                fii_derivatives_score

            )
        )

        regime = calculate_regime(
            institutional_score
        )

        result = pd.DataFrame([{

            "Date":
            datetime.now()
            .strftime("%Y-%m-%d"),

            "FII_OI_Score":
            fii_oi_score,

            "DII_OI_Score":
            dii_oi_score,

            "PRO_OI_Score":
            pro_oi_score,

            "CLIENT_OI_Score":
            client_oi_score,

            "FII_Volume_Score":
            fii_volume_score,

            "DII_Volume_Score":
            dii_volume_score,

            "PRO_Volume_Score":
            pro_volume_score,

            "CLIENT_Volume_Score":
            client_volume_score,

            "FII_Derivatives_Score":
            fii_derivatives_score,

            "Institutional_Score":
            institutional_score,

            "Regime":
            regime

        }])

        os.makedirs(
            "data/intelligence",
            exist_ok=True
        )

        result.to_csv(
            SAVE_FILE,
            index=False
        )

        logger.info(
            f"Institutional Regime: "
            f"{regime}"
        )

        return result

    except Exception as e:

        logger.error(
            f"Institutional positioning error: {e}"
        )

        return pd.DataFrame()
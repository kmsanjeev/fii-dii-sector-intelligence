import os
import pandas as pd

from datetime import datetime
from nselib import derivatives

from datetime import datetime
from datetime import timedelta

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

from utils.logger import logger


SAVE_FILE = (
    "data/intelligence/"
    "institutional_positioning.csv"
)


def _net_position(row):

    row.index = (
        row.index
        .astype(str)
        .str.strip()
    )

    return (

        float(row["Future Index Long"])

        +

        float(row["Future Stock Long"])

        -

        float(row["Future Index Short"])

        -

        float(row["Future Stock Short"])

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

        oi_df.columns = (
            oi_df.columns
            .astype(str)
            .str.strip()
        )

        volume_df.columns = (
            volume_df.columns
            .astype(str)
            .str.strip()
        )

        fii_derivatives = (
            derivatives
            .fii_derivatives_statistics(
                trade_date=trade_date
            )
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

        institutional_score = round(

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

        if institutional_score > 0:

            regime = (
                "ACCUMULATION"
            )

        elif institutional_score < 0:

            regime = (
                "DISTRIBUTION"
            )

        else:

            regime = (
                "NEUTRAL"
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
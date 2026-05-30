import pandas as pd

from datetime import datetime
from datetime import timedelta

from nselib import derivatives

from utils.logger import logger

from storage.institutional_history_manager import (
    append_historical_data,
    get_existing_dates
)

from fetchers.institutional_positioning_engine import (
    calculate_score,
    calculate_regime,
    _net_position
)


BATCH_SIZE = 50


def get_missing_dates():

    existing_dates = (
        get_existing_dates()
    )

    end_date = datetime.now()

    start_date = datetime(
        2016,
        1,
        1
    )

    missing = []

    current = start_date

    while current <= end_date:

        if current.weekday() < 5:

            date_str = current.strftime(
                "%Y-%m-%d"
            )

            if date_str not in existing_dates:

                missing.append(
                    current
                )

        current += timedelta(
            days=1
        )

    return missing[
        :BATCH_SIZE
    ]


def run_institutional_backfill():

    try:

        logger.info(
            "Institutional Backfill Started"
        )

        missing_dates = (
            get_missing_dates()
        )

        if not missing_dates:

            logger.info(
                "No missing institutional dates"
            )

            return

        collected = []

        for trade_date in missing_dates:

            try:

                nse_date = (
                    trade_date.strftime(
                        "%d-%m-%Y"
                    )
                )

                oi_df = (
                    derivatives
                    .participant_wise_open_interest(
                        trade_date=nse_date
                    )
                )

                volume_df = (
                    derivatives
                    .participant_wise_trading_volume(
                        trade_date=nse_date
                    )
                )

                fii_derivatives = (
                    derivatives
                    .fii_derivatives_statistics(
                        trade_date=nse_date
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

                fii_oi_score = (
                    _net_position(
                        fii_oi
                    )
                )

                dii_oi_score = (
                    _net_position(
                        dii_oi
                    )
                )

                pro_oi_score = (
                    _net_position(
                        pro_oi
                    )
                )

                client_oi_score = (
                    _net_position(
                        client_oi
                    )
                )

                fii_volume_score = (
                    _net_position(
                        fii_vol
                    )
                )

                dii_volume_score = (
                    _net_position(
                        dii_vol
                    )
                )

                pro_volume_score = (
                    _net_position(
                        pro_vol
                    )
                )

                client_volume_score = (
                    _net_position(
                        client_vol
                    )
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

                regime = (
                    calculate_regime(
                        institutional_score
                    )
                )

                collected.append({

                    "Date":
                    trade_date.strftime(
                        "%Y-%m-%d"
                    ),

                    "FII_OI_Net":
                    fii_oi_score,

                    "DII_OI_Net":
                    dii_oi_score,

                    "PRO_OI_Net":
                    pro_oi_score,

                    "CLIENT_OI_Net":
                    client_oi_score,

                    "FII_Volume_Net":
                    fii_volume_score,

                    "DII_Volume_Net":
                    dii_volume_score,

                    "PRO_Volume_Net":
                    pro_volume_score,

                    "CLIENT_Volume_Net":
                    client_volume_score,

                    "FII_Derivatives_Net":
                    fii_derivatives_score,

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

                })

            except Exception:

                continue

        if collected:

            append_historical_data(

                pd.DataFrame(
                    collected
                )

            )

        logger.info(
            "Institutional Backfill Completed"
        )

    except Exception as e:

        logger.error(

            f"Institutional Backfill Error: "
            f"{e}"

        )
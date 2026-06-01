# research/test_missing_dates.py

from nselib import derivatives

dates = [

    "13-06-2018",
    "12-12-2019"

]

for d in dates:

    print("\n")
    print("=" * 50)
    print(d)

    try:

        oi = derivatives.participant_wise_open_interest(
            trade_date=d
        )

        print(
            oi.head()
        )

    except Exception as e:

        print(
            "OI ERROR:",
            e
        )

    try:

        vol = derivatives.participant_wise_trading_volume(
            trade_date=d
        )

        print(
            vol.head()
        )

    except Exception as e:

        print(
            "VOL ERROR:",
            e
        )

    try:

        fii = derivatives.fii_derivatives_statistics(
            trade_date=d
        )

        print(
            fii.head()
        )

    except Exception as e:

        print(
            "FII ERROR:",
            e
        )
from nselib import derivatives

dates = [
    "01-08-2024",
    "01-08-2023",
    "01-08-2022",
    "01-08-2021",
    "01-08-2020",
    "01-08-2019",
    "01-08-2018",
    "01-08-2017",
    "01-08-2016",
    "01-08-2015",
    "01-08-2014",
    "01-08-2013",
    "01-08-2012",
    "01-08-2011",
    "01-08-2010"
]

for d in dates:
    try:
        df = derivatives.fii_derivatives_statistics(
            trade_date=d
        )

        print(
            d,
            "SUCCESS",
            len(df)
        )

    except Exception as e:
        print(
            d,
            "FAILED",
            str(e)
        )
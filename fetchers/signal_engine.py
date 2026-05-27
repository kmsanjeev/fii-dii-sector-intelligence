import pandas as pd


def generate_signals(

    date,
    gainers,
    losers,
    strongest_sector,
    weakest_sector,
    combined_flow

):

    rows=[]

    if not gainers.empty:

        for _,r in gainers.iterrows():

            signal=(

                "BUY"

                if combined_flow > 0

                else

                "WATCH"

            )

            rows.append({

                "Date":
                date,

                "Signal":
                signal,

                "Stock":
                r["symbol"],

                "Sector":
                strongest_sector,

                "Strength":
                "Strong"

            })

    if not losers.empty:

        for _,r in losers.iterrows():

            if combined_flow < 0:

                rows.append({

                    "Date":
                    date,

                    "Signal":
                    "SELL",

                    "Stock":
                    r["symbol"],

                    "Sector":
                    weakest_sector,

                    "Strength":
                    "Weak"

                })

    return pd.DataFrame(
        rows
    )
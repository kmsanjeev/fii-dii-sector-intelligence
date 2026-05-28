import pandas as pd


def calculate_score(

    signal,
    combined_flow,
    sector_change,
    stock_change

):

    score = 50

    # ====================
    # Flow Bias
    # ====================

    if combined_flow > 0:

        score += 20

    else:

        score -= 20

    # ====================
    # Sector Strength
    # ====================

    if sector_change > 1:

        score += 15

    elif sector_change < -1:

        score -= 15

    # ====================
    # Stock Momentum
    # ====================

    if stock_change > 2:

        score += 15

    elif stock_change < -2:

        score -= 15

    # ====================
    # Signal Bias
    # ====================

    if signal == "BUY":

        score += 10

    elif signal == "SELL":

        score -= 10

    # Clamp

    score = max(
        0,
        min(100, score)
    )

    return round(score, 2)


def generate_signals(

    date,
    gainers,
    losers,
    strongest_sector,
    weakest_sector,
    strongest_sector_change,
    weakest_sector_change,
    combined_flow

):

    rows = []

    # ====================
    # BUY / WATCH
    # ====================

    if not gainers.empty:

        for _, r in gainers.iterrows():

            stock_change = round(
                float(
                    r["percentChange"]
                ),
                2
            )

            signal = (

                "BUY"

                if combined_flow > 0

                else

                "WATCH"

            )

            score = calculate_score(

                signal,
                combined_flow,
                strongest_sector_change,
                stock_change

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
                "Strong",

                "Score":
                score,

                "Stock_Change":
                stock_change,

                "Sector_Change":
                strongest_sector_change,

                "Flow_Bias":
                combined_flow

            })

    # ====================
    # SELL
    # ====================

    if not losers.empty:

        for _, r in losers.iterrows():

            stock_change = round(
                float(
                    r["percentChange"]
                ),
                2
            )

            signal = "SELL"

            score = calculate_score(

                signal,
                combined_flow,
                weakest_sector_change,
                stock_change

            )

            rows.append({

                "Date":
                date,

                "Signal":
                signal,

                "Stock":
                r["symbol"],

                "Sector":
                weakest_sector,

                "Strength":
                "Weak",

                "Score":
                score,

                "Stock_Change":
                stock_change,

                "Sector_Change":
                weakest_sector_change,

                "Flow_Bias":
                combined_flow

            })

    df = pd.DataFrame(
        rows
    )

    if not df.empty:

        df = df.sort_values(
            by="Score",
            ascending=False
        )

    return df
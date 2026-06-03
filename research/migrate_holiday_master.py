import pandas as pd

MASTER_FILE = (
    "data/reference/"
    "nse_holidays_master.csv"
)

TARGET_FILE = (
    "data/reference/"
    "nse_holidays.csv"
)

df = pd.read_csv(
    MASTER_FILE
)

df = df.rename(
    columns={
        "DATE": "Date",
        "YEAR": "Year",
        "HOLIDAY": "Holiday"
    }
)

df["Date"] = pd.to_datetime(
    df["Date"],
    format="%d-%m-%Y"
)

df["Date"] = (
    df["Date"]
    .dt.strftime("%Y-%m-%d")
)

df = (
    df
    .sort_values("Date")
    .drop_duplicates(
        subset=["Date"]
    )
)

df.to_csv(
    TARGET_FILE,
    index=False
)

print(
    f"Saved {len(df)} holidays"
)
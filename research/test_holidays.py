from nselib import trading_holiday_calendar

df = trading_holiday_calendar()

print(df.head(20))
print()
print(df.columns.tolist())
print()
print(df["tradingDate"].min())
print(df["tradingDate"].max())
print()
print(df["Product"].unique())
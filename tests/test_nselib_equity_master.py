from nselib import capital_market

print("Fetching...")

try:
    data = capital_market.equity_list()
    print(type(data))
    print(data.head())
    print("Rows:", len(data))
except Exception as e:
    print("ERROR:", e)

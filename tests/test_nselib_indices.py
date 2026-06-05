from nselib import capital_market

print("Testing index_data()")

try:
    data = capital_market.index_data()

    print(type(data))

    if hasattr(data, "head"):
        print(data.head())

    print(data)

except Exception as e:
    print("ERROR:", e)
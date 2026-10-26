
from vnstock import Market

symbol = "FPT"
start_date = "2024-10-23"
end_date = "2026-10-23"

stock = Market().equity(symbol)

df = stock.ohlcv(
    start=start_date,
    end=end_date,
    interval="1D",
)

print("Rows:", len(df))
print("Columns:", df.columns.tolist())
print("Source metadata:", df.attrs)
print(df.head(3))
print(df.tail(3))

if not df.empty:
    print("First date:", df["time"].min())
    print("Last date:", df["time"].max())

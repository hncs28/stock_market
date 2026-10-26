
from datetime import date
from pathlib import Path

import pandas as pd
from vnstock import Market


SYMBOLS = ["FPT", "VNM", "HPG"]

START_DATE = "2024-10-23"
END_DATE = "2026-10-23"

RAW_DIR = Path("data/raw")


def extract_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch daily historical stock data from the market data source."""

    print(f"[INFO] Fetching {symbol}...")

    stock = Market().equity(symbol)

    df = stock.ohlcv(
        start=start_date,
        end=end_date,
        interval="1D",
    )

    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol}")

    # Attach the stock symbol so the data can be identified later.
    df.insert(0, "symbol", symbol)

    print(f"[INFO] {symbol}: received {len(df)} rows")
    print(
        f"{symbol}: rows={len(df)}, "
        f"first={df['time'].min()}, "
        f"last={df['time'].max()}"
    )

    return df


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    successful = []
    failed = []

    for symbol in SYMBOLS:
        try:
            df = extract_stock_data(
                symbol=symbol,
                start_date=START_DATE,
                end_date=END_DATE,
            )

            output_file = (
                RAW_DIR
                / f"{symbol}_{START_DATE}_{END_DATE}.csv"
            )

            df.to_csv(
                output_file,
                index=False,
                encoding="utf-8-sig",
            )

            print(f"[INFO] Saved: {output_file}")
            successful.append(symbol)

        except Exception as exc:
            print(f"[ERROR] {symbol}: {exc}")
            failed.append(symbol)

    print("\n========== EXTRACT SUMMARY ==========")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed:
        raise RuntimeError(
            f"Extraction failed for: {', '.join(failed)}"
        )



if __name__ == "__main__":
    main()
    

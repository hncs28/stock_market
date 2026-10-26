import pandas as pd


def transform_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw stock data into clean format ready for validation and loading."""
    df = df.copy()

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()

    # Convert time/timestamp column to trading_date (YYYY-MM-DD)
    if "time" in df.columns:
        df["trading_date"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d")
        df = df.drop(columns=["time"])
    elif "trading_date" in df.columns:
        df["trading_date"] = pd.to_datetime(df["trading_date"]).dt.strftime("%Y-%m-%d")

    # Cast numeric columns
    price_cols = ["open", "high", "low", "close"]
    for col in price_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype("Int64")

    # Reorder columns if all expected columns exist
    expected_cols = [
        "symbol",
        "trading_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    present_cols = [c for c in expected_cols if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in expected_cols]
    df = df[present_cols + remaining_cols]

    if "symbol" in df.columns and "trading_date" in df.columns:
        df = df.sort_values(by=["symbol", "trading_date"]).reset_index(drop=True)

    return df

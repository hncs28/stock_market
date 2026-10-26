
import pandas as pd


def validate_stock_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split rows into valid and rejected records."""

    df = df.copy()

    required_values = [
        "symbol",
        "trading_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    # One list of reasons per row.
    reasons = pd.Series("", index=df.index, dtype="string")

    def add_reason(mask: pd.Series, message: str) -> None:
        nonlocal reasons
        reasons.loc[mask] = reasons.loc[mask].map(
            lambda old: f"{old}; {message}" if old else message
        )

    # 1. Required values must not be missing.
    missing_mask = df[required_values].isna().any(axis=1)
    add_reason(missing_mask, "missing_required_value")

    # 2. Numeric fields must be finite and non-negative.
    price_columns = ["open", "high", "low", "close"]

    for column in price_columns:
        negative = df[column].lt(0).fillna(False)
        add_reason(negative, f"negative_{column}")

    negative_volume = df["volume"].lt(0).fillna(False)
    add_reason(negative_volume, "negative_volume")

    numeric_columns = price_columns + ["volume"]

    for column in numeric_columns:
        finite_mask = pd.Series(
            True,
            index=df.index,
        )
        finite_mask.loc[df[column].notna()] = (
            df.loc[df[column].notna(), column]
            .map(lambda value: __import__("math").isfinite(float(value)))
        )
        add_reason(~finite_mask, f"non_finite_{column}")

    # 3. OHLC consistency.
    bad_high_low = (
        df["high"].lt(df["low"]).fillna(False)
    )
    add_reason(bad_high_low, "high_below_low")

    bad_high_open = (
        df["high"].lt(df["open"]).fillna(False)
    )
    add_reason(bad_high_open, "high_below_open")

    bad_high_close = (
        df["high"].lt(df["close"]).fillna(False)
    )
    add_reason(bad_high_close, "high_below_close")

    bad_low_open = (
        df["low"].gt(df["open"]).fillna(False)
    )
    add_reason(bad_low_open, "low_above_open")

    bad_low_close = (
        df["low"].gt(df["close"]).fillna(False)
    )
    add_reason(bad_low_close, "low_above_close")

    # 4. A duplicate business key makes the entire key group ambiguous.
    duplicate_key = df.duplicated(
        subset=["symbol", "trading_date"],
        keep=False,
    )
    add_reason(duplicate_key, "duplicate_symbol_date")

    # 5. Split valid and rejected rows.
    valid_mask = reasons.eq("")

    valid_df = df.loc[valid_mask].copy()
    rejected_df = df.loc[~valid_mask].copy()
    rejected_df["rejection_reason"] = reasons.loc[~valid_mask]

    return valid_df, rejected_df

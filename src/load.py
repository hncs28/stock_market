
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ.get('DB_HOST', 'localhost')}:"
    f"{os.environ.get('DB_PORT', '5432')}/"
    f"{os.environ['DB_NAME']}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


UPSERT_SQL = text("""
    INSERT INTO stock_prices (
        symbol,
        trading_date,
        open,
        high,
        low,
        close,
        volume,
        source
    )
    VALUES (
        :symbol,
        :trading_date,
        :open,
        :high,
        :low,
        :close,
        :volume,
        :source
    )
    ON CONFLICT (symbol, trading_date)
    DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume,
        source = EXCLUDED.source,
        loaded_at = CURRENT_TIMESTAMP
""")


def load_stock_data(csv_file: Path) -> int:
    df = pd.read_csv(csv_file)

    if df.empty:
        print(f"[INFO] Empty file, skipped: {csv_file}")
        return 0

    # This stage expects already validated data.
    required = [
        "symbol",
        "trading_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    missing = set(required) - set(df.columns)

    if missing:
        raise ValueError(
            f"{csv_file}: missing columns {sorted(missing)}"
        )

    df["trading_date"] = pd.to_datetime(
        df["trading_date"],
        errors="raise",
    ).dt.date

    df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
    df["source"] = "vci"

    records = df[
        required + ["source"]
    ].to_dict(orient="records")

    # A transaction ensures the batch is committed as a unit.
    with engine.begin() as connection:
        connection.execute(UPSERT_SQL, records)

    print(f"[INFO] Loaded {len(records)} rows from {csv_file}")
    return len(records)


def main() -> None:
    clean_dir = Path("data/clean")

    if not clean_dir.exists():
        raise FileNotFoundError(
            "data/clean does not exist. Run Transform first."
        )

    total = 0

    for csv_file in sorted(clean_dir.glob("*.csv")):
        total += load_stock_data(csv_file)

    print(f"[INFO] Total input rows processed: {total}")


if __name__ == "__main__":
    main()

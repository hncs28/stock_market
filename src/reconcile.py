
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


def main() -> None:
    clean_dir = Path("data/clean")
    frames = []

    for file in sorted(clean_dir.glob("*.csv")):
        df = pd.read_csv(file)
        frames.append(df)

    if not frames:
        raise FileNotFoundError("No clean CSV files found")

    source_df = pd.concat(frames, ignore_index=True)

    # Count the expected unique business keys in clean data.
    source_df["trading_date"] = pd.to_datetime(
        source_df["trading_date"],
        errors="raise",
    ).dt.date

    source_keys = source_df[
        ["symbol", "trading_date"]
    ].drop_duplicates()

    db_df = pd.read_sql(
        text("""
            SELECT symbol, trading_date
            FROM stock_prices
        """),
        engine,
    )

    db_df["trading_date"] = pd.to_datetime(
        db_df["trading_date"],
        errors="raise",
    ).dt.date

    source_keys = source_keys.assign(
        symbol=source_keys["symbol"].str.upper().str.strip()
    )
    db_df["symbol"] = db_df["symbol"].str.upper().str.strip()

    comparison = source_keys.merge(
        db_df,
        on=["symbol", "trading_date"],
        how="left",
        indicator=True,
    )

    missing_in_db = comparison[
        comparison["_merge"] == "left_only"
    ]

    print("Clean CSV rows:", len(source_df))
    print("Unique source keys:", len(source_keys))
    print("Database rows:", len(db_df))
    print("Source keys missing in database:", len(missing_in_db))

    if not missing_in_db.empty:
        print(missing_in_db.head(20).to_string(index=False))
        raise RuntimeError("Reconciliation failed")


if __name__ == "__main__":
    main()

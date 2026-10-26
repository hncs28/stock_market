
from pathlib import Path

import pandas as pd

from transform import transform_stock_data
from validate import validate_stock_data


RAW_DIR = Path("data/raw")
CLEAN_DIR = Path("data/clean")
REJECTED_DIR = Path("data/rejected")


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    for raw_file in RAW_DIR.glob("*.csv"):
        print(f"\nProcessing {raw_file.name}")

        raw_df = pd.read_csv(raw_file)

        transformed_df = transform_stock_data(raw_df)
        valid_df, rejected_df = validate_stock_data(transformed_df)

        valid_file = CLEAN_DIR / raw_file.name
        rejected_file = REJECTED_DIR / raw_file.name

        valid_df.to_csv(valid_file, index=False)
        rejected_df.to_csv(rejected_file, index=False)

        print(f"Input rows: {len(raw_df)}")
        print(f"Valid rows: {len(valid_df)}")
        print(f"Rejected rows: {len(rejected_df)}")


if __name__ == "__main__":
    main()

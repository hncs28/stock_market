
from pathlib import Path

import pandas as pd

for file in Path("data/raw").glob("*.csv"):
    df = pd.read_csv(file)

    print(f"\nFile: {file.name}")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print(df.head(5).to_string(index=False))
    print("Missing values:")
    print(df.isna().sum())

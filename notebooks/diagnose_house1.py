
from pathlib import Path
import pandas as pd
import numpy as np

root = Path(__file__).resolve().parent.parent
data_dir = root / "data" / "raw" / "house1"

files = [
    data_dir / "RAW_House1_Part1.csv",
    data_dir / "RAW_House1_Part2.csv",
]

time_col = "Time"
power_cols = ["Aggregate"] + [f"Appliance{i}" for i in range(1, 10)]

for file in files:
    print("\n" + "=" * 70)
    print(file.name)
    print("=" * 70)

    # Read only timestamp and power columns; process in chunks.
    columns = [time_col] + power_cols
    chunks = []

    for chunk in pd.read_csv(
        file,
        usecols=columns,
        chunksize=200_000
    ):
        chunk[time_col] = pd.to_datetime(
            chunk[time_col], errors="coerce"
        )
        chunks.append(chunk)

    df = pd.concat(chunks, ignore_index=True)
    df = df.dropna(subset=[time_col]).sort_values(time_col)

    print(f"Rows with valid timestamps: {len(df):,}")
    print(f"Duplicate timestamps: {df[time_col].duplicated().sum():,}")

    intervals = df[time_col].diff().dt.total_seconds().dropna()

    print("\nTimestamp interval in seconds:")
    print(intervals.describe(percentiles=[0.25, 0.50, 0.75, 0.95]).round(2))

    print(f"Intervals <= 0 seconds: {(intervals <= 0).sum():,}")
    print(f"Intervals > 60 seconds: {(intervals > 60).sum():,}")

    print("\nMissing values per power column:")
    print(df[power_cols].isna().sum().to_string())

    print("\nNegative readings per power column:")
    print((df[power_cols] < 0).sum().to_string())

    print("\nMaximum observed power per column:")
    print(df[power_cols].max().round(2).to_string())

print("\nDiagnostics complete.")

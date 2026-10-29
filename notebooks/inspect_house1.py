
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent.parent
data_dir = root / "data" / "raw" / "house1"

files = [
    data_dir / "RAW_House1_Part1.csv",
    data_dir / "RAW_House1_Part2.csv",
]

for file in files:
    print("\n" + "=" * 65)
    print(f"FILE: {file.name}")
    print("=" * 65)

    if not file.exists():
        print(f"ERROR: File not found: {file}")
        continue

    # Read only a small sample first
    sample = pd.read_csv(file, nrows=5)

    print("\nColumn names:")
    print(sample.columns.tolist())

    print("\nFirst five rows:")
    print(sample.to_string(index=False))

    # Count rows and inspect data types in chunks to avoid loading
    # the entire large CSV into memory.
    total_rows = 0
    missing_values = None
    min_time = None
    max_time = None

    for chunk in pd.read_csv(file, chunksize=200_000):
        total_rows += len(chunk)

        if missing_values is None:
            missing_values = chunk.isna().sum()
        else:
            missing_values += chunk.isna().sum()

        # REFIT normally uses the column name "Time"
        if "Time" in chunk.columns:
            timestamps = pd.to_datetime(
                chunk["Time"], errors="coerce"
            ).dropna()

            if not timestamps.empty:
                chunk_min = timestamps.min()
                chunk_max = timestamps.max()

                min_time = (
                    chunk_min if min_time is None
                    else min(min_time, chunk_min)
                )
                max_time = (
                    chunk_max if max_time is None
                    else max(max_time, chunk_max)
                )

    print(f"\nTotal rows: {total_rows:,}")
    print("\nMissing values per column:")
    print(missing_values.to_string() if missing_values is not None else "None")

    print(f"\nEarliest timestamp: {min_time}")
    print(f"Latest timestamp:   {max_time}")

print("\nInspection completed.")

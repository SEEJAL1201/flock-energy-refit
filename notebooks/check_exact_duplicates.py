
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent.parent
data_dir = root / "data" / "raw" / "house1"

file = data_dir / "RAW_House1_Part1.csv"

total_rows = 0
exact_duplicates = 0
unique_rows = 0

# Count exact duplicates across the full file.
# The CSV is processed in chunks to limit memory use.
seen_rows = set()

for chunk in pd.read_csv(file, chunksize=100_000):
    total_rows += len(chunk)

    # Convert rows into tuples so duplicates can be compared.
    for row in chunk.itertuples(index=False, name=None):
        key = tuple(
            None if pd.isna(value) else value
            for value in row
        )

        if key in seen_rows:
            exact_duplicates += 1
        else:
            seen_rows.add(key)
            unique_rows += 1

print(f"Total rows: {total_rows:,}")
print(f"Exact duplicate rows: {exact_duplicates:,}")
print(f"Unique complete rows: {unique_rows:,}")
print(f"Check total: {exact_duplicates + unique_rows:,}")

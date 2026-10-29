
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent.parent
data_dir = root / "data" / "raw" / "house1"

files = [
    data_dir / "RAW_House1_Part1.csv",
    data_dir / "RAW_House1_Part2.csv",
]

columns = ["Time", "Aggregate"] + [
    f"Appliance{i}" for i in range(1, 10)
]

for file in files:
    print("\n" + "=" * 65)
    print(file.name)
    print("=" * 65)

    # Count timestamp occurrences in chunks without retaining all readings.
    counts = {}
    examples = {}

    for chunk in pd.read_csv(file, usecols=columns, chunksize=200_000):
        chunk["Time"] = pd.to_datetime(chunk["Time"], errors="coerce")
        chunk = chunk.dropna(subset=["Time"])

        timestamp_counts = chunk["Time"].value_counts()
        for timestamp, count in timestamp_counts.items():
            counts[timestamp] = counts.get(timestamp, 0) + int(count)

    repeated = {timestamp: count for timestamp, count in counts.items()
                if count > 1}

    print(f"Unique timestamps: {len(counts):,}")
    print(f"Timestamps repeated: {len(repeated):,}")
    print(f"Rows belonging to repeated timestamps: "
          f"{sum(repeated.values()):,}")

    # Examine the first few repeated timestamps against the original file.
    if repeated:
        selected = set(list(repeated.keys())[:10])
        rows_found = []

        for chunk in pd.read_csv(file, usecols=columns, chunksize=200_000):
            chunk["Time"] = pd.to_datetime(chunk["Time"], errors="coerce")
            matches = chunk[chunk["Time"].isin(selected)]
            if not matches.empty:
                rows_found.append(matches)

        if rows_found:
            sample = pd.concat(rows_found, ignore_index=True)
            print("\nExample repeated timestamps:")
            print(sample.sort_values("Time").to_string(index=False))

print("\nSummary complete. No source data was changed.")

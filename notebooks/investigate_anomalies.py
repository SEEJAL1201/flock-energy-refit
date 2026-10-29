
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent.parent
data_dir = root / "data" / "raw" / "house1"

part1 = data_dir / "RAW_House1_Part1.csv"
part2 = data_dir / "RAW_House1_Part2.csv"

power_cols = ["Aggregate"] + [
    f"Appliance{i}" for i in range(1, 10)
]

# -------------------------------------------------
# 1. Inspect duplicate timestamps in a sample
# -------------------------------------------------
print("\n=== PART 1: DUPLICATE TIMESTAMP EXAMPLES ===")

sample = pd.read_csv(part1, nrows=100_000)
sample["Time"] = pd.to_datetime(sample["Time"], errors="coerce")

duplicate_rows = sample[
    sample.duplicated("Time", keep=False)
].sort_values("Time")

print(f"Rows in sample: {len(sample):,}")
print(f"Rows involved in repeated timestamps: {len(duplicate_rows):,}")

if not duplicate_rows.empty:
    print("\nFirst 15 duplicate-timestamp records:")
    print(duplicate_rows.head(15).to_string(index=False))

    duplicated_groups = duplicate_rows.groupby("Time")
    exact_groups = 0
    conflicting_groups = 0

    for _, group in duplicated_groups:
        if len(group.drop(columns=["Time"]).drop_duplicates()) == 1:
            exact_groups += 1
        else:
            conflicting_groups += 1

    print(f"\nRepeated timestamp groups with identical readings: {exact_groups}")
    print(f"Repeated timestamp groups with conflicting readings: {conflicting_groups}")
else:
    print("No duplicate timestamps found in this sample.")

# -------------------------------------------------
# 2. Count high readings in both files
# -------------------------------------------------
for file in [part1, part2]:
    print(f"\n=== HIGH READINGS: {file.name} ===")

    counts = {column: 0 for column in power_cols}
    examples = {column: [] for column in power_cols}

    for chunk in pd.read_csv(file, chunksize=200_000):
        for column in power_cols:
            values = pd.to_numeric(chunk[column], errors="coerce")
            mask = values > 4000

            counts[column] += int(mask.sum())

            if len(examples[column]) < 3 and mask.any():
                remaining = 3 - len(examples[column])
                rows = chunk.loc[mask, ["Time", column]].head(remaining)
                examples[column].extend(rows.to_dict("records"))

    print("\nReadings above 4000 W (investigation threshold):")
    print(pd.Series(counts).to_string())

    print("\nExamples of high readings:")
    for column, records in examples.items():
        if records:
            print(f"\n{column}:")
            for record in records:
                print(f"  {record['Time']} -> {record[column]} W")

print("\nInvestigation complete. Original CSV files were not modified.")

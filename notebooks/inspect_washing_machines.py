
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "cleaned"

# Household number: washing-machine channel
HOUSEHOLDS = {
    1: "Appliance5",
    2: "Appliance2",
    3: "Appliance6",
    5: "Appliance3",
}

print("REFIT WASHING-MACHINE DATA INSPECTION")
print("=" * 65)

for house, channel in HOUSEHOLDS.items():
    file_path = DATA_DIR / f"CLEAN_House{house}.csv"

    print(f"\nHouse {house} | {channel}")
    print("-" * 45)

    if not file_path.exists():
        print("ERROR: File not found:", file_path.name)
        continue

    # Read only the columns needed for this household.
    df = pd.read_csv(file_path, nrows=5)

    print("Available columns:", df.columns.tolist())

    # Identify the time column from the file headers.
    time_candidates = [
        col for col in df.columns
        if col.strip().lower() in
        {"time", "datetime", "timestamp", "date"}
    ]

    if not time_candidates:
        print("ERROR: Could not identify the timestamp column.")
        continue

    time_col = time_candidates[0]

    if channel not in df.columns:
        print(f"ERROR: {channel} is not present in this file.")
        continue

    # Read only the timestamp and target appliance columns.
    data = pd.read_csv(
        file_path,
        usecols=[time_col, channel]
    )

    data[time_col] = pd.to_datetime(
        data[time_col], errors="coerce"
    )
    data[channel] = pd.to_numeric(
        data[channel], errors="coerce"
    )

    data = data.dropna(subset=[time_col])
    data = data.sort_values(time_col)

    power = data[channel]

    print(f"Rows: {len(data):,}")
    print(f"Date range: {data[time_col].min()} to "
          f"{data[time_col].max()}")
    print(f"Missing readings: {power.isna().sum():,}")
    print(f"Zero readings: {(power == 0).sum():,}")
    print(f"Positive readings: {(power > 0).sum():,}")
    print(f"Maximum power (W): {power.max()}")
    print(f"Mean power (W): {power.mean():.2f}")
    print(f"Median power (W): {power.median():.2f}")

print("\nInspection complete.")

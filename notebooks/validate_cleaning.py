
from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parent.parent
csv_path = root / "data" / "processed" / "house1_clean_1min.csv"
report_path = root / "reports" / "house1_quality_report.json"

print("=== OUTPUT FILE CHECK ===")

for path in [
    csv_path,
    report_path,
    root / "reports" / "house1_cleaned_first_day.png",
    root / "data" / "processed" / "house1_flagged_readings.csv",
]:
    if path.exists():
        print(f"FOUND: {path.name} ({path.stat().st_size / 1e6:.2f} MB)")
    else:
        print(f"MISSING: {path.name}")

if not csv_path.exists():
    raise FileNotFoundError(csv_path)

df = pd.read_csv(csv_path, parse_dates=["Time"], index_col="Time")

print("\n=== DATASET VALIDATION ===")
print(f"Rows: {len(df):,}")
print(f"First timestamp: {df.index.min()}")
print(f"Last timestamp:  {df.index.max()}")
print(f"Duplicate minute timestamps: {df.index.duplicated().sum():,}")

intervals = df.index.to_series().diff().dt.total_seconds().dropna()
print(f"Intervals other than 60 seconds: {(intervals != 60).sum():,}")

power_cols = ["Aggregate"] + [f"Appliance{i}" for i in range(1, 10)]

print("\nMissing values in power columns:")
print(df[power_cols].isna().sum().to_string())

print("\nNegative readings in power columns:")
print((df[power_cols] < 0).sum().to_string())

print("\nMaximum readings in power columns:")
print(df[power_cols].max().round(2).to_string())

print("\nFlagged minutes:")
for col in ["no_original_reading", "aggregate_missing", "long_outage"]:
    if col in df.columns:
        print(f"{col}: {df[col].fillna(False).astype(bool).sum():,}")

if report_path.exists():
    print("\n=== CLEANING REPORT ===")
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    print(json.dumps(report, indent=2))

print("\nValidation finished.")

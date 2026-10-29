
from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Use the one-minute cleaned House 1 dataset.
input_file = DATA_DIR / "house1_clean_1min.csv"
output_file = DATA_DIR / "house1_disaggregation_1min.csv"

if not input_file.exists():
    raise FileNotFoundError(
        f"Could not find {input_file}. "
        "Check that house1_clean_1min.csv exists in data/processed."
    )

df = pd.read_csv(input_file, parse_dates=["Time"])
df = df.sort_values("Time").drop_duplicates("Time")

required = ["Time", "Aggregate", "Appliance5"]
missing_columns = [c for c in required if c not in df.columns]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

df = df[required].copy()
df["Aggregate"] = pd.to_numeric(df["Aggregate"], errors="coerce")
df["Appliance5"] = pd.to_numeric(df["Appliance5"], errors="coerce")

# Retain only rows where both input and target are available.
df["valid_for_model"] = (
    df["Aggregate"].notna()
    & df["Appliance5"].notna()
    & (df["Aggregate"] >= 0)
    & (df["Appliance5"] >= 0)
)

valid_df = df.loc[df["valid_for_model"]].copy()

# Do not randomly shuffle this dataset; it is time-series data.
valid_df.to_csv(output_file, index=False)

report = {
    "source_file": str(input_file.relative_to(ROOT)),
    "output_file": str(output_file.relative_to(ROOT)),
    "total_rows": int(len(df)),
    "valid_rows": int(len(valid_df)),
    "excluded_rows": int(len(df) - len(valid_df)),
    "start_time": str(df["Time"].min()),
    "end_time": str(df["Time"].max()),
    "aggregate_missing": int(df["Aggregate"].isna().sum()),
    "washing_machine_missing": int(df["Appliance5"].isna().sum()),
    "aggregate_max_w": (
        float(df["Aggregate"].max())
        if df["Aggregate"].notna().any() else None
    ),
    "washing_machine_max_w": (
        float(df["Appliance5"].max())
        if df["Appliance5"].notna().any() else None
    ),
    "target_zero_percentage": round(
        100 * (valid_df["Appliance5"] == 0).mean(), 2
    ) if len(valid_df) else None,
}

report_file = REPORT_DIR / "disaggregation_data_report.json"
report_file.write_text(json.dumps(report, indent=2))

print("DISAGGREGATION DATA PREPARATION")
print("=" * 45)
print(json.dumps(report, indent=2))
print("\nPrepared dataset:", output_file)
print("Data report:", report_file)

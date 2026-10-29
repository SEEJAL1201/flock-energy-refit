
from pathlib import Path
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ==================================================
# 1. PATHS AND SETTINGS
# ==================================================
ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data" / "raw" / "house1"
OUTPUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    DATA_DIR / "RAW_House1_Part1.csv",
    DATA_DIR / "RAW_House1_Part2.csv",
]

TIME_COL = "Time"

POWER_COLS = ["Aggregate"] + [
    f"Appliance{i}" for i in range(1, 10)
]

MAX_APPLIANCE_W = 4000
MAX_AGGREGATE_W = 4000
SHORT_GAP_MINUTES = 2

PLOT_START = None
# Set PLOT_START to a timestamp such as "2013-12-28 00:00:00"
# to plot a particular day. None selects the first day.


# ==================================================
# 2. READ AND COMBINE RAW FILES
# ==================================================
frames = []
invalid_timestamp_rows = 0
input_rows_by_file = {}

for file in FILES:
    if not file.exists():
        raise FileNotFoundError(f"Missing input file: {file}")

    print(f"Reading {file.name}...")

    df = pd.read_csv(file)

    expected = [TIME_COL] + POWER_COLS
    missing_columns = set(expected) - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{file.name} is missing columns: "
            f"{sorted(missing_columns)}"
        )

    input_rows_by_file[file.name] = int(len(df))

    df[TIME_COL] = pd.to_datetime(
        df[TIME_COL], errors="coerce"
    )

    for col in POWER_COLS:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    invalid_timestamp_rows += int(
        df[TIME_COL].isna().sum()
    )

    # Rows without usable timestamps cannot enter a time series.
    df = df.dropna(subset=[TIME_COL])

    frames.append(df[[TIME_COL] + POWER_COLS])

raw = pd.concat(frames, ignore_index=True)

report = {
    "input_rows": int(sum(input_rows_by_file.values())),
    "input_rows_by_file": input_rows_by_file,
    "invalid_timestamp_rows_removed": invalid_timestamp_rows,
    "exact_duplicate_rows_removed": 0,
    "repeated_timestamp_groups": 0,
    "negative_power_values": {},
    "extreme_appliance_values_above_4000W": {},
    "extreme_aggregate_values_above_4000W": 0,
    "original_intervals_over_60_seconds": 0,
    "short_gap_minutes_interpolated": {},
    "long_outage_minutes": 0,
}


# ==================================================
# 3. SAVE A PRE-CLEANING SAMPLE FOR COMPARISON
# ==================================================
# Keep the raw observations for plotting. This is a
# limited plotting sample, not a second full data copy.

raw_plot = raw.copy()

raw_plot = raw_plot.sort_values(TIME_COL)
raw_plot = raw_plot.set_index(TIME_COL)

# Resolve duplicate timestamps for a readable raw plot.
raw_plot = raw_plot.groupby(level=0)[POWER_COLS].median()

if PLOT_START is None:
    plot_start = raw_plot.index.min().floor("D")
else:
    plot_start = pd.Timestamp(PLOT_START).floor("D")

plot_end = plot_start + pd.Timedelta(days=1)

raw_sample = raw_plot.loc[plot_start:plot_end]

if raw_sample.empty:
    print(
        f"Warning: no raw records found in plot window "
        f"{plot_start} to {plot_end}"
    )


# ==================================================
# 4. REMOVE EXACT DUPLICATE ROWS
# ==================================================
before_exact = len(raw)

raw = raw.drop_duplicates(
    subset=[TIME_COL] + POWER_COLS
)

report["exact_duplicate_rows_removed"] = int(
    before_exact - len(raw)
)


# ==================================================
# 5. FLAG AND HANDLE SUSPICIOUS POWER READINGS
# ==================================================
for col in POWER_COLS:
    report["negative_power_values"][col] = int(
        (raw[col] < 0).sum()
    )

for col in POWER_COLS[1:]:
    report["extreme_appliance_values_above_4000W"][col] = int(
        (raw[col] > MAX_APPLIANCE_W).sum()
    )

report["extreme_aggregate_values_above_4000W"] = int(
    (raw["Aggregate"] > MAX_AGGREGATE_W).sum()
)

# Preserve all suspicious source records before modifying
# values in the analytical dataset.
anomaly_mask = pd.Series(False, index=raw.index)

for col in POWER_COLS:
    anomaly_mask |= raw[col] < 0

anomaly_mask |= raw["Aggregate"] > MAX_AGGREGATE_W

for col in POWER_COLS[1:]:
    anomaly_mask |= raw[col] > MAX_APPLIANCE_W

anomalies = raw.loc[anomaly_mask].copy()

anomaly_path = OUTPUT_DIR / "house1_flagged_readings.csv"
anomalies.to_csv(anomaly_path, index=False)

print(f"Flagged source records saved: {len(anomalies):,}")

# Negative power readings are treated as invalid.
for col in POWER_COLS:
    raw.loc[raw[col] < 0, col] = np.nan

# Extreme appliance values are excluded from analytical
# power channels, but their original values remain in
# house1_flagged_readings.csv.
for col in POWER_COLS[1:]:
    raw.loc[raw[col] > MAX_APPLIANCE_W, col] = np.nan

# Aggregate readings above the threshold are retained.
# They are flagged rather than automatically deleted.
raw["aggregate_extreme_flag"] = (
    raw["Aggregate"] > MAX_AGGREGATE_W
)


# ==================================================
# 6. RESOLVE REPEATED TIMESTAMPS
# ==================================================
raw = raw.sort_values(TIME_COL)

timestamp_sizes = raw.groupby(TIME_COL).size()

report["repeated_timestamp_groups"] = int(
    (timestamp_sizes > 1).sum()
)

# Use the median when multiple observations share a timestamp.
# This reduces sensitivity to conflicting repeated records.
df = raw.groupby(TIME_COL)[POWER_COLS].median()

# Flag a timestamp if any source record at that timestamp
# had an extreme aggregate reading.
df["aggregate_extreme_flag"] = (
    raw.groupby(TIME_COL)["aggregate_extreme_flag"].max()
)

df = df.sort_index()


# ==================================================
# 7. RESAMPLE TO ONE-MINUTE INTERVALS
# ==================================================
# Median power is used for irregular observations within
# each minute. This is a practical summary, not an energy
# integral over the minute.

minute = df[POWER_COLS].resample("1min").median()

# Preserve a minute-level flag if any source timestamp
# in that minute had an aggregate reading above the limit.
minute["aggregate_extreme_flag"] = (
    df["aggregate_extreme_flag"]
    .resample("1min")
    .max()
    .reindex(minute.index)
    .eq(True)
)

# Flag minute bins containing no original timestamp.
original_counts = df.resample("1min").size()

minute["no_original_reading"] = (
    original_counts.reindex(
        minute.index, fill_value=0
    ) == 0
)

original_intervals = (
    df.index.to_series()
    .diff()
    .dt.total_seconds()
)

report["original_intervals_over_60_seconds"] = int(
    (original_intervals > 60).sum()
)


# ==================================================
# 8. INTERPOLATE ONLY SHORT GAPS
# ==================================================
# Interpolate at most two consecutive missing minute
# values, and only where valid readings exist on both sides.
# Longer gaps remain missing.

for col in POWER_COLS:
    missing_before = int(minute[col].isna().sum())

    minute[col] = minute[col].interpolate(
        method="time",
        limit=SHORT_GAP_MINUTES,
        limit_area="inside",
    )

    missing_after = int(minute[col].isna().sum())

    report["short_gap_minutes_interpolated"][col] = (
        missing_before - missing_after
    )


# ==================================================
# 9. FLAG MISSING DATA AND LONG OUTAGES
# ==================================================
minute["aggregate_missing"] = (
    minute["Aggregate"].isna()
)

missing = minute["aggregate_missing"]

run_id = missing.ne(missing.shift()).cumsum()

run_lengths = missing.groupby(run_id).transform("sum")

minute["long_outage"] = (
    missing & (run_lengths > SHORT_GAP_MINUTES)
)

report["long_outage_minutes"] = int(
    minute["long_outage"].sum()
)

report["output_minutes"] = int(len(minute))
report["output_start"] = str(minute.index.min())
report["output_end"] = str(minute.index.max())

report["missing_power_values_after_cleaning"] = {
    col: int(minute[col].isna().sum())
    for col in POWER_COLS
}

report["aggregate_extreme_flagged_minutes"] = int(
    minute["aggregate_extreme_flag"].sum()
)


# ==================================================
# 10. SAVE CLEANED DATA AND QUALITY REPORT
# ==================================================
output_csv = OUTPUT_DIR / "house1_clean_1min.csv"

minute.to_csv(
    output_csv,
    index_label=TIME_COL
)

report_path = REPORT_DIR / "house1_quality_report.json"

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("\nCLEANING SUMMARY")
print("=" * 45)
print(f"Input rows: {report['input_rows']:,}")
print(
    "Invalid timestamps removed: "
    f"{report['invalid_timestamp_rows_removed']:,}"
)
print(
    "Exact duplicate rows removed: "
    f"{report['exact_duplicate_rows_removed']:,}"
)
print(
    "Repeated timestamp groups: "
    f"{report['repeated_timestamp_groups']:,}"
)
print(
    "Original intervals > 60 seconds: "
    f"{report['original_intervals_over_60_seconds']:,}"
)
print(
    "Aggregate extreme source readings: "
    f"{report['extreme_aggregate_values_above_4000W']:,}"
)
print(
    "Output one-minute rows: "
    f"{report['output_minutes']:,}"
)
print(
    "Long-outage minutes: "
    f"{report['long_outage_minutes']:,}"
)

print("\nMissing power values after cleaning:")
for col, count in report[
    "missing_power_values_after_cleaning"
].items():
    print(f"  {col}: {count:,}")

print(f"\nCleaned CSV: {output_csv}")
print(f"Quality report: {report_path}")
print(f"Anomaly audit: {anomaly_path}")


# ==================================================
# 11. PLOT BEFORE AND AFTER CLEANING
# ==================================================
plot_cols = ["Aggregate", "Appliance1", "Appliance2"]

# Select the same 24-hour window for both plots.
clean_sample = minute.loc[
    plot_start:plot_end, plot_cols
]

if not raw_sample.empty and not clean_sample.empty:
    fig, axes = plt.subplots(
        len(plot_cols), 2,
        figsize=(16, 10),
        sharex="col"
    )

    for row, col in enumerate(plot_cols):
        # Before cleaning: raw observations at original
        # sampling times, after combining repeated timestamps.
        axes[row, 0].plot(
            raw_sample.index,
            raw_sample[col],
            linewidth=0.7
        )
        axes[row, 0].set_title(f"{col} — Before cleaning")
        axes[row, 0].set_ylabel("Power (W)")
        axes[row, 0].grid(True, alpha=0.3)

        # After cleaning: one-minute values.
        axes[row, 1].plot(
            clean_sample.index,
            clean_sample[col],
            linewidth=0.7
        )
        axes[row, 1].set_title(f"{col} — After cleaning")
        axes[row, 1].set_ylabel("Power (W)")
        axes[row, 1].grid(True, alpha=0.3)

    axes[-1, 0].set_xlabel("Time")
    axes[-1, 1].set_xlabel("Time")

    fig.suptitle(
        f"House 1: Before and after cleaning "
        f"({plot_start.date()})"
    )

    fig.tight_layout()

    comparison_path = (
        REPORT_DIR / "house1_before_after_cleaning.png"
    )

    fig.savefig(comparison_path, dpi=150)
    plt.close(fig)

    print(f"Before/after plot: {comparison_path}")

else:
    print(
        "Comparison plot skipped because the selected "
        "24-hour window has no data in one of the datasets."
    )


# Also save a cleaned-only plot for convenience.
clean_plot = minute.loc[plot_start:plot_end, plot_cols]

if not clean_plot.empty:
    fig, axes = plt.subplots(
        3, 1, figsize=(14, 9), sharex=True
    )

    for ax, col in zip(axes, plot_cols):
        ax.plot(
            clean_plot.index,
            clean_plot[col],
            linewidth=0.7
        )
        ax.set_ylabel(f"{col} (W)")
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Time")
    fig.suptitle(
        f"House 1: Cleaned one-minute readings "
        f"({plot_start.date()})"
    )
    fig.tight_layout()

    cleaned_plot_path = (
        REPORT_DIR / "house1_cleaned_first_day.png"
    )

    fig.savefig(cleaned_plot_path, dpi=150)
    plt.close(fig)

    print(f"Cleaned-only plot: {cleaned_plot_path}")


print("\nSection 1 cleaning script finished.")


from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

HOUSEHOLDS = [1, 2, 3, 5]
THRESHOLD_W = 10

hourly_results = []
daily_results = []

for house in HOUSEHOLDS:
    path = DATA_DIR / f"house{house}_washing_machine_1min_flagged.csv"

    df = pd.read_csv(path, parse_dates=["Time"])
    df = df.set_index("Time").sort_index()

    power = pd.to_numeric(df["power_w"], errors="coerce")
    valid = power.notna()
    active = power > THRESHOLD_W

    # Exclude flagged flat-reading minutes from activity-rate estimates.
    flagged = df["flat_reading_flag"].fillna(False).astype(bool)
    eligible = valid & ~flagged

    work = pd.DataFrame({
        "active": active & eligible,
        "eligible": eligible,
        "energy_wh": power.clip(lower=0) / 60,
    }, index=df.index)

    # Hourly activity rate: active minutes / eligible minutes.
    hourly = work.groupby(work.index.hour).agg(
        active_minutes=("active", "sum"),
        eligible_minutes=("eligible", "sum"),
        energy_wh=("energy_wh", "sum"),
    )
    hourly["active_rate_pct"] = (
        100 * hourly["active_minutes"] /
        hourly["eligible_minutes"].replace(0, pd.NA)
    )
    hourly["house"] = house
    hourly["hour"] = hourly.index
    hourly_results.append(hourly.reset_index(drop=True))

    # Daily activity: active minutes and estimated energy per calendar day.
    daily = work.resample("D").agg(
        active_minutes=("active", "sum"),
        eligible_minutes=("eligible", "sum"),
        energy_wh=("energy_wh", "sum"),
    )
    daily["active_rate_pct"] = (
        100 * daily["active_minutes"] /
        daily["eligible_minutes"].replace(0, pd.NA)
    )
    daily["day_of_week"] = daily.index.day_name()
    daily["house"] = house
    daily_results.append(daily.reset_index(names="date"))

hourly_df = pd.concat(hourly_results, ignore_index=True)
daily_df = pd.concat(daily_results, ignore_index=True)

hourly_path = REPORT_DIR / "washing_machine_hourly_patterns.csv"
daily_path = REPORT_DIR / "washing_machine_daily_patterns.csv"

hourly_df.to_csv(hourly_path, index=False)
daily_df.to_csv(daily_path, index=False)

# Plot hourly activity rates for the four households.
plt.figure(figsize=(11, 5))
for house in HOUSEHOLDS:
    subset = hourly_df[hourly_df["house"] == house]
    plt.plot(
        subset["hour"],
        subset["active_rate_pct"],
        marker="o",
        markersize=3,
        label=f"House {house}",
    )

plt.xticks(range(24))
plt.xlabel("Hour of day")
plt.ylabel("Active minutes (%)")
plt.title("Washing-Machine Activity by Hour")
plt.legend()
plt.tight_layout()
plt.savefig(REPORT_DIR / "washing_machine_hourly_patterns.png", dpi=150)
plt.close()

# Compare average activity rates by day of week.
weekday_order = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]

daily_summary = (
    daily_df.groupby(["house", "day_of_week"])["active_rate_pct"]
    .mean()
    .unstack("day_of_week")
    .reindex(columns=weekday_order)
)

daily_summary.to_csv(REPORT_DIR / "washing_machine_weekday_summary.csv")

print("Hourly patterns saved:", hourly_path)
print("Daily patterns saved:", daily_path)
print("Hourly plot saved: reports/washing_machine_hourly_patterns.png")
print("\nAverage daily activity rate by weekday (%):")
print(daily_summary.round(2).to_string())
print("\nUsage-pattern analysis complete.")

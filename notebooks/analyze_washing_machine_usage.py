
from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "cleaned"
OUTPUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

HOUSEHOLDS = {
    1: "Appliance5",
    2: "Appliance2",
    3: "Appliance6",
    5: "Appliance3",
}

summary = []

for house, channel in HOUSEHOLDS.items():
    file_path = DATA_DIR / f"CLEAN_House{house}.csv"

    print(f"\nProcessing House {house} ({channel})...")

    # Read only the required columns from the large CSV.
    df = pd.read_csv(
        file_path,
        usecols=["Time", channel]
    )

    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
    df[channel] = pd.to_numeric(df[channel], errors="coerce")
    df = df.dropna(subset=["Time"])
    df = df.sort_values("Time").drop_duplicates("Time", keep="last")
    df = df.set_index("Time")

    # Resample power to one-minute resolution.
    # Median reduces the effect of isolated spikes.
    minute = df[channel].resample("1min").median().to_frame("power_w")

    # Preserve missing minutes as missing; do not assume they mean zero.
    minute["power_missing"] = minute["power_w"].isna()

    # Define an active minute using a 10 W threshold.
    # This is an initial analytical threshold, not an official REFIT label.
    minute["active"] = minute["power_w"] > 10

    # Approximate energy: average watts over one minute / 60 = Wh.
    minute["energy_wh"] = minute["power_w"].clip(lower=0) / 60

    # Detect potential events: active periods separated by at least
    # 30 minutes without activity are treated as separate events.
    active = minute["active"].fillna(False)
    inactive_gap = (~active).astype(int)
    group = inactive_gap.cumsum()

    event_ids = pd.Series(index=minute.index, dtype="float64")
    event_counter = 0
    in_event = False
    inactive_run = 0

    for timestamp, is_active in active.items():
        if is_active:
            if not in_event or inactive_run >= 30:
                event_counter += 1
            event_ids.loc[timestamp] = event_counter
            in_event = True
            inactive_run = 0
        else:
            inactive_run += 1
            in_event = False if inactive_run >= 30 else in_event

    minute["event_id"] = event_ids

    out_file = OUTPUT_DIR / f"house{house}_washing_machine_1min.csv"
    minute.to_csv(out_file)

    valid_power = minute["power_w"].dropna()
    positive = valid_power[valid_power > 10]
    events = minute.loc[minute["event_id"].notna(), "event_id"].nunique()

    # Energy is approximate and is calculated only from observed/resampled
    # values, without filling missing periods.
    energy_kwh = minute["energy_wh"].sum(min_count=1) / 1000

    result = {
        "house": house,
        "channel": channel,
        "one_minute_rows": int(len(minute)),
        "missing_minutes": int(minute["power_missing"].sum()),
        "active_minutes_over_10w": int((valid_power > 10).sum()),
        "active_percentage_of_valid_minutes": (
            round(100 * (valid_power > 10).mean(), 2)
            if len(valid_power) else None
        ),
        "mean_power_w": round(float(valid_power.mean()), 2)
            if len(valid_power) else None,
        "peak_power_w": round(float(valid_power.max()), 2)
            if len(valid_power) else None,
        "approx_energy_kwh": round(float(energy_kwh), 3)
            if pd.notna(energy_kwh) else None,
        "potential_events": int(events),
        "output_file": str(out_file.relative_to(ROOT)),
    }
    summary.append(result)

    print(json.dumps(result, indent=2))

    # Plot the first seven days of available data.
    first_time = minute.index.min()
    first_week = minute.loc[
        first_time:first_time + pd.Timedelta(days=7)
    ]

    plt.figure(figsize=(12, 4))
    plt.plot(first_week.index, first_week["power_w"], linewidth=0.8)
    plt.title(f"House {house} Washing-Machine Power (First 7 Days)")
    plt.xlabel("Time")
    plt.ylabel("Power (W)")
    plt.tight_layout()
    plt.savefig(
        REPORT_DIR / f"house{house}_washing_machine_first_week.png",
        dpi=150
    )
    plt.close()

summary_path = REPORT_DIR / "washing_machine_usage_summary.json"
summary_path.write_text(json.dumps(summary, indent=2))

print("\n" + "=" * 60)
print("WASHING-MACHINE ANALYSIS COMPLETE")
print("Summary saved to:", summary_path)
print("One-minute CSVs saved in:", OUTPUT_DIR)
print("Plots saved in:", REPORT_DIR)

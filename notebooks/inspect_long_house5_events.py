
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / "data" / "processed" / "house5_washing_machine_1min.csv"

df = pd.read_csv(path, parse_dates=["Time"])
df["power_w"] = pd.to_numeric(df["power_w"], errors="coerce")
df = df.sort_values("Time").reset_index(drop=True)

THRESHOLD_W = 10
GAP_MINUTES = 10

active = (df["power_w"] > THRESHOLD_W).fillna(False).to_numpy()

# Identify continuous active runs.
runs = []
start = None

for i, value in enumerate(active):
    if value and start is None:
        start = i
    elif not value and start is not None:
        runs.append((start, i - 1))
        start = None

if start is not None:
    runs.append((start, len(active) - 1))

# Merge runs separated by fewer than 10 inactive minutes.
events = []
for start, end in runs:
    if events and start - events[-1][1] - 1 < GAP_MINUTES:
        events[-1][1] = end
    else:
        events.append([start, end])

durations = [
    (end - start + 1, start, end)
    for start, end in events
]

long_events = sorted(durations, reverse=True)[:10]

print("TEN LONGEST HOUSE 5 EVENTS")
print("=" * 65)

for duration, start, end in long_events:
    event = df.iloc[start:end + 1]
    valid_power = event["power_w"].dropna()

    print(f"\nDuration: {duration:,} minutes")
    print(f"Start: {event['Time'].iloc[0]}")
    print(f"End:   {event['Time'].iloc[-1]}")
    print(f"Rows: {len(event):,}")
    print(f"Missing power readings: {event['power_w'].isna().sum():,}")
    print(f"Active minutes (>10 W): {(valid_power > 10).sum():,}")
    print(f"Median power (W): {valid_power.median():.1f}")
    print(f"Maximum power (W): {valid_power.max():.1f}")

    # Show a small sample from the beginning and end.
    print("First 5 readings:")
    print(event[["Time", "power_w"]].head().to_string(index=False))
    print("Last 5 readings:")
    print(event[["Time", "power_w"]].tail().to_string(index=False))

print("\nInspection complete.")

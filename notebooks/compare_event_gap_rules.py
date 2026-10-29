
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"

HOUSEHOLDS = [1, 2, 3, 5]
THRESHOLD_W = 10
GAP_RULES = [10, 30]

def detect_events(power, gap_minutes):
    active = (power > THRESHOLD_W).fillna(False).to_numpy()

    runs = []
    start = None

    for i, is_active in enumerate(active):
        if is_active and start is None:
            start = i
        elif not is_active and start is not None:
            runs.append((start, i - 1))
            start = None

    if start is not None:
        runs.append((start, len(active) - 1))

    events = []
    for start, end in runs:
        if events and start - events[-1][1] - 1 < gap_minutes:
            events[-1][1] = end
        else:
            events.append([start, end])

    return [end - start + 1 for start, end in events]

for house in HOUSEHOLDS:
    path = DATA_DIR / f"house{house}_washing_machine_1min.csv"
    df = pd.read_csv(path, usecols=["power_w"])
    power = pd.to_numeric(df["power_w"], errors="coerce")

    print(f"\nHouse {house}")
    print("-" * 50)

    for gap in GAP_RULES:
        durations = pd.Series(detect_events(power, gap))

        print(f"\nInactivity gap: {gap} minutes")
        print(f"Total detected events: {len(durations)}")
        print(f"Median duration: {durations.median():.1f} min")
        print(f"Events > 180 min: {(durations > 180).sum()}")
        print(f"Events > 360 min: {(durations > 360).sum()}")
        print(f"Longest duration: {durations.max()} min")

print("\nComparison complete.")

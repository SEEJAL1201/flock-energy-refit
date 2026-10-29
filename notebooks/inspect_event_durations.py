
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"

HOUSEHOLDS = [1, 2, 3, 5]
THRESHOLD_W = 10
GAP_MINUTES = 30

for house in HOUSEHOLDS:
    path = DATA_DIR / f"house{house}_washing_machine_1min.csv"
    df = pd.read_csv(path, parse_dates=["Time"], index_col="Time")

    power = pd.to_numeric(df["power_w"], errors="coerce")
    active = (power > THRESHOLD_W).fillna(False).to_numpy()

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

    # Merge runs separated by fewer than GAP_MINUTES inactive minutes.
    events = []
    for start, end in runs:
        if events and start - events[-1][1] - 1 < GAP_MINUTES:
            events[-1][1] = end
        else:
            events.append([start, end])

    durations = pd.Series([
        end - start + 1 for start, end in events
    ], dtype="int64")

    print(f"\nHouse {house}")
    print("=" * 45)
    print(f"Total merged events: {len(durations)}")
    print("\nDuration percentiles (minutes):")
    print(durations.quantile([0.25, 0.50, 0.75, 0.90, 0.95, 0.99]).round(1))
    print("\nEvents longer than 180 minutes:", int((durations > 180).sum()))
    print("Events longer than 360 minutes:", int((durations > 360).sum()))
    print("\n10 longest events (minutes):")
    print(durations.nlargest(10).to_list())

print("\nDuration inspection complete.")

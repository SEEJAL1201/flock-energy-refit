
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"

HOUSEHOLDS = [1, 2, 3, 5]
ACTIVE_THRESHOLD_W = 10
MIN_INACTIVE_GAP_MINUTES = 30

for house in HOUSEHOLDS:
    file_path = DATA_DIR / f"house{house}_washing_machine_1min.csv"
    df = pd.read_csv(file_path, parse_dates=["Time"], index_col="Time")

    power = pd.to_numeric(df["power_w"], errors="coerce")
    active = power > ACTIVE_THRESHOLD_W
    valid = power.notna()

    # Detect contiguous active runs first.
    # Then merge runs separated by less than 30 inactive minutes.
    active_positions = active.fillna(False).to_numpy()
    runs = []
    start = None

    for i, is_active in enumerate(active_positions):
        if is_active and start is None:
            start = i
        elif not is_active and start is not None:
            runs.append((start, i - 1))
            start = None

    if start is not None:
        runs.append((start, len(active_positions) - 1))

    merged_events = []
    for run_start, run_end in runs:
        if not merged_events:
            merged_events.append([run_start, run_end])
            continue

        previous_end = merged_events[-1][1]
        inactive_gap = run_start - previous_end - 1

        if inactive_gap < MIN_INACTIVE_GAP_MINUTES:
            merged_events[-1][1] = run_end
        else:
            merged_events.append([run_start, run_end])

    durations = []
    peaks = []
    energies = []

    for start_idx, end_idx in merged_events:
        event_power = power.iloc[start_idx:end_idx + 1]
        active_minutes = int((event_power > ACTIVE_THRESHOLD_W).sum())
        duration_minutes = end_idx - start_idx + 1
        peak_w = event_power.max()
        energy_kwh = event_power.clip(lower=0).sum() / 60000

        # Keep events with at least 5 active minutes for this diagnostic.
        if active_minutes >= 5:
            durations.append(duration_minutes)
            peaks.append(float(peak_w))
            energies.append(float(energy_kwh))

    print(f"\nHouse {house}")
    print("-" * 40)
    print(f"Valid minutes: {int(valid.sum()):,}")
    print(f"Raw active runs: {len(runs):,}")
    print(f"Events after 30-minute merging: {len(merged_events):,}")
    print(f"Events with at least 5 active minutes: {len(durations):,}")

    if durations:
        print(f"Median event duration (min): {pd.Series(durations).median():.1f}")
        print(f"Median event peak (W): {pd.Series(peaks).median():.1f}")
        print(f"Median estimated event energy (kWh): {pd.Series(energies).median():.4f}")
        print(f"Longest event duration (min): {max(durations):,}")

print("\nEvent validation diagnostic complete.")

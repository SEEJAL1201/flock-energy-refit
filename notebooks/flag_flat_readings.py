
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

for house in [1, 2, 3, 5]:
    path = DATA_DIR / f"house{house}_washing_machine_1min.csv"
    df = pd.read_csv(path, parse_dates=["Time"])
    power = pd.to_numeric(df["power_w"], errors="coerce")

    # A new run begins when the power changes or is missing.
    same_as_previous = (
        power.eq(power.shift())
        & power.notna()
        & power.gt(10)
    )
    run_id = (~same_as_previous).cumsum()

    run_length = (
        power.groupby(run_id)
        .transform("size")
    )

    # Flag constant nonzero readings lasting at least 120 minutes.
    df["flat_reading_flag"] = (
        power.gt(10)
        & same_as_previous.groupby(run_id).transform("size").ge(120)
        & run_length.ge(120)
    )

    # Keep power values unchanged; this is a diagnostic flag only.
    output = DATA_DIR / f"house{house}_washing_machine_1min_flagged.csv"
    df.to_csv(output, index=False)

    flagged = df.loc[df["flat_reading_flag"]]

    print(f"\nHouse {house}")
    print(f"Flagged minutes: {len(flagged):,}")
    print(f"Output: {output.name}")

print("\nFlat-reading flags created. Original power values were retained.")

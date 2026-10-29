
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"

for house in [1, 2, 3, 5]:
    path = DATA_DIR / f"house{house}_washing_machine_1min.csv"
    df = pd.read_csv(path, usecols=["power_w"])

    power = pd.to_numeric(df["power_w"], errors="coerce")

    # Count consecutive minutes with exactly the same nonzero reading.
    same_as_previous = power.eq(power.shift()) & power.notna() & power.gt(10)
    group = (~same_as_previous).cumsum()

    runs = (
        pd.DataFrame({"power": power, "group": group})
        .loc[lambda x: x["power"] > 10]
        .groupby(["group", "power"], sort=False)
        .size()
        .reset_index(name="minutes")
    )

    long_runs = runs[runs["minutes"] >= 120].sort_values(
        "minutes", ascending=False
    )

    print(f"\nHouse {house}")
    print("-" * 45)
    print(f"Constant-power runs >= 120 minutes: {len(long_runs)}")
    if not long_runs.empty:
        print("Longest runs:")
        print(long_runs.head(10).to_string(index=False))

print("\nFlat-reading inspection complete.")

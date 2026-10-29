
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent.parent
csv_path = root / "data" / "processed" / "house1_clean_1min.csv"

df = pd.read_csv(csv_path, parse_dates=["Time"])

power_cols = ["Aggregate"] + [
    f"Appliance{i}" for i in range(1, 10)
]

print("=== EXTREME READINGS ABOVE 4000 W ===")

for col in power_cols:
    extreme = df[df[col] > 4000]

    if not extreme.empty:
        print(f"\n{col}: {len(extreme):,} readings")
        print(
            extreme[["Time", col]]
            .sort_values(col, ascending=False)
            .head(5)
            .to_string(index=False)
        )

print("\n=== RECORDS AROUND THE LARGEST AGGREGATE READING ===")

idx = df["Aggregate"].idxmax()
start = max(0, idx - 3)
end = min(len(df), idx + 4)

print(
    df.loc[start:end, ["Time"] + power_cols]
    .to_string(index=False)
)

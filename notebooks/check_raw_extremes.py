
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent.parent
raw_dir = root / "data" / "raw" / "house1"

files = [
    raw_dir / "RAW_House1_Part1.csv",
    raw_dir / "RAW_House1_Part2.csv",
]

# Suspicious periods identified in the cleaned data
checks = [
    ("2013-12-28 08:05:00", "2013-12-28 08:13:00"),
    ("2014-04-19 09:23:00", "2014-04-19 09:33:00"),
    ("2015-01-19 07:43:00", "2015-01-19 07:53:00"),
]

for start, end in checks:
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)

    print(f"\n{'=' * 65}")
    print(f"Checking {start} to {end}")

    for file in files:
        if not file.exists():
            continue

        # Read only the relevant time range from each raw file.
        for chunk in pd.read_csv(file, chunksize=250_000):
            chunk["Time"] = pd.to_datetime(
                chunk["Time"], errors="coerce"
            )

            match = chunk[
                chunk["Time"].between(start, end)
            ]

            if not match.empty:
                cols = ["Time", "Aggregate"] + [
                    f"Appliance{i}" for i in range(1, 10)
                ]
                print(f"\nSource: {file.name}")
                print(match[cols].to_string(index=False))

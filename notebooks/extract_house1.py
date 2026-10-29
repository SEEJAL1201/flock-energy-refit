
from pathlib import Path
import py7zr

root = Path(__file__).resolve().parent.parent
archive = Path.home() / "Downloads" / "REFIT_RAW_081116.7z"
destination = root / "data" / "raw" / "house1"

required_files = [
    "RAW_House1_Part1.csv",
    "RAW_House1_Part2.csv",
]

if not archive.exists():
    raise FileNotFoundError(f"Archive not found: {archive}")

destination.mkdir(parents=True, exist_ok=True)

with py7zr.SevenZipFile(archive, mode="r") as z:
    available = set(z.getnames())
    missing = [name for name in required_files if name not in available]

    if missing:
        raise FileNotFoundError(f"Missing archive entries: {missing}")

    z.extract(path=destination, targets=required_files)

print("\nExtraction verification:")
for name in required_files:
    # py7zr may preserve the archived filename in a nested directory.
    matches = list(destination.rglob(name))
    if not matches:
        print(f"MISSING: {name}")
        continue

    for path in matches:
        print(f"{path.name}: {path.stat().st_size / (1024**2):.2f} MB")

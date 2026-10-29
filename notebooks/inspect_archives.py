
from pathlib import Path
import py7zr

downloads = Path.home() / "Downloads"

archives = [
    downloads / "REFIT_RAW_081116.7z",
    downloads / "CLEAN_REFIT_081116.7z",
]

for archive in archives:
    print("\n" + "=" * 70)
    print(f"Archive: {archive.name}")
    print("=" * 70)

    if not archive.exists():
        print(f"ERROR: File not found: {archive}")
        continue

    print(f"Size: {archive.stat().st_size / (1024**2):.2f} MB")

    try:
        with py7zr.SevenZipFile(archive, mode="r") as z:
            names = z.getnames()

        print(f"Number of archived entries: {len(names)}")

        print("\nFirst 25 entries:")
        for name in names[:25]:
            print(" ", name)

        print("\nEntries containing House 1 or House_1:")
        matches = [
            name for name in names
            if "house1" in name.lower()
            or "house_1" in name.lower()
        ]
        for name in matches[:30]:
            print(" ", name)

        if not matches:
            print("No obvious House 1 filenames found; we will inspect naming patterns.")

    except Exception as exc:
        print(f"ERROR inspecting archive: {type(exc).__name__}: {exc}")

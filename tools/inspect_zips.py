import zipfile
from pathlib import Path

bundle = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")

for name in ["manuscript_revised_2026-10-11.zip", "supplementary_revised_2026-10-11.zip"]:
    p = bundle / name
    print(f"=== {p.name} ({p.stat().st_size} bytes) ===")
    with zipfile.ZipFile(p, "r") as z:
        for info in z.infolist():
            print(f"  {info.file_size:>10}  {info.filename}")
        print(f"  Total entries: {len(z.infolist())}")
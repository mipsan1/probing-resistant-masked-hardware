import zipfile
from pathlib import Path

p = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript_revised_2026-10-12_d2removed.zip")
print(f"Zip size: {p.stat().st_size} bytes")
with zipfile.ZipFile(p, "r") as z:
    for info in z.infolist():
        print(f"  {info.file_size:>10}  {info.filename}")
import json
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
lib = json.loads((BUNDLE / "synth" / "library_yosys.json").read_text())
for l in lib.get("libraries", []):
    names = [c["name"] for c in l.get("cells", [])]
    print(f"  {l['name']}: {len(names)} cells: {names}")
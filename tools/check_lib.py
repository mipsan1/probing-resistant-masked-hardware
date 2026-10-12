import json
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
lib = json.loads((BUNDLE / "synth" / "library_yosys.json").read_text())
for l in lib.get("libraries", []):
    if l["name"] == "custom":
        cells = [c["name"] for c in l["cells"]]
        print(f"  custom cells: {cells}")
        for c in l["cells"]:
            if "xnor" in c["name"].lower() or c["name"] == "reg":
                print(f"    {c['name']}: aliases={c.get('aliases', [])}")
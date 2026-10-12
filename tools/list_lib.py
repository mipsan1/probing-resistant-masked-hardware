import json
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
lib = json.loads((BUNDLE / "synth" / "library_yosys.json").read_text())
print('library_yosys.json cells:')
for c in lib.get('cells', []):
    name = c.get('name')
    print(f"  {name}")
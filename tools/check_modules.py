import json
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
data = json.loads((BUNDLE / "tools" / "prolead-modeB" / "design" / "netlist.json").read_text())
print(f"top-level keys: {list(data.keys())}")
print(f"modules: {len(data.get('modules', {}))}")
for k, v in list(data.get("modules", {}).items())[:10]:
    print(f"  {k}: {len(v.get('cells', {}))} cells, {len(v.get('netnames', {}))} nets")
print(f"...")
for k, v in list(data.get("modules", {}).items())[-5:]:
    print(f"  {k}: {len(v.get('cells', {}))} cells, {len(v.get('netnames', {}))} nets")
import json
data = json.load(open(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9.json"))
print(f"top-level keys: {list(data.keys())}")
print(f"modules: {list(data.get('modules', {}).keys())[:5]}")
for k, v in data.get("modules", {}).items():
    print(f"  {k}: {len(v.get('cells', {}))} cells, {len(v.get('netnames', {}))} nets")
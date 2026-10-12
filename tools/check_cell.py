import json
data = json.load(open(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\tools\prolead-modeB\design\netlist.json"))
mod = data["modules"]["circuit"]
for cname, c in mod["cells"].items():
    if c.get("type") == "NOT":
        print("NOT cell:")
        pd = c.get("port_directions")
        print(f"  port_directions: {pd}")
        conn = c.get("connections")
        print(f"  connections: {conn}")
        break
print()
print(f"Total cells: {len(mod['cells'])}")
# count by type
from collections import Counter
types = Counter(c.get("type") for c in mod["cells"].values())
print("Cell type counts:")
for t, n in sorted(types.items()):
    print(f"  {t}: {n}")
"""Add NOT_ (uppercase + underscore) as a library cell/alias."""
import json
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
lib_path = BUNDLE / "synth" / "library_yosys.json"
data = json.loads(lib_path.read_text())

custom = None
for l in data.get("libraries", []):
    if l.get("name") == "custom":
        custom = l
        break

# For each cell, add ALL forms of aliases
additions_per_base = {
    "not": ["NOT", "NOT_", "$_NOT", "$_NOT_"],
    "and": ["AND", "AND_", "$_AND", "$_AND_"],
    "or": ["OR", "OR_", "$_OR", "$_OR_"],
    "nand": ["NAND", "NAND_", "$_NAND", "$_NAND_"],
    "nor": ["NOR", "NOR_", "$_NOR", "$_NOR_"],
    "xor": ["XOR", "XOR_", "$_XOR", "$_XOR_"],
    "xnor": ["XNOR", "XNOR_", "$_XNOR", "$_XNOR_"],
    "dff": ["DFF", "DFF_", "$_DFF", "$_DFF_", "$_DFF_P", "$_DFF_P_"],
}

for c in custom.get("cells", []):
    name = c["name"]
    if name in additions_per_base:
        for a in additions_per_base[name]:
            if a not in c["aliases"]:
                c["aliases"].append(a)

# Save
lib_path.write_text(json.dumps(data, indent=2))
print(f"Updated: {lib_path} ({lib_path.stat().st_size} B)")
for c in custom.get("cells", []):
    if c["name"] in additions_per_base:
        print(f"  {c['name']}: {c['aliases']}")
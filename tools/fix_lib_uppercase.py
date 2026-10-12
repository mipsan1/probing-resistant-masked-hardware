"""Add NOT, AND, OR, etc. as uppercase cell names (matching 7/19 netlist style)."""
import json
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
lib_path = BUNDLE / "synth" / "library_yosys.json"
data = json.loads(lib_path.read_text())

# Add uppercase aliases to all custom cells
custom = None
for l in data.get("libraries", []):
    if l.get("name") == "custom":
        custom = l
        break

if custom is None:
    print("No custom library found")
    raise SystemExit(1)

# For each cell, ensure uppercase variant is in aliases
for c in custom.get("cells", []):
    name = c["name"]
    aliases = c.get("aliases", [])
    # Add uppercase name if not present
    upper = name.upper()
    if upper != name and upper not in aliases:
        aliases.append(upper)
    # Also add without trailing underscore form if has trailing _
    # (none in this case)
    c["aliases"] = aliases

# Add NOT cell (not in original) and AND/OR/NAND/NOR/XOR cells
existing_names = {c["name"].lower() for c in custom["cells"]}
existing_aliases = set()
for c in custom["cells"]:
    existing_aliases.update(a.lower() for a in c.get("aliases", []))

# Add new cell entries for direct NOT, AND, OR, etc. (in case 7/19 netlist uses these as cell names)
additions = [
    ("NOT", "not", ["not", "NOT", "$_NOT_"]),
    ("AND", "and", ["and", "AND", "$_AND_"]),
    ("OR", "or", ["or", "OR", "$_OR_"]),
    ("NAND", "nand", ["nand", "NAND", "$_NAND_"]),
    ("NOR", "nor", ["nor", "NOR", "$_NOR_"]),
    ("XOR", "xor", ["xor", "XOR", "$_XOR_"]),
    ("XNOR", "xnor", ["xnor", "XNOR", "$_XNOR_"]),
    ("DFF", "dff", ["dff", "DFF", "$_DFF_P_"]),
]
for name, base, aliases in additions:
    if base.lower() not in existing_names:
        print(f"  WARN: base {base} not in cells, skipping")
        continue
    # Add uppercase alias to the existing cell
    for c in custom["cells"]:
        if c["name"] == base:
            for a in aliases:
                if a not in c["aliases"]:
                    c["aliases"].append(a)
            break

# Also ensure custom has uppercase variant
# Save
lib_path.write_text(json.dumps(data, indent=2))
print(f"Updated: {lib_path} ({lib_path.stat().st_size} B)")
print("Custom cells after update:")
for c in custom["cells"]:
    print(f"  {c['name']}: aliases={c['aliases']}")
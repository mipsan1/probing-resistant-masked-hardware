"""Add all uppercase + underscore aliases for v9 netlist cells."""
import json
import re
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
text = Path(BUNDLE / "synth" / "prolead" / "circuit_v9_xform.v").read_text(errors="replace")

# Find all uppercase cell instantiations
emit_cells = set()
for m in re.finditer(r"(?:^|;)\s*([A-Z][A-Z0-9_]+)\s+\\\$[^\\s\(]+\s*\(", text, re.MULTILINE):
    emit_cells.add(m.group(1))
for m in re.finditer(r"(?:^|;)\s*([A-Z][A-Z0-9_]+)\s+[^\\s\(]+\s*\(", text, re.MULTILINE):
    emit_cells.add(m.group(1))

print(f"emit cells: {sorted(emit_cells)}")

# Map to library bases
mapping = {
    "AND_": "and",
    "NAND_": "nand",
    "OR_": "or",
    "NOR_": "nor",
    "XOR_": "xor",
    "XNOR_": "xnor",
    "NOT_": "not",
    "ANDNOT_": "andnot",  # need new cell
    "ORNOT_": "ornot",  # need new cell
    "MUX_": "mux",
    "DFF_": "dff",
    "DFFE_PN0P_": "dff",  # treat as dff
    "DFF_P_": "dff",
    "REG_": "dff",
}

needed = {}
for cell in emit_cells:
    base = mapping.get(cell)
    if base is None:
        print(f"  WARN: no mapping for {cell}")
        continue
    needed[cell] = base

# Update library
lib_path = BUNDLE / "synth" / "library_yosys.json"
data = json.loads(lib_path.read_text())
custom = None
for l in data.get("libraries", []):
    if l.get("name") == "custom":
        custom = l
        break

existing_bases = {c["name"]: c for c in custom.get("cells", [])}

# Add new cell types (andnot, ornot) if not present
new_cells_to_add = set()
for cell, base in needed.items():
    if base not in existing_bases:
        if base in ("andnot", "ornot"):
            new_cells_to_add.add(base)

for new_base in new_cells_to_add:
    if new_base == "andnot":
        custom["cells"].append({
            "name": "andnot",
            "aliases": ["ANDNOT", "ANDNOT_", "AND_NOT", "AND_NOT_", "aoi21", "AOI21"],
            "type": "gate",
            "inputs": ["A", "B"],
            "outputs": ["Y"],
            "equations": ["not (A and B)"]
        })
    elif new_base == "ornot":
        custom["cells"].append({
            "name": "ornot",
            "aliases": ["ORNOT", "ORNOT_", "OR_NOT", "OR_NOT_", "oai21", "OAI21"],
            "type": "gate",
            "inputs": ["A", "B"],
            "outputs": ["Y"],
            "equations": ["not (A or B)"]
        })
    existing_bases[new_base] = custom["cells"][-1]

# Add cell aliases
for cell, base in needed.items():
    if base in existing_bases:
        c = existing_bases[base]
        aliases = c.get("aliases", [])
        if cell not in aliases:
            aliases.append(cell)
        # Also add stripped and $_ prefixed forms
        for v in [cell.rstrip("_"), f"$_{cell}", f"$_{cell.rstrip('_')}"]:
            if v not in aliases:
                aliases.append(v)
        c["aliases"] = aliases

# Also: ensure dff has DFF_, DFFE_* aliases
for c in custom.get("cells", []):
    if c["name"] == "dff":
        for a in ["DFF", "DFF_", "DFF_P_", "DFF_P", "$_DFF", "$_DFF_", "$_DFF_P", "$_DFF_P_",
                  "$_DFFE_PN0P_", "$_DFFE_PN0_", "DFFE_PN0P_", "DFFE_PN0_", "DFF_X1", "DFF_X2", "DFF_X4",
                  "REG", "REG_", "$_REG", "$_REG_"]:
            if a not in c["aliases"]:
                c["aliases"].append(a)

lib_path.write_text(json.dumps(data, indent=2))
print(f"\nUpdated library: {lib_path.stat().st_size} B")
for c in custom.get("cells", []):
    if c["name"] in ("and", "or", "not", "xor", "xnor", "nand", "nor", "andnot", "ornot", "mux", "dff"):
        print(f"  {c['name']}: aliases count = {len(c['aliases'])}")
"""Add more DFF aliases for $_DFF_P_ etc."""
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

dff_aliases = ["DFF", "DFF_", "$_DFF", "$_DFF_", "$_DFF_P", "$_DFF_P_", "DFF_P_", "DFF_P",
               "$_DFF_PN0P_", "$_DFFE_PN0P_", "DFFE_PN0P_",
               "$_DFF_PN0_", "$_DFFE_PN0_",
               "$_SDFF_PN0_", "SDFF_PN0_",
               "DFF_X1", "DFF_X2", "DFF_X4"]
for c in custom.get("cells", []):
    if c["name"] == "dff":
        for a in dff_aliases:
            if a not in c["aliases"]:
                c["aliases"].append(a)
        # Also add REG-style aliases
        if "REG" not in c["aliases"]:
            c["aliases"].append("REG")
        if "REG_" not in c["aliases"]:
            c["aliases"].append("REG_")
        if "$_REG" not in c["aliases"]:
            c["aliases"].append("$_REG")
        if "$_REG_" not in c["aliases"]:
            c["aliases"].append("$_REG_")

lib_path.write_text(json.dumps(data, indent=2))
print(f"Updated: {lib_path}")
print(f"dff aliases: {custom.get('cells', [])[0]['aliases']}")
for c in custom.get("cells", []):
    if c["name"] == "dff":
        print(f"\n  {c['name']}: aliases count = {len(c['aliases'])}")
        for a in c['aliases']:
            print(f"    {a}")
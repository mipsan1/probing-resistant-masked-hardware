"""Add reg, $_XNOR_, $_DFF_P_ aliases to library_yosys.json so PROLEAD can read v12 netlist."""
import json
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
lib_path = BUNDLE / "synth" / "library_yosys.json"
data = json.loads(lib_path.read_text())

# Find custom library
for lib in data.get("libraries", []):
    if lib.get("name") == "custom":
        # Add $_XNOR_ alias to xnor
        for c in lib.get("cells", []):
            if c["name"] == "xnor":
                if "$_XNOR_" not in c["aliases"]:
                    c["aliases"].append("$_XNOR_")
                    print(f"  added $_XNOR_ alias to {c['name']}")
            if c["name"] == "xor":
                if "$_XOR_" not in c["aliases"]:
                    c["aliases"].append("$_XOR_")
                    print(f"  added $_XOR_ alias to {c['name']}")
            if c["name"] == "dff":
                if "$_DFF_P_" not in c["aliases"]:
                    c["aliases"].append("$_DFF_P_")
                    print(f"  added $_DFF_P_ alias to {c['name']}")
        # Add reg cell
        names = {c["name"] for c in lib.get("cells", [])}
        if "reg" not in names:
            lib["cells"].append({
                "name": "reg",
                "aliases": ["$_DFF_P_", "$reg"],
                "type": "register",
                "timing": "rising_edge",
                "inputs": ["C", "D"],
                "clock": "C",
                "outputs": ["Q"],
                "equations": ["((not C) and Q) or (C and D)"]
            })
            print(f"  added reg cell")
        # Add buf
        names = {c["name"] for c in lib.get("cells", [])}
        if "buf" not in names:
            lib["cells"].append({
                "name": "buf",
                "aliases": ["$_BUF_"],
                "type": "relaxed_gate",
                "inputs": ["A"],
                "outputs": ["Y"],
                "equations": ["A"]
            })
            print(f"  added buf cell")
        break

lib_path.write_text(json.dumps(data, indent=2))
print(f"Updated: {lib_path} ({lib_path.stat().st_size} B)")
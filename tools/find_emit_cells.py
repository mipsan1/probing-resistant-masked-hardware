from pathlib import Path
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9_xform.v").read_text(errors="replace")
import re
# Find all uppercase cell names (instantiations)
matches = set()
# Match "CELLNAME instname (" pattern at line start
for m in re.finditer(r"^\s*([A-Z][A-Z0-9_]+)\s+\\\$?[^\\s\(]+\s*\(", text, re.MULTILINE):
    matches.add(m.group(1))
print(f"all uppercase cells: {sorted(matches)}")
# Also check what library needs
needed = sorted(matches)
print(f"\n{len(needed)} unique cells needed")
for c in needed:
    print(f"  {c}")
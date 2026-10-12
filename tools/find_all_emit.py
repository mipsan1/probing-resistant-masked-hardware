from pathlib import Path
import re
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9_xform.v").read_text(errors="replace")
# Find all uppercase cell instantiations: CELL_NAME instance_name (
# Format: optional whitespace, UPPERCASE_NAME, space, instance, optional escaped \, (
matches = set()
# Match: start of line or after semicolon, uppercase token, space, inst, (
for m in re.finditer(r"(?:^|;)\s*([A-Z][A-Z0-9_]+)\s+\\\$[^\\s\(]+\s*\(", text, re.MULTILINE):
    matches.add(m.group(1))
# Also escaped form
for m in re.finditer(r"(?:^|;)\s*([A-Z][A-Z0-9_]+)\s+[^\\s\(]+\s*\(", text, re.MULTILINE):
    matches.add(m.group(1))
print(f"all uppercase cells: {sorted(matches)}")
"""Diagnose _pre_d1.v: find all modules and their top."""
import re
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
text = (BUNDLE / "synth" / "prolead" / "_pre_d1.v").read_text(errors="replace")
modules = re.findall(r"module\s+(\w+)\s*\(", text)
print(f"Total modules: {len(modules)}")
print(f"Unique: {sorted(set(modules))}")
# Top module is the one with `circuit` name (per PROLEAD convention)
print(f"\nFirst 30 chars after each 'module' keyword:")
for m in re.finditer(r"module\s+(\w+)", text):
    print(f"  pos {m.start()}: {m.group(1)}")
# Find randomIn width
m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
if m:
    width = int(m.group(1)) - int(m.group(2)) + 1
    print(f"\n  randomIn width: {width} bits = {width//8} bytes")
else:
    print(f"\n  randomIn not found")
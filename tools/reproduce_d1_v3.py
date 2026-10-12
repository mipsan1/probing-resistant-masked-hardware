"""Use wslpath to convert Windows path properly."""
import subprocess
import time
import re
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")

# Convert Windows path to WSL path via wslpath
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()
print(f"WSL path: {wsl_path}")

# Run synth
cmd = ["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
       f"cd '{wsl_path}' && yosys -q synth/synth_for_prolead_rel.ys 2>&1 | tail -30"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
print(f"\n=== yosys synth ===")
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0 and r.stderr:
    print(f"  stderr: {r.stderr[-500:]}")

pre_v = BUNDLE / "synth" / "prolead" / "_pre_d1.v"
if pre_v.exists():
    print(f"\n  _pre_d1.v: {pre_v.stat().st_size} B")
    text = pre_v.read_text(errors="replace")
    m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
    if m:
        width = int(m.group(1)) - int(m.group(2)) + 1
        print(f"  randomIn width: [{m.group(1)}:{m.group(2)}] = {width} bits = {width//8} bytes")
    m2 = re.search(r"module\s+(\w+)\s*\(", text)
    if m2:
        print(f"  top module: {m2.group(1)}")
else:
    print(f"\n  ! _pre_d1.v not generated")
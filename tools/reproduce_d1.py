"""Run full reproduction: WSL2 yosys synth -> docker PROLEAD."""
import subprocess
import json
import time
import hashlib
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
# WSL2 sees Windows paths as /mnt/c/...; we use the Linux absolute path
WSL_BUNDLE = "/mnt/c/Users/mipsa/Downloads/[IEEE TIFS Submitted 0731]/tifs-submission-bundle-2026-07-29"
# Bracket path is tricky in bash; use a no-bracket path via environment

print("=== Step 1: WSL2 yosys synth (current RTL -> circuit.v) ===")
# Use WSL2 yosys
synth_cmd = f"""bash -c 'cd "{WSL_BUNDLE}" && yosys -q synth/synth_for_prolead.ys 2>&1 | tail -10'"""
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{WSL_BUNDLE}' && yosys -q synth/synth_for_prolead.ys 2>&1 | tail -20"],
                   capture_output=True, text=True, timeout=120)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"  stderr: {r.stderr[-500:]}")

# Check output
pre_v = BUNDLE / "synth" / "prolead" / "_pre_d1.v"
if pre_v.exists():
    print(f"\n  _pre_d1.v: {pre_v.stat().st_size} B")
    # Find randomIn width
    import re
    text = pre_v.read_text(errors="replace")
    m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
    if m:
        print(f"  randomIn width: [{m.group(1)}:{m.group(2)}] = {int(m.group(1))-int(m.group(2))+1} bits = {(int(m.group(1))-int(m.group(2))+1)//8} bytes")
else:
    print(f"\n  ! _pre_d1.v not generated")
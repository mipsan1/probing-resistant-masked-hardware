"""WSL2 synth with absolute paths to handle bracket path issue."""
import subprocess
import json
import time
import hashlib
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")

# Use WSL2 path - the bundle is at /mnt/c/Users/mipsa/Downloads/[IEEE TIFS Submitted 0731]/tifs-submission-bundle-2026-07-29
# In bash, brackets are special chars; escape them
WSL_BUNDLE_BASH = '"/mnt/c/Users/mipsa/Downloads/\[IEEE TIFS Submitted 0731\]/tifs-submission-bundle-2026-07-29"'

print("=== Step 1: WSL2 yosys synth (current RTL -> circuit.v) ===")
synth_ys_content = f"""read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
hierarchy -check -top masked_sbox_first_order
proc; opt
fsm; opt
memory; opt
techmap; opt
clean
setundef -zero
write_verilog -nostr -noattr synth/prolead/_pre_d1.v
stat
"""
# Write the .ys with relative paths inside the bundle
(BUNDLE / "synth" / "synth_for_prolead_rel.ys").write_text(synth_ys_content)

# Now run wsl
cmd = ["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
       f'cd {WSL_BUNDLE_BASH} && yosys -q synth/synth_for_prolead_rel.ys 2>&1 | tail -25']
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0 and r.stderr:
    print(f"  stderr: {r.stderr[-500:]}")

pre_v = BUNDLE / "synth" / "prolead" / "_pre_d1.v"
if pre_v.exists():
    print(f"\n  _pre_d1.v: {pre_v.stat().st_size} B")
    import re
    text = pre_v.read_text(errors="replace")
    m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
    if m:
        width = int(m.group(1)) - int(m.group(2)) + 1
        print(f"  randomIn width: [{m.group(1)}:{m.group(2)}] = {width} bits = {width//8} bytes")
    # Top module name
    m2 = re.search(r"module\s+(\w+)\s*\(", text)
    if m2:
        print(f"  top module: {m2.group(1)}")
else:
    print(f"\n  ! _pre_d1.v not generated")
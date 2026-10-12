"""Full reproduction: WSL2 yosys with circuit wrapper, then docker PROLEAD."""
import subprocess
import json
import time
import re
import hashlib
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")

# Get WSL path
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()
print(f"WSL path: {wsl_path}")

# 1) Write synth_circuit.ys with relative paths
synth_circuit_ys = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
flatten; opt
clean
setundef -zero
write_verilog -nostr -noattr -noexpr synth/prolead/circuit.v
stat
"""
(BUNDLE / "synth" / "synth_circuit_rel.ys").write_text(synth_circuit_ys)

print(f"\n=== Step 1: yosys synth_circuit.ys (wrapper + flatten) ===")
t0 = time.time()
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{wsl_path}' && yosys -q synth/synth_circuit_rel.ys 2>&1 | tail -20"],
                   capture_output=True, text=True, timeout=180)
print(f"  exit: {r.returncode}  elapsed: {time.time()-t0:.1f}s")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0 and r.stderr:
    print(f"  stderr: {r.stderr[-500:]}")

circuit_v = BUNDLE / "synth" / "prolead" / "circuit.v"
if circuit_v.exists():
    print(f"\n  circuit.v: {circuit_v.stat().st_size} B")
    print(f"  MD5: {hashlib.md5(circuit_v.read_bytes()).hexdigest()}")
    text = circuit_v.read_text(errors="replace")
    m = re.search(r"module\s+(\w+)\s*\(", text)
    if m:
        print(f"  top module: {m.group(1)}")
    m2 = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
    if m2:
        width = int(m2.group(1)) - int(m2.group(2)) + 1
        print(f"  randomIn width: {width} bits = {width//8} bytes")
    n_modules = len(re.findall(r"module\s+\w+", text))
    print(f"  total modules: {n_modules}")
else:
    print(f"\n  ! circuit.v not generated")
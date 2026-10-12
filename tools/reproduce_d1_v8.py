"""Try synth with dfflibmap to canonicalize DFF cells to library's $_DFF_P_."""
import subprocess
import json
import time
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()

# Try with dfflibmap
ys = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
dfflibmap -liberty synth/library_yosys.lib
opt
flatten; opt
clean
setundef -zero
write_verilog -nostr -noattr -noexpr synth/prolead/circuit_dffmapped.v
"""
(BUNDLE / "synth" / "_dffmapped.ys").write_text(ys)

print("=== yosys with dfflibmap ===")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{wsl_path}' && yosys -q synth/_dffmapped.ys 2>&1 | tail -20"],
                   capture_output=True, text=True, timeout=180)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0 and r.stderr:
    print(f"  stderr: {r.stderr[-500:]}")

# Try without -liberty (use generic)
ys2 = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
dfflibmap -liberty <(echo)
opt
flatten; opt
clean
setundef -zero
write_verilog -nostr -noattr -noexpr synth/prolead/circuit_dffmapped2.v
"""
# Skip dffmapped2; instead try the synth_circuit.ys approach but with dfflibmap via library file

# Use the library file from the prolead image
print(f"\n=== Try with prolead image's library (yosys comes with simcells.v) ===")
# The prolead image has yosys at /opt/PROLEAD/yosys. Let me check what simcells it has
r = subprocess.run(["docker", "run", "--rm", "prolead-masked-aes:latest",
                    "bash", "-c", "ls /opt/PROLEAD/yosys/syn/ 2>&1 | head -10; find /opt/PROLEAD -name 'simcells*' 2>/dev/null | head -5"],
                   capture_output=True, text=True, timeout=60)
print(f"  yosys/syn/ contents: {r.stdout}")
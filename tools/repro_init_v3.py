"""Synth with abc -fast (matches 7/19 12:59 synth_first_order_full.ys) to canonicalize
DFFE_PN0P to $_DFF_P_ (or simpler DFF)."""
import subprocess
import json
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()

# Mirrors synth_first_order_full.ys (7/19 12:59) but with current RTL + circuit wrapper
ys = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
abc -fast; opt
clean
setundef -zero
write_verilog -nostr -noattr -noexpr synth/prolead/circuit_v3.v
"""
(BUNDLE / "synth" / "_abc_fast.ys").write_text(ys)

print("=== yosys synth with abc -fast ===")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{wsl_path}' && yosys -q synth/_abc_fast.ys 2>&1 | tail -15"],
                   capture_output=True, text=True, timeout=180)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0 and r.stderr:
    print(f"  stderr: {r.stderr[-500:]}")

out = BUNDLE / "synth" / "prolead" / "circuit_v3.v"
if out.exists():
    text = out.read_text(errors="replace")
    m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
    if m:
        width = int(m.group(1)) - int(m.group(2)) + 1
        print(f"  randomIn: {width} bits = {width//8} bytes")
    print(f"  file: {out.stat().st_size} B")
    n_DFFE = text.count("DFFE")
    n_const0 = text.count("32'h00000000")
    print(f"  DFFE: {n_DFFE}, 32'h00000000: {n_const0}")
    # Check what DFF cells remain
    import re as re2
    dff_cells = set(re2.findall(r'\$_(?:SDFF|DFF|DFFE|DFFE[PN]\w*)_', text))
    print(f"  DFF cell types: {dff_cells}")

# Try PROLEAD
print(f"\n=== PROLEAD init test on circuit_v3.v ===")
result_dir = BUNDLE / "sim" / "prolead_init_v3"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v3.v "
    f"--configfile=synth/config_init_7b.json "
    f"--resultfolder=/work/sim/prolead_init_v3 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Successfully", "Error", "FATAL", "logic_error", "Standard Probes", "Probing Sets", "matched", "extended", "placable", "initialized", "applied", "Probing"]):
        print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 5):")
    for line in r.stderr.split("\n")[-5:]:
        print(f"    {line[:200]}")
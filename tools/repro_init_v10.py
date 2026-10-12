"""Synth WITHOUT -noexpr (match 7/19 synth_first_order_full.ys exactly)."""
import subprocess
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()

ys1 = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
abc -fast; opt
flatten; opt
clean
setundef -zero
write_verilog -nostr -noattr synth/prolead/circuit_v10.v
"""
(BUNDLE / "synth" / "_v10.ys").write_text(ys1)

print("=== yosys synth without -noexpr (7/19 12:59 style) ===")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{wsl_path}' && yosys -q synth/_v10.ys 2>&1 | tail -10"],
                   capture_output=True, text=True, timeout=180)
print(f"  exit: {r.returncode}")

out = BUNDLE / "synth" / "prolead" / "circuit_v10.v"
if out.exists():
    text = out.read_text(errors="replace")
    dff_cells = set(re.findall(r'\$_(?:SDFF|DFF|DFFE|SDFFE)\w*', text))
    print(f"  DFF cell types: {dff_cells}")
    print(f"  file: {out.stat().st_size} B")
    cells = set(re.findall(r'\$_\w+', text))
    print(f"  $_ cells: {sorted(cells)}")
    m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
    if m:
        width = int(m.group(1)) - int(m.group(2)) + 1
        print(f"  randomIn: {width} bits = {width//8} bytes")
    mods = re.findall(r"^module\s+(\w+)", text, re.MULTILINE)
    print(f"  modules: {sorted(set(mods))}")
    n_const0 = text.count("32'h00000000")
    print(f"  32'h00000000: {n_const0}")
    n_XNOR = text.count("XNOR")
    print(f"  XNOR: {n_XNOR}")

# PROLEAD
print(f"\n=== PROLEAD init test on circuit_v10.v ===")
result_dir = BUNDLE / "sim" / "prolead_init_v10"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v10.v "
    f"--configfile=synth/config_init_7b.json "
    f"--resultfolder=/work/sim/prolead_init_v10 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Successfully", "Error", "FATAL", "matched", "extended", "placable", "initialized", "applied", "Probing", "Standard", "Probes"]):
        print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 5):")
    for line in r.stderr.split("\n")[-5:]:
        print(f"    {line[:200]}")
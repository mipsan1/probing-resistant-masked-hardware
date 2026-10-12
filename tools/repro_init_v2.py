"""Synth without setundef -zero to avoid 32'h00000000 literal."""
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

ys = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
dfflibmap -liberty /dev/null 2>/dev/null || true
flatten; opt
clean
write_verilog -nostr -noattr -noexpr synth/prolead/circuit_v2.v
"""
(BUNDLE / "synth" / "_no_setundef.ys").write_text(ys)

print("=== yosys synth (no setundef, with dfflibmap attempt) ===")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{wsl_path}' && yosys -q synth/_no_setundef.ys 2>&1 | tail -10"],
                   capture_output=True, text=True, timeout=180)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0 and r.stderr:
    print(f"  stderr: {r.stderr[-500:]}")

out = BUNDLE / "synth" / "prolead" / "circuit_v2.v"
if out.exists():
    text = out.read_text(errors="replace")
    m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
    if m:
        width = int(m.group(1)) - int(m.group(2)) + 1
        print(f"  randomIn: {width} bits = {width//8} bytes")
    print(f"  file: {out.stat().st_size} B")
    # Check for problematic patterns
    n_32hex = text.count("32'h")
    n_DFFE = text.count("DFFE")
    n_reg = text.count("reg[")
    n_const0 = text.count("32'h00000000")
    n_const1 = text.count("'h0")
    print(f"  32'h...: {n_32hex}, DFFE: {n_DFFE}, reg[: {n_reg}")
    print(f"  32'h00000000: {n_const0}, 'h0: {n_const1}")
else:
    print(f"  ! not generated")

# Try PROLEAD
print(f"\n=== PROLEAD init test on circuit_v2.v ===")
result_dir = BUNDLE / "sim" / "prolead_init_v2"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v2.v "
    f"--configfile=synth/config_init_7b.json "
    f"--resultfolder=/work/sim/prolead_init_v2 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Successfully", "Error", "FATAL", "logic_error", "Standard Probes", "Probing Sets", "matched", "extended", "placable", "initialized"]):
        print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 5):")
    for line in r.stderr.split("\n")[-5:]:
        print(f"    {line[:200]}")
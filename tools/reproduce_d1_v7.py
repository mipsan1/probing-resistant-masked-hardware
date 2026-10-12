"""Try synth without flatten (hierarchy preserved) so PROLEAD sees the wrapper structure."""
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

# Try multiple synth strategies
strategies = {
    "no_flatten_noexpr": """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
clean
setundef -zero
write_verilog -nostr -noattr -noexpr synth/prolead/circuit_no_flatten.v
""",
    "with_flatten": """read_verilog -sv rtl/masked_sbox_pkg.v
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
write_verilog -nostr -noattr -noexpr synth/prolead/circuit_flattened.v
""",
    "no_flatten_no_noexpr": """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
clean
setundef -zero
write_verilog -nostr -noattr synth/prolead/circuit_no_noexpr.v
""",
}
for name, ys in strategies.items():
    (BUNDLE / "synth" / f"_{name}.ys").write_text(ys)

for name in strategies:
    print(f"\n=== Strategy: {name} ===")
    r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                        f"cd '{wsl_path}' && yosys -q synth/_{name}.ys 2>&1 | tail -5"],
                       capture_output=True, text=True, timeout=180)
    print(f"  yosys exit: {r.returncode}")
    out_v = BUNDLE / "synth" / "prolead" / f"circuit_{name.split('_', 1)[1]}.v"
    if out_v.exists():
        text = out_v.read_text(errors="replace")
        m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
        if m:
            width = int(m.group(1)) - int(m.group(2)) + 1
            print(f"  randomIn: {width} bits = {width//8} bytes")
        n_mod = len(re.findall(r"module\s+\w+", text))
        print(f"  modules: {n_mod}, file: {out_v.stat().st_size} B")
        # Check for "32'h00000000" or other literal constants PROLEAD chokes on
        const_count = text.count("32'h00000000") + text.count("32'h0000")
        print(f"  32'h... constants: {const_count}")

# Test PROLEAD on the no_flatten variants
print(f"\n=== PROLEAD test on no_flatten_noexpr (7 bytes) ===")
result_dir = BUNDLE / "sim" / "prolead_d1_repro_v7"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)

docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    "cd /work && /opt/PROLEAD/release/PROLEAD "
    "--designfile=synth/prolead/circuit_no_flatten.v "
    "--configfile=synth/config.json "
    "--resultfolder=/work/sim/prolead_d1_repro_v7 "
    "--libraryfile=synth/library_yosys.json "
    "--libraryname=custom"
]
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
print(f"  exit: {r.returncode}, elapsed: depends on PROLEAD")
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Successfully", "Probing", "Elapsed", "Standard", "Output", "Error", "FATAL", "logic_error", "Error while"]):
        print(f"    {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 10):")
    for line in r.stderr.split("\n")[-10:]:
        print(f"    {line[:200]}")
leak_files = list(result_dir.glob("prolead_*_leakages.json"))
if leak_files:
    rep = json.loads(leak_files[0].read_text())
    print(f"\n  result: sims={rep.get('number_of_simulations')}, sets={rep.get('total_number_of_probing_sets')}, leaking={rep.get('number_of_leaking_probing_sets')}")
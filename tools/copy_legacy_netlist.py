"""Copy the 7/19 d=1 candidate netlist (circuit_struct_attr.v) into the bundle and
try to reproduce the 7/19 PROLEAD result."""
import shutil
import subprocess
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
SRC = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\IEEE-Transactions-TIFS_0717_hardware_Advanced\syn\prolead\circuit_struct_attr.v")
DST = BUNDLE / "synth" / "prolead_d1_candidate_attr.v"

# 1) Copy
if not SRC.exists():
    raise SystemExit(f"missing source: {SRC}")
shutil.copy2(SRC, DST)
print(f"Copied: {DST.name} ({DST.stat().st_size} B)")
import hashlib
print(f"  MD5: {hashlib.md5(DST.read_bytes()).hexdigest()}")

# 2) Run PROLEAD via docker
result_dir = BUNDLE / "sim" / "prolead_repro_2026-10-12"
result_dir.mkdir(parents=True, exist_ok=True)
result_dir_in_container = "/work/sim/prolead_repro_2026-10-12"

cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designFile=synth/prolead_d1_candidate_attr.v "
    f"--configFile=synth/config.json "
    f"--outputDirectory={result_dir_in_container} "
    f"--libraryFile=synth/library_yosys.json "
    f"--libraryName=custom"
]
print(f"\n=== Running PROLEAD (target: reproduce 7/19 0/14,400) ===")
print(f"  command: {' '.join(cmd[:6])} ... {cmd[-2]}")
r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
print(f"  exit: {r.returncode}")
print(f"  stdout (last 30 lines):")
for line in r.stdout.split("\n")[-30:]:
    print(f"    {line}")
if r.stderr:
    print(f"  stderr (last 10 lines):")
    for line in r.stderr.split("\n")[-10:]:
        print(f"    {line}")

# 3) Inspect the result
import json
leak_files = list(result_dir.glob("prolead_*_leakages.json"))
if leak_files:
    best = max(leak_files, key=lambda p: int(json.loads(p.read_text()).get("number_of_simulations", 0)))
    rep = json.loads(best.read_text())
    print(f"\n=== Reproduction result ({best.name}) ===")
    print(f"  sims: {rep.get('number_of_simulations')}")
    print(f"  total sets: {rep.get('total_number_of_probing_sets')}")
    print(f"  leaking: {rep.get('number_of_leaking_probing_sets')}")
    top = rep.get("most_leaking_probing_sets_in_total", [])
    if top:
        max_v = top[0].get("-log10(p)")
        print(f"  worst -log10(p): {max_v}")
    print(f"\n=== Reference (7/19 17:50:36) ===")
    print(f"  sims: 512000")
    print(f"  total sets: 14400")
    print(f"  leaking: 0")
    print(f"  worst stdout -log10(p): 4.205497")
    print(f"  worst JSON max_log10p: 3.386122")
else:
    print(f"\nNo leakages JSON found in {result_dir}")
"""Run docker PROLEAD on the freshly-synthesized circuit.v."""
import subprocess
import json
import time
import re
import hashlib
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")

# Clean previous result dir
result_dir = BUNDLE / "sim" / "prolead_d1_repro_2026-10-12"
if result_dir.exists():
    import shutil
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)

# PROLEAD command (docker)
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    "cd /work && /opt/PROLEAD/release/PROLEAD "
    "--designfile=synth/prolead/circuit.v "
    "--configfile=synth/config.json "
    "--resultfolder=/work/sim/prolead_d1_repro_2026-10-12 "
    "--libraryfile=synth/library_yosys.json "
    "--libraryname=custom"
]
print(f"=== Step 2: docker PROLEAD (reproduce 7/19 0/14,400) ===")
print(f"  design: synth/prolead/circuit.v (376 KB, MD5 1bd62272...)")
t0 = time.time()
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=1800)
elapsed = time.time() - t0
print(f"  exit: {r.returncode}  elapsed: {elapsed:.1f}s")

# Capture stdout log
if (result_dir / "stdout.log").exists():
    pass
# Show relevant stdout
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Successfully", "Probing", "Elapsed", "Standard", "Output", "Error", "FATAL", "logic_error"]):
        print(f"  stdout: {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 20):")
    for line in r.stderr.split("\n")[-20:]:
        print(f"    {line[:200]}")

# Inspect
leak_files = list(result_dir.glob("prolead_*_leakages.json"))
if leak_files:
    rep = json.loads(leak_files[0].read_text())
    print(f"\n=== Reproduction result ({leak_files[0].name}) ===")
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
    if str(rep.get('number_of_simulations')) == '512000' and str(rep.get('total_number_of_probing_sets')) == '14400' and str(rep.get('number_of_leaking_probing_sets')) == '0':
        print(f"\n  ✓ BIT-EXACT REPRODUCTION (512k sims, 14400 sets, 0 leaking)")
    else:
        print(f"\n  ≠ partial match")
else:
    print(f"\n  ! No leakages JSON in {result_dir}")
    print(f"  result_dir contents: {list(result_dir.iterdir())}")
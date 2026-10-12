"""Run PROLEAD on the 7/19 d=1 candidate netlist (lowercase --designfile)."""
import subprocess
import json
import hashlib
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
result_dir = BUNDLE / "sim" / "prolead_repro_2026-10-12"
result_dir.mkdir(parents=True, exist_ok=True)

# run_full.py style: lowercase --designfile, --configfile, --resultfolder, --libraryfile, --libraryname
cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead_d1_candidate_attr.v "
    f"--configfile=synth/config.json "
    f"--resultfolder=/work/sim/prolead_repro_2026-10-12 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
print(f"=== PROLEAD run (target: reproduce 7/19 0/14,400) ===")
print(f"  netlist: synth/prolead_d1_candidate_attr.v (9.1 MB, MD5 {hashlib.md5((BUNDLE / 'synth/prolead_d1_candidate_attr.v').read_bytes()).hexdigest()[:8]}...)")
r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
print(f"  exit: {r.returncode}")
# Print relevant stdout
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Probing", "Elapsed", "Standard Probes", "Probing Sets", "Output", "Successfully", "Output written", "Error", "FATAL"]):
        print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 15 lines):")
    for line in r.stderr.split("\n")[-15:]:
        print(f"    {line}")

# Inspect result
leak_files = list(result_dir.glob("prolead_*_leakages.json"))
if leak_files:
    best = max(leak_files, key=lambda p: int(json.loads(p.read_text()).get("number_of_simulations", 0)))
    rep = json.loads(best.read_text())
    print(f"\n=== Reproduction result ===")
    print(f"  file: {best.name}")
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
    if rep.get('number_of_simulations') == '512000' and rep.get('total_number_of_probing_sets') == '14400' and rep.get('number_of_leaking_probing_sets') == '0':
        print(f"\n  ✓ BIT-EXACT REPRODUCTION")
    else:
        print(f"\n  ≠ divergence: sims/14400/leaking")
else:
    print(f"\nNo leakages JSON in {result_dir}")
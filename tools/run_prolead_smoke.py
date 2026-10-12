"""Run PROLEAD on the 7/19 d=1 candidate netlist with a small smoke test
to confirm reproducibility, then a full run."""
import subprocess
import json
import time
import hashlib
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
NETLIST = BUNDLE / "synth" / "prolead_d1_candidate_attr.v"

print(f"=== Smoke test: 16,000 sims, d=1 ===")
print(f"  netlist: {NETLIST.name} ({NETLIST.stat().st_size} B, MD5 {hashlib.md5(NETLIST.read_bytes()).hexdigest()[:8]}...)")

# 1) Smoke config: copy current config and override sims to 16000
smoke_cfg = BUNDLE / "synth" / "config_smoke_d1.json"
import json as j
src_cfg = j.loads((BUNDLE / "synth" / "config.json").read_text())
src_cfg["simulation"]["number_of_simulations"] = "16000"
src_cfg["simulation"]["number_of_simulations_per_step"] = "16000"
src_cfg["simulation"]["number_of_simulations_per_write"] = "16000"
smoke_cfg.write_text(j.dumps(src_cfg, indent=2))

smoke_dir = BUNDLE / "sim" / "prolead_repro_smoke_2026-10-12"
smoke_dir.mkdir(parents=True, exist_ok=True)
cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead_d1_candidate_attr.v "
    f"--configfile=synth/config_smoke_d1.json "
    f"--resultfolder=/work/sim/prolead_repro_smoke_2026-10-12 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
print(f"  cmd: {' '.join(cmd[:6])} ... {cmd[-2][:60]}")
t0 = time.time()
r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
elapsed = time.time() - t0
print(f"  exit: {r.returncode}  elapsed: {elapsed:.1f}s")
if r.returncode != 0:
    print(f"  stderr (last 20):")
    for line in r.stderr.split("\n")[-20:]:
        print(f"    {line}")
else:
    leak_files = list(smoke_dir.glob("prolead_*_leakages.json"))
    if leak_files:
        rep = j.loads(leak_files[0].read_text())
        print(f"  sims: {rep.get('number_of_simulations')}")
        print(f"  total sets: {rep.get('total_number_of_probing_sets')}")
        print(f"  leaking: {rep.get('number_of_leaking_probing_sets')}")
        top = rep.get("most_leaking_probing_sets_in_total", [])
        if top:
            print(f"  worst -log10(p): {top[0].get('-log10(p)')}")
    else:
        print(f"  No leakages JSON. stdout (last 30):")
        for line in r.stdout.split("\n")[-30:]:
            print(f"    {line[:200]}")
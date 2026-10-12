"""Try PROLEAD with extended library on circuit_v12.v."""
import subprocess
import shutil
import json
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
result_dir = BUNDLE / "sim" / "prolead_init_v13"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)

docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v12.v "
    f"--configfile=synth/config_init_7b.json "
    f"--resultfolder=/work/sim/prolead_init_v13 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
print(f"exit: {r.returncode}")
# Show all stdout (init phase)
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"stderr:")
    for line in r.stderr.split("\n")[-10:]:
        print(f"  {line[:200]}")
# Result
leak_files = list(result_dir.glob("prolead_*_leakages.json"))
if leak_files:
    rep = json.loads(leak_files[0].read_text())
    print(f"\nresult: sims={rep.get('number_of_simulations')}, sets={rep.get('total_number_of_probing_sets')}, leaking={rep.get('number_of_leaking_probing_sets')}")
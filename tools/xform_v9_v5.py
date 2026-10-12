"""Replace 32'h00000000 constant with 1'b0 to avoid PROLEAD signal-not-found error."""
import re
import subprocess
import shutil
import time
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
src = BUNDLE / "synth" / "prolead" / "circuit_v9_xform.v"
dst = BUNDLE / "synth" / "prolead" / "circuit_v9_xform2.v"
data = src.read_bytes()

# Replace 32'h00000000 with 1'b0 (single bit zero, common idiom)
xform = data.replace(b"32'h00000000", b"1'b0")
# Also replace any other zero constants
xform = xform.replace(b"32'h0", b"1'b0")
xform = xform.replace(b"8'h00", b"1'b0")
xform = xform.replace(b"8'h0", b"1'b0")
dst.write_bytes(xform)

n_zeros = xform.count(b"32'h00000000")
n_1b0 = xform.count(b"1'b0")
print(f"32'h00000000 remaining: {n_zeros}")
print(f"1'b0 count: {n_1b0}")

# Run PROLEAD
result_dir = BUNDLE / "sim" / "prolead_init_v9_xform"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)

print(f"\n=== PROLEAD init on circuit_v9_xform2 ===")
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v9_xform2.v "
    f"--configfile=synth/config_init_256_d1.json "
    f"--resultfolder=/work/sim/prolead_init_v9_xform "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
t0 = time.time()
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
elapsed = time.time() - t0
print(f"  exit: {r.returncode}, elapsed: {elapsed:.1f}s")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0:
    for line in r.stderr.split("\n"):
        print(f"  stderr: {line[:200]}")

# Inspect
probes_file = result_dir / "prolead_circuit_probes.json"
if probes_file.exists():
    print(f"\n=== prolead_circuit_probes.json ===")
    print(f"  file: {probes_file.stat().st_size} B")
    import json
    data = json.loads(probes_file.read_text())
    for k in data:
        if isinstance(data[k], list):
            print(f"  {k}: {len(data[k])}")
        else:
            print(f"  {k}: {data[k]}")
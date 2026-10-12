"""Byte-level sed: replace literal bytes \\$_XXX_ with XXX (no regex)."""
import subprocess
import shutil
import time
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
src = BUNDLE / "synth" / "prolead" / "circuit_v9.v"
dst = BUNDLE / "synth" / "prolead" / "circuit_v9_xform.v"
data = src.read_bytes()

# Iterate over \\$_XXX_ patterns and replace with XXX
# Use bytes-level: find b'\\$_' + word + b'_' and replace with word
# b'\\$_' in bytes is backslash + dollar + underscore = 3 bytes
import re
# Use bytes regex
xform = re.sub(rb"\\\$_(\w+)", lambda m: m.group(1), data)
dst.write_bytes(xform)

# Verify
n_NOT_xform = xform.count(b"NOT")
n_XNOR_xform = xform.count(b"XNOR")
n_AND_xform = xform.count(b" AND ")
n_OR_xform = xform.count(b" OR ")
n_bs_remaining = xform.count(b"\\$_")
print(f"NOT count: {n_NOT_xform}")
print(f"XNOR count: {n_XNOR_xform}")
print(f"AND count: {n_AND_xform}")
print(f"OR count: {n_OR_xform}")
print(f"remaining \\_$: {n_bs_remaining}")
# Check first NOT
idx = xform.find(b"NOT ")
if idx > 0:
    print(f"NOT context: {xform[max(0,idx-5):idx+15]!r}")

# Run PROLEAD
result_dir = BUNDLE / "sim" / "prolead_init_v9_xform"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)

print(f"\n=== PROLEAD init on transformed v9 ===")
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v9_xform.v "
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
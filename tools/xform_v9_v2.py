"""Correctly convert \\$_XXX_ to XXX using backreference."""
import re
import subprocess
import shutil
import time
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
src = BUNDLE / "synth" / "prolead" / "circuit_v9.v"
dst = BUNDLE / "synth" / "prolead" / "circuit_v9_xform.v"
text = src.read_text(errors="replace")

# Use backreference: \$(...) captured group replaced
# Pattern: \\$_(name) -> \1
# In raw string: r'\\$_(w+)' captures the cell name
# But that matches only one char. Use \w* for trailing chars.
xform = re.sub(r"\\\$_(\w+)", r"\1", text)
dst.write_bytes(xform.encode("utf-8"))

# Verify
n_NOT_orig = text.count("\\$_NOT_")
n_NOT_xform = xform.count("\\$_NOT_")
n_XNOR_xform = xform.count("XNOR")
n_XOR_xform = xform.count("XOR ")
n_AND_xform = xform.count("AND ")
print(f"\\$_NOT_ count: orig={n_NOT_orig}, xform={n_NOT_xform}")
print(f"XNOR count: {n_XNOR_xform}")
print(f"XOR count: {n_XOR_xform}")
print(f"AND count: {n_AND_xform}")
# Check first instance
idx = xform.find("NOT ")
if idx >= 0:
    print(f"NOT context: {xform[max(0,idx-15):idx+30]!r}")
idx = xform.find("XNOR ")
if idx >= 0:
    print(f"XNOR context: {xform[max(0,idx-15):idx+30]!r}")

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
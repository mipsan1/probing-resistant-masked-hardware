"""Convert \\$_XXX_ to XXX in v9 netlist and run PROLEAD init."""
import re
import subprocess
import shutil
import time
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
src = BUNDLE / "synth" / "prolead" / "circuit_v9.v"
dst = BUNDLE / "synth" / "prolead" / "circuit_v9_xform.v"
text = src.read_text(errors="replace")

# Match backslash + dollar + underscore + word, strip backslash+dollar+underscore
def strip_prefix(m):
    name = m.group(0)
    # name is like '\$_NOT_' or '\$_XNOR_'
    if name.startswith("\\$_") and name.endswith("_"):
        return name[4:-1]  # strip \$_, keep last _ removed
    return name

xform = re.sub(r"\\\$_\w+", strip_prefix, text)
dst.write_bytes(xform.encode("utf-8"))

# Verify
n_xform = xform.count("XNOR")
n_orig = text.count("XNOR")
print(f"  XNOR count: orig={n_orig}, xform={n_xform}")
n_DFF = xform.count("DFF")
n_xs = xform.count("\\$_")
print(f"  DFF count: {n_DFF}, remaining \\$_: {n_xs}")

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
"""Correctly add a 32-bit zero wire (with proper bit-range syntax)."""
import re
import subprocess
import shutil
import time
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
src = BUNDLE / "synth" / "prolead" / "circuit_v9_xform.v"
dst = BUNDLE / "synth" / "prolead" / "circuit_v9_xform2.v"
text = src.read_text(errors="replace")

# Find the line with 32'h00000000
import re
# Replace the whole line
old_pattern = r"assign\s+\\masked_sbox_pkg::aes_affine_byte\$func\$rtl/masked_sbox_first_order\.v:606\$153\.r\s+=\s+32'h00000000;"

new_line = (
    "wire [31:0] \\zero_const_32 = 32'b0;\n"
    "  assign \\masked_sbox_pkg::aes_affine_byte$func$rtl/masked_sbox_first_order.v:606$153.r = \\zero_const_32;"
)

m = re.search(old_pattern, text)
if m:
    text = text[:m.start()] + new_line + text[m.end():]
    print(f"  replaced line at offset {m.start()}")
else:
    print("  ! pattern not found, trying loose match")
    for m in re.finditer(r"32'h00000000", text):
        print(f"    found at {m.start()}: {text[max(0,m.start()-30):m.end()+30]!r}")
        idx = m.start()
        # Find the start of this assign
        line_start = text.rfind("assign", 0, idx)
        line_end = text.find(";", idx) + 1
        old = text[line_start:line_end]
        new = "wire [31:0] \\zero_const_32 = 32'b0;\n  assign \\masked_sbox_pkg::aes_affine_byte$func$rtl/masked_sbox_first_order.v:606$153.r = \\zero_const_32;"
        text = text[:line_start] + new + text[line_end:]
        print(f"    replaced: {old[:50]}... -> {new[:50]}...")
        break

dst.write_bytes(text.encode("utf-8"))
print(f"  wrote: {dst} ({dst.stat().st_size} B)")

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
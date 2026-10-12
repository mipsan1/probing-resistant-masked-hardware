"""Synth masked_sbox_first_order.v only (no circuit.v wrapper), then manually wrap."""
import subprocess
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()

# Step 1: synth just masked_sbox_first_order
ys1 = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
hierarchy -check -top masked_sbox_first_order
proc; opt
fsm; opt
memory; opt
techmap; opt
abc -fast; opt
clean
setundef -zero
write_verilog -noattr synth/prolead/_sbox_only_syn.v
"""
(BUNDLE / "synth" / "_sbox_only.ys").write_text(ys1)

print("=== yosys synth masked_sbox_first_order only ===")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{wsl_path}' && yosys -q synth/_sbox_only.ys 2>&1 | tail -10"],
                   capture_output=True, text=True, timeout=180)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")

sbox_syn = BUNDLE / "synth" / "prolead" / "_sbox_only_syn.v"
if sbox_syn.exists():
    text = sbox_syn.read_text(errors="replace")
    dff_cells = set(re.findall(r'\$_(?:SDFF|DFF|DFFE|SDFFE)\w*', text))
    print(f"  DFF cell types: {dff_cells}")
    print(f"  file: {sbox_syn.stat().st_size} B")
    # Find top module
    m = re.search(r"module\s+(\w+)\s*\(", text)
    if m:
        print(f"  top module: {m.group(1)}")

# Step 2: write a circuit wrapper around the sbox (synthesized)
# But the cleanest way is: just rename top module in sbox_syn.v to "circuit"
# and add port renaming for randomIn
# Actually circuit.v has 7 bytes randomIn bus, sbox has 7 bytes r0..r6 individual
# Need to manually craft a wrapper

print(f"\n=== Generating circuit wrapper around _sbox_only_syn.v ===")
sbox_text = sbox_syn.read_text(errors="replace")
# Rename top module to "circuit" and add randomIn bus
wrap = """// circuit wrapper around synthesized masked_sbox_first_order
module circuit(clk, sboxIn, randomIn, sboxOut);
  input clk;
  input [15:0] sboxIn;
  input [55:0] randomIn;
  output [15:0] sboxOut;
"""
# Read synthesized sbox to get its port list
m = re.search(r"module\s+(\w+)\s*\(([^;]*)\);", sbox_text, re.DOTALL)
if m:
    sbox_module = m.group(1)
    sbox_ports = m.group(2)
    print(f"  sbox module: {sbox_module}")
    print(f"  sbox ports: {sbox_ports[:200]}")
    # Now extract just the body of sbox_syn.v
    # Find the sbox module body
    body_start = sbox_text.find(");", m.end()) + 2
    body_end = sbox_text.rfind("endmodule")
    sbox_body = sbox_text[body_start:body_end]
    # Replace sbox's individual r0_in..r6_in ports with randomIn bus slices
    # And rename top module
    wrapped = f"""module circuit(clk, sboxIn, randomIn, sboxOut);
  input clk;
  input [15:0] sboxIn;
  input [55:0] randomIn;
  output [15:0] sboxOut;

  wire [7:0] x0 = sboxIn[7:0];
  wire [7:0] x1 = sboxIn[15:8];
  wire [7:0] r0 = randomIn[ 0 +: 8];
  wire [7:0] r1 = randomIn[ 8 +: 8];
  wire [7:0] r2 = randomIn[16 +: 8];
  wire [7:0] r3 = randomIn[24 +: 8];
  wire [7:0] r4 = randomIn[32 +: 8];
  wire [7:0] r5 = randomIn[40 +: 8];
  wire [7:0] r6 = randomIn[48 +: 8];
  wire [7:0] y0, y1;
  wire v_out;

{sbox_body}

  assign sboxOut[7:0]  = y0;
  assign sboxOut[15:8] = y1;
endmodule
"""
    (BUNDLE / "synth" / "prolead" / "circuit_v5.v").write_text(wrapped)
    print(f"  wrote: synth/prolead/circuit_v5.v ({len(wrapped)} B)")

# Try PROLEAD
print(f"\n=== PROLEAD init test on circuit_v5.v ===")
result_dir = BUNDLE / "sim" / "prolead_init_v5"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v5.v "
    f"--configfile=synth/config_init_7b.json "
    f"--resultfolder=/work/sim/prolead_init_v5 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Successfully", "Error", "FATAL", "matched", "extended", "placable", "initialized", "applied", "Probing", "Standard"]):
        print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 5):")
    for line in r.stderr.split("\n")[-5:]:
        print(f"    {line[:200]}")
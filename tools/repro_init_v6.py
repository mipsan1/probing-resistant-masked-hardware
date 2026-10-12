"""Synth masked_sbox_first_order with flatten + abc -fast, then wrap."""
import subprocess
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()

# Mirror synth_circuit.ys from 7/19 11:51: hierarchy -top circuit + flatten + abc -fast
# But sbox first: synth with flatten and abc -fast
ys1 = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
hierarchy -check -top masked_sbox_first_order
proc; opt
fsm; opt
memory; opt
techmap; opt
abc -fast; opt
flatten
opt
clean
setundef -zero
write_verilog -noattr synth/prolead/_sbox_flat.v
"""
(BUNDLE / "synth" / "_sbox_flat.ys").write_text(ys1)

print("=== yosys synth masked_sbox_first_order with flatten + abc -fast ===")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{wsl_path}' && yosys -q synth/_sbox_flat.ys 2>&1 | tail -10"],
                   capture_output=True, text=True, timeout=180)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")

sbox_syn = BUNDLE / "synth" / "prolead" / "_sbox_flat.v"
if sbox_syn.exists():
    text = sbox_syn.read_text(errors="replace")
    dff_cells = set(re.findall(r'\$_(?:SDFF|DFF|DFFE|SDFFE)\w*', text))
    print(f"  DFF cell types: {dff_cells}")
    m = re.search(r"module\s+(\w+)\s*\(", text)
    if m:
        print(f"  top module: {m.group(1)}")
    # Find all modules
    mods = re.findall(r"module\s+(\w+)", text)
    print(f"  total modules: {len(set(mods))} (unique)")

# Wrap: top is now masked_sbox_first_order (after hierarchy -top), but emit was aes_affine_byte_mod
# Means hierarchy didn't apply. Let me use a different approach: read the existing _sbox_flat.v
# and create a circuit module wrapping the sbox body

# Read sbox ports (look for masked_sbox_first_order module)
m = re.search(r"module\s+masked_sbox_first_order\s*\(([^;]*)\);", text, re.DOTALL)
if m:
    sbox_ports = m.group(1)
    print(f"  masked_sbox_first_order ports: {sbox_ports[:200]}")
    # Get body
    body_start = text.find(");", m.end()) + 2
    body_end = text.rfind("endmodule")
    sbox_body = text[body_start:body_end]

    # Build wrapper that renames top to "circuit" with randomIn bus
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
    (BUNDLE / "synth" / "prolead" / "circuit_v6.v").write_text(wrapped)
    print(f"  wrote circuit_v6.v ({len(wrapped)} B)")
else:
    print("  ! masked_sbox_first_order module not found in sbox_syn")
    # Try the actual top module
    m = re.search(r"module\s+(\w+)\s*\(([^;]*)\);", text, re.DOTALL)
    if m:
        print(f"  actual top: {m.group(1)}")

# Try PROLEAD
print(f"\n=== PROLEAD init test on circuit_v6.v ===")
result_dir = BUNDLE / "sim" / "prolead_init_v6"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v6.v "
    f"--configfile=synth/config_init_7b.json "
    f"--resultfolder=/work/sim/prolead_init_v6 "
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
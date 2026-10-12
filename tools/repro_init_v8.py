"""Synth WITHOUT flatten (mirrors 7/19 13:24 circuit_struct_attr.v structure)."""
import subprocess
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()

ys1 = """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
hierarchy -check -top masked_sbox_first_order
proc; opt
fsm; opt
memory; opt
techmap; opt
clean
setundef -zero
write_verilog -nostr -noattr synth/prolead/_sbox_no_flatten.v
"""
(BUNDLE / "synth" / "_sbox_no_flatten.ys").write_text(ys1)

print("=== yosys synth sbox without flatten (mirrors 7/19 13:24) ===")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"cd '{wsl_path}' && yosys -q synth/_sbox_no_flatten.ys 2>&1 | tail -10"],
                   capture_output=True, text=True, timeout=180)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")

sbox_syn = BUNDLE / "synth" / "prolead" / "_sbox_no_flatten.v"
if sbox_syn.exists():
    text = sbox_syn.read_text(errors="replace")
    dff_cells = set(re.findall(r'\$_(?:SDFF|DFF|DFFE|SDFFE)\w*', text))
    print(f"  DFF cell types: {dff_cells}")
    m = re.search(r"module\s+(\w+)\s*\(", text)
    if m:
        print(f"  top module: {m.group(1)}")
    print(f"  file: {sbox_syn.stat().st_size} B")
    # Count modules
    mods = re.findall(r"^module\s+(\w+)", text, re.MULTILINE)
    print(f"  total modules: {len(mods)}, unique: {sorted(set(mods))}")

    # Wrap with randomIn bus
    m = re.search(r"module\s+masked_sbox_first_order\s*\(([^;]*)\);", text, re.DOTALL)
    if m:
        body_start = text.find(");", m.end()) + 2
        body_end = text.rfind("endmodule")
        # Find all endmodule positions and take the FIRST one (sbox body only)
        # The sbox is the first module. Find its endmodule.
        first_end = text.find("endmodule", body_start)
        sbox_body = text[body_start:first_end].strip()
        # Add remaining modules as submodules
        rest = text[first_end+len("endmodule"):].strip()

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

{rest}
"""
        (BUNDLE / "synth" / "prolead" / "circuit_v8.v").write_text(wrapped)
        print(f"  wrote circuit_v8.v ({len(wrapped)} B)")

# PROLEAD test
print(f"\n=== PROLEAD init test on circuit_v8.v ===")
result_dir = BUNDLE / "sim" / "prolead_init_v8"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v8.v "
    f"--configfile=synth/config_init_7b.json "
    f"--resultfolder=/work/sim/prolead_init_v8 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
print(f"  exit: {r.returncode}")
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Successfully", "Error", "FATAL", "matched", "extended", "placable", "initialized", "applied", "Probing", "Standard", "Probes"]):
        print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 5):")
    for line in r.stderr.split("\n")[-5:]:
        print(f"    {line[:200]}")
"""v12 + setundef -zero, attempt to match 7/19 13:24 output style."""
import subprocess
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                    f"wslpath '{BUNDLE}'"],
                   capture_output=True, text=True, timeout=30)
wsl_path = r.stdout.strip()

# Try multiple variants
variants = {
    "v14a": """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
abc -fast; opt
flatten
opt
clean
setundef -zero
write_verilog -nostr -noattr synth/prolead/circuit_v14a.v
""",
    "v14b": """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
read_verilog -sv rtl/circuit.v
hierarchy -check -top circuit
proc; opt
fsm; opt
memory; opt
techmap; opt
abc -fast; opt
clean
setundef -zero
write_verilog -nostr -noattr synth/prolead/circuit_v14b.v
""",
    "v14c": """read_verilog -sv rtl/masked_sbox_pkg.v
read_verilog -sv rtl/masked_sbox_first_order.v
hierarchy -check -top masked_sbox_first_order
proc; opt
fsm; opt
memory; opt
techmap; opt
abc -fast; opt
clean
setundef -zero
write_verilog -noattr synth/prolead/circuit_v14c.v
""",
}

for name, ys in variants.items():
    (BUNDLE / "synth" / f"_{name}.ys").write_text(ys)
    print(f"\n=== {name} ===")
    r = subprocess.run(["wsl", "-d", "Ubuntu", "-u", "root", "bash", "-c",
                        f"cd '{wsl_path}' && yosys -q synth/_{name}.ys 2>&1 | tail -3"],
                       capture_output=True, text=True, timeout=180)
    print(f"  yosys exit: {r.returncode}")
    out = BUNDLE / "synth" / "prolead" / f"circuit_{name}.v"
    if out.exists():
        text = out.read_text(errors="replace")
        dff_cells = set(re.findall(r'\$_(?:SDFF|DFF|DFFE|SDFFE)\w*', text))
        n_reg = len(re.findall(r'\breg\b\s*\[', text))
        n_wire = len(re.findall(r'\bwire\b\s*\[', text))
        n_assign = text.count("assign")
        m = re.search(r"input\s*\[(\d+):(\d+)\]\s*randomIn", text)
        width = (int(m.group(1)) - int(m.group(2)) + 1) if m else 0
        print(f"  file: {out.stat().st_size} B, randomIn: {width//8}B, DFF: {dff_cells}, reg[: {n_reg}, wire[: {n_wire}, assign: {n_assign}")

# Try PROLEAD on v14a (flatten + setundef + extra opt clean)
print(f"\n=== PROLEAD test on v14 variants ===")
for name in variants:
    result_dir = BUNDLE / "sim" / f"prolead_init_{name}"
    if result_dir.exists():
        shutil.rmtree(result_dir)
    result_dir.mkdir(parents=True, exist_ok=True)
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{BUNDLE}:/work",
        "prolead-masked-aes:latest",
        "bash", "-c",
        f"cd /work && /opt/PROLEAD/release/PROLEAD "
        f"--designfile=synth/prolead/circuit_{name}.v "
        f"--configfile=synth/config_init_7b.json "
        f"--resultfolder=/work/sim/prolead_init_{name} "
        f"--libraryfile=synth/library_yosys.json "
        f"--libraryname=custom"
    ]
    r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
    if r.returncode == 0:
        print(f"  {name}: PROLEAD OK! exit=0")
        for line in r.stdout.split("\n"):
            if any(s in line for s in ["matched", "extended", "placable", "initialized", "applied", "Probing", "Standard", "Probes"]):
                print(f"    {line[:200]}")
    else:
        # Find the error
        for line in r.stderr.split("\n"):
            if "what()" in line or "Error" in line:
                print(f"  {name}: {line[:200]}")
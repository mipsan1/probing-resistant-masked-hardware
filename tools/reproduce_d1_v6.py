"""Try PROLEAD with circuit_struct_attr.v (6 bytes, d=1 legacy) and config adjusted."""
import subprocess
import json
import time
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
circuit = BUNDLE / "synth" / "prolead_d1_candidate_attr.v"  # 6 bytes, 7/19 13:24

# Build a config that matches this netlist: randomIn[47:0] (6 bytes), 19 cycles
cfg = {
    "performance": {
        "max_number_of_threads": "half",
        "minimize_probing_sets": "aggressive",
        "number_of_entries_in_report": 10
    },
    "simulation": {
        "groups": ["8'h$$", "8'h00"],
        "number_of_clock_cycles": 19,
        "always_random_inputs": ["randomIn[47:0]"],
        "output_shares": ["sboxOut[7:0]", "sboxOut[15:8]"],
        "expected_output": ["8'h$$", "8'h63"],
        "input_sequence": [
            {
                "signals": [
                    {"name": "sboxIn[7:0]", "value": "group_in0[7:0]"},
                    {"name": "sboxIn[15:8]", "value": "group_in1[7:0]"}
                ]
            }
        ],
        "number_of_simulations": 16000,  # smoke
        "number_of_simulations_per_step": 16000,
        "number_of_simulations_per_write": 16000
    },
    "hardware": {"clock_signal_name": "clk"},
    "side_channel_analysis": {"order": 1, "transitional_leakage": True}
}
cfg_path = BUNDLE / "synth" / "config_smoke_6b_d1.json"
cfg_path.write_text(json.dumps(cfg, indent=2))

# Clean
result_dir = BUNDLE / "sim" / "prolead_d1_repro_6b_2026-10-12"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)

print(f"=== PROLEAD smoke test on circuit_struct_attr.v (6 bytes, d=1) ===")
print(f"  netlist: prolead_d1_candidate_attr.v ({circuit.stat().st_size} B)")
print(f"  config: randomIn[47:0] (6 bytes), 19 cycles, 16k sims")

docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    "cd /work && /opt/PROLEAD/release/PROLEAD "
    "--designfile=synth/prolead_d1_candidate_attr.v "
    "--configfile=synth/config_smoke_6b_d1.json "
    "--resultfolder=/work/sim/prolead_d1_repro_6b_2026-10-12 "
    "--libraryfile=synth/library_yosys.json "
    "--libraryname=custom"
]
t0 = time.time()
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
elapsed = time.time() - t0
print(f"  exit: {r.returncode}  elapsed: {elapsed:.1f}s")
# Show relevant
for line in r.stdout.split("\n"):
    if any(s in line for s in ["Successfully", "Probing", "Elapsed", "Standard", "Output", "Error", "FATAL", "logic_error"]):
        print(f"    {line[:200]}")
if r.returncode != 0:
    print(f"  stderr (last 15):")
    for line in r.stderr.split("\n")[-15:]:
        print(f"    {line[:200]}")

leak_files = list(result_dir.glob("prolead_*_leakages.json"))
if leak_files:
    rep = json.loads(leak_files[0].read_text())
    print(f"\n  result: sims={rep.get('number_of_simulations')}, sets={rep.get('total_number_of_probing_sets')}, leaking={rep.get('number_of_leaking_probing_sets')}")
    top = rep.get("most_leaking_probing_sets_in_total", [])
    if top:
        print(f"  worst -log10(p): {top[0].get('-log10(p)')}")
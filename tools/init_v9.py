"""Run PROLEAD init on v9 netlist with extended library to generate prolead_circuit_probes.json."""
import subprocess
import shutil
import time
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
result_dir = BUNDLE / "sim" / "prolead_init_v9"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)

# Use a config that aborts simulation early (very small sims) but completes init
cfg = {
    "performance": {
        "max_number_of_threads": "half",
        "minimize_probing_sets": "aggressive",
        "number_of_entries_in_report": 10
    },
    "simulation": {
        "groups": ["8'h$$", "8'h00"],
        "number_of_clock_cycles": 19,
        "always_random_inputs": ["randomIn[55:0]"],
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
        "number_of_simulations": 256,
        "number_of_simulations_per_step": 256,
        "number_of_simulations_per_write": 256
    },
    "hardware": {"clock_signal_name": "clk"},
    "side_channel_analysis": {"order": 1, "transitional_leakage": True}
}
cfg_path = BUNDLE / "synth" / "config_init_256_d1.json"
import json
cfg_path.write_text(json.dumps(cfg, indent=2))

print("=== PROLEAD init on v9 netlist (extended library, 256 sims abort) ===")
docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v9.v "
    f"--configfile=synth/config_init_256_d1.json "
    f"--resultfolder=/work/sim/prolead_init_v9 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
t0 = time.time()
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
elapsed = time.time() - t0
print(f"  exit: {r.returncode}, elapsed: {elapsed:.1f}s")
print(f"\n=== PROLEAD stdout ===")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"\n=== PROLEAD stderr ===")
    for line in r.stderr.split("\n"):
        print(f"  {line[:200]}")

# Inspect result
probes_file = result_dir / "prolead_circuit_probes.json"
if probes_file.exists():
    print(f"\n=== prolead_circuit_probes.json ===")
    print(f"  file: {probes_file.stat().st_size} B")
    import json
    data = json.loads(probes_file.read_text())
    if "placed_probes" in data:
        print(f"  placed_probes count: {len(data['placed_probes'])}")
    if "extended_probes" in data:
        print(f"  extended_probes count: {len(data['extended_probes'])}")
    if "extensions" in data:
        print(f"  extensions count: {len(data['extensions'])}")
else:
    print(f"\n  ! no probes file generated")
"""Re-run PROLEAD with very small sims_per_write to capture the initialization step
output and compare to 7/19 17:29 stdout (15200 probes, 14400 sets, 56 fresh masks)."""
import subprocess
import json
import re
import shutil
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")

# Try multiple netlists to find the one that matches 7/19 17:29 numbers
candidates = [
    ("current_7bytes", BUNDLE / "synth" / "prolead" / "circuit.v"),
    ("legacy_6bytes_attr", BUNDLE / "synth" / "prolead_d1_candidate_attr.v"),
    ("legacy_6bytes_noattr", BUNDLE / "synth" / "prolead" / "circuit_no_noexpr.v"),
    ("current_7bytes_no_flatten", BUNDLE / "synth" / "prolead" / "circuit_no_flatten.v"),
]

# Use small sims_per_write so PROLEAD aborts early in simulation but prints
# full initialization diagnostics
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
        "number_of_simulations": 1024,
        "number_of_simulations_per_step": 1024,
        "number_of_simulations_per_write": 1024
    },
    "hardware": {"clock_signal_name": "clk"},
    "side_channel_analysis": {"order": 1, "transitional_leakage": True}
}
# Config with 6 bytes randomIn (for 6-byte netlists)
cfg_6b = json.loads(json.dumps(cfg))
cfg_6b["simulation"]["always_random_inputs"] = ["randomIn[47:0]"]

# Save both configs
cfg_7b_path = BUNDLE / "synth" / "config_init_7b.json"
cfg_6b_path = BUNDLE / "synth" / "config_init_6b.json"
cfg_7b_path.write_text(json.dumps(cfg, indent=2))
cfg_6b_path.write_text(json.dumps(cfg_6b, indent=2))

reference = """[7/19 17:29:27] Successfully read design file with topmodule "circuit"!
[7/19 17:29:27] Successfully matched 56 fresh mask signals...
[7/19 17:29:28] Successfully detected 1475521 possible probes in total.
[7/19 17:29:29] Successfully extended 15200 placable probes in total.
[7/19 17:29:30] Successfully placed 16872 possible extensions in total.
[7/19 17:29:31] Successfully initialized a univariate evaluation with 15200 probing sets.
[7/19 17:29:32] Successfully set a batch of 15200 probing sets.
[7/19 17:29:32] Successfully applied probing set minimization. 800 covered probing sets removed.
[7/19 17:29:32] | #Standard Probes | #Extended Probes | #Probing Sets | ...
[7/19 17:29:32] |            15200 |            16872 |         14400 |                       2 |                      38 |               15.720000 |"""
print("=== Reference (7/19 17:29:27-32) ===")
print(reference)
print()

for name, netlist in candidates:
    if not netlist.exists():
        print(f"\n=== {name}: SKIP (no netlist) ===")
        continue
    # Pick config based on netlist characteristics
    if "noexpr" in str(netlist).lower() or "candidate" in str(netlist).lower():
        cfg_path = cfg_6b_path
    else:
        cfg_path = cfg_7b_path
    print(f"\n=== {name}: {netlist.name} ({netlist.stat().st_size} B), config: {cfg_path.name} ===")

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
        f"--designfile={netlist.relative_to(BUNDLE).as_posix()} "
        f"--configfile={cfg_path.relative_to(BUNDLE).as_posix()} "
        f"--resultfolder=/work/{result_dir.relative_to(BUNDLE).as_posix()} "
        f"--libraryfile=synth/library_yosys.json "
        f"--libraryname=custom"
    ]
    r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=600)
    # Show init-relevant lines
    for line in r.stdout.split("\n"):
        if any(s in line for s in ["Successfully", "Error", "FATAL", "logic_error", "Standard Probes", "Probing Sets"]):
            print(f"  {line[:200]}")
    if r.returncode != 0:
        print(f"  stderr (last 5):")
        for line in r.stderr.split("\n")[-5:]:
            print(f"    {line[:200]}")
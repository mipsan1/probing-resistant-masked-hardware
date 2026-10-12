"""Full PROLEAD run on v9 xform2 netlist: 512000 simulations, 19 cycles, d=1, aggressive minimize.

Mirrors 7/19 17:50:36 run but uses the current RTL synth (v9) with xform2
post-processing (primitive name + assign line normalization)."""
import subprocess
import json
import shutil
import time
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")

# Mirror 7/19 config exactly
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
        "number_of_simulations": 512000,
        "number_of_simulations_per_step": 128000,
        "number_of_simulations_per_write": 512000
    },
    "hardware": {"clock_signal_name": "clk"},
    "side_channel_analysis": {"order": 1, "transitional_leakage": True}
}
cfg_path = BUNDLE / "synth" / "config_full_v9.json"
cfg_path.write_text(json.dumps(cfg, indent=2))
print(f"Wrote config: {cfg_path} ({cfg_path.stat().st_size} B)")

# Result dir
result_dir = BUNDLE / "sim" / "prolead_full_v9"
if result_dir.exists():
    shutil.rmtree(result_dir)
result_dir.mkdir(parents=True, exist_ok=True)

# Use the xform2 netlist (primitives + assign lines removed)
netlist = BUNDLE / "synth" / "prolead" / "circuit_v9_xform2.v"
print(f"Netlist: {netlist} ({netlist.stat().st_size} B)")

print(f"\n=== PROLEAD full run (512K sims, mirrors 7/19 17:50:36) ===")
print(f"  command:")
print(f"    --designfile=synth/prolead/circuit_v9_xform2.v")
print(f"    --configfile=synth/config_full_v9.json")
print(f"    --resultfolder=sim/prolead_full_v9")
print(f"    --libraryfile=synth/library_yosys.json")
print(f"    --libraryname=custom")
print()
print(f"  expected: ~10-20 min wall time on 8-thread Docker")

docker_cmd = [
    "docker", "run", "--rm",
    "-v", f"{BUNDLE}:/work",
    "prolead-masked-aes:latest",
    "bash", "-c",
    f"cd /work && /opt/PROLEAD/release/PROLEAD "
    f"--designfile=synth/prolead/circuit_v9_xform2.v "
    f"--configfile=synth/config_full_v9.json "
    f"--resultfolder=/work/sim/prolead_full_v9 "
    f"--libraryfile=synth/library_yosys.json "
    f"--libraryname=custom"
]
print(f"  docker: {' '.join(docker_cmd[:6])} ... {docker_cmd[-2][:60]}")
t0 = time.time()
r = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=3600)
elapsed = time.time() - t0
print(f"\n  exit: {r.returncode}, elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")

# Show PROLEAD stdout
print(f"\n=== PROLEAD stdout ===")
for line in r.stdout.split("\n"):
    print(f"  {line[:200]}")
if r.returncode != 0:
    print(f"\n=== PROLEAD stderr (last 30) ===")
    for line in r.stderr.split("\n")[-30:]:
        print(f"  {line[:200]}")

# Inspect
leak_files = list(result_dir.glob("prolead_*_leakages.json"))
probes_files = list(result_dir.glob("prolead_*_probes.json"))
print(f"\n=== Result files ===")
print(f"  leakages JSON: {len(leak_files)}")
for f in leak_files:
    print(f"    {f.name} ({f.stat().st_size} B)")
print(f"  probes JSON: {len(probes_files)}")
for f in probes_files:
    print(f"    {f.name} ({f.stat().st_size} B)")

if leak_files:
    print(f"\n=== Result ===")
    rep = json.loads(leak_files[0].read_text())
    print(f"  sims: {rep.get('number_of_simulations')}")
    print(f"  total sets: {rep.get('total_number_of_probing_sets')}")
    print(f"  leaking: {rep.get('number_of_leaking_probing_sets')}")
    top = rep.get("most_leaking_probing_sets_in_total", [])
    if top:
        max_v = top[0].get("-log10(p)")
        print(f"  worst -log10(p): {max_v}")
        # Bonferroni threshold
        n_sets = int(rep.get("total_number_of_probing_sets", 0))
        if n_sets:
            import math
            bonf = -math.log10(0.05/n_sets)
            print(f"  Bonferroni threshold: {bonf:.4f}")

# Save result to historical evidence too
if leak_files:
    import shutil
    dst_dir = BUNDLE / "docs" / "historical_evidence" / "v9_reproduction"
    dst_dir.mkdir(exist_ok=True)
    for f in leak_files:
        shutil.copy2(f, dst_dir / f.name)
    for f in probes_files:
        shutil.copy2(f, dst_dir / f.name)
    print(f"\n  copied to: {dst_dir}")
"""Verify that 7/19 PROLEAD's 14,400 set / 15,200 probe numbers
match netlist_d1_reproduction.json (8959 sets)."""
import json
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
data = json.loads((BUNDLE / "netlist_d1_reproduction.json").read_text())

n_rings = sum(1 for k in data if k.startswith("ring_"))
n_pairs = sum(1 for k in data if k.startswith("pair_"))
n_singles = sum(1 for k in data if k.startswith("single_"))
print(f"From netlist_d1_reproduction.json:")
print(f"  rings: {n_rings}")
print(f"  pairs: {n_pairs}")
print(f"  singles: {n_singles}")
print(f"  total: {n_rings + n_pairs + n_singles}")

# 7/19 reference
print(f"\n7/19 17:50:36 (run_full_progress.log):")
print(f"  sets: 14400")
print(f"  worst -log10(p) stdout: 4.205497")

# Interpretation
print(f"\n===")
print(f"8959 ≠ 14400 → netlist_d1_reproduction.json is from a different PROLEAD run")
print(f"  (possibly 7/19 'aggressive' minimize or smoke)")
print(f"  Or it's the 7/19 run with 15200 probes before minimization to 14400")
print(f"  (15200 - 8959 = 6241 ≈ -800 removed by minimization not exactly match)")
print(f"")
print(f"  Rings/pairs/singles total = {n_rings + n_pairs + n_singles}")
print(f"  If each ring is 1 set, each pair is 1 set, each single is 1 set → {n_rings + n_pairs + n_singles} sets")
print(f"  But 7/19 reported 14400 after minimization (15200 - 800)")
print(f"  → Each 'ring' might map to multiple probe sets, not 1:1")
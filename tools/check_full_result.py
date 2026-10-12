import json
import math
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
data = json.loads((BUNDLE / "sim/prolead_full_v9/prolead_circuit_0_0_512000_leakages.json").read_text())
print(f"sims: {data['number_of_simulations']}")
print(f"total sets: {data['total_number_of_probing_sets']}")
print(f"leaking: {data['number_of_leaking_probing_sets']}")
top = data.get("most_leaking_probing_sets_in_total", [])
if top:
    max_v = top[0].get("-log10(p)")
    print(f"worst -log10(p): {max_v}")
n = int(data["total_number_of_probing_sets"])
bonf = -math.log10(0.05/n)
print(f"Bonferroni threshold: {bonf:.4f}")
print(f"  => {max_v} < {bonf:.4f} = {'SECURE' if max_v < bonf else 'LEAK'}")
# Compare with 7/19
print()
print(f"=== 7/19 reference (17:50:36) ===")
print(f"  sims: 512000")
print(f"  sets: 14400")
print(f"  leaking: 0")
print(f"  worst stdout -log10(p): 4.205497")
print(f"  worst JSON max_log10p: 3.386122")
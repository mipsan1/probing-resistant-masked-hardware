"""Fix smoke config: number_of_simulations must be int, not string."""
import json
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
cfg = BUNDLE / "synth" / "config_smoke_d1.json"
data = json.loads(cfg.read_text())
data["simulation"]["number_of_simulations"] = 16000
data["simulation"]["number_of_simulations_per_step"] = 16000
data["simulation"]["number_of_simulations_per_write"] = 16000
cfg.write_text(json.dumps(data, indent=2))
print(f"Updated: {cfg}")
print(f"  number_of_simulations: {data['simulation']['number_of_simulations']} (type {type(data['simulation']['number_of_simulations']).__name__})")
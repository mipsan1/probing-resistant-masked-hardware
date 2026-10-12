"""Hard-rewrite config_smoke_d1.json: all number_of_* as bare ints."""
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
cfg = BUNDLE / "synth" / "config_smoke_d1.json"
text = cfg.read_text()
# Replace any "16000" with 16000 (no quotes)
text = text.replace('"16000"', '16000')
text = text.replace('"8000"', '8000')
text = text.replace('"4000"', '4000')
cfg.write_text(text)
print(f"Updated: {cfg}")
# Verify
import json
d = json.loads(cfg.read_text())
sim = d["simulation"]
print(f"  number_of_simulations: {sim['number_of_simulations']} (type {type(sim['number_of_simulations']).__name__})")
print(f"  number_of_clock_cycles: {sim['number_of_clock_cycles']} (type {type(sim['number_of_clock_cycles']).__name__})")
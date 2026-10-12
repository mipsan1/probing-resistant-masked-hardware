"""Force-fix config_smoke_d1.json: 16000 as bare int."""
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
cfg = BUNDLE / "synth" / "config_smoke_d1.json"
text = cfg.read_text()
text = text.replace('"number_of_simulations": "16000"', '"number_of_simulations": 16000')
text = text.replace('"number_of_simulations_per_step": "16000"', '"number_of_simulations_per_step": 16000')
text = text.replace('"number_of_simulations_per_write": "16000"', '"number_of_simulations_per_write": 16000')
cfg.write_text(text)
import json
d = json.loads(cfg.read_text())
sim = d['simulation']
print(f"  number_of_simulations: {sim['number_of_simulations']!r} ({type(sim['number_of_simulations']).__name__})")
print(f"  number_of_simulations_per_step: {sim['number_of_simulations_per_step']!r} ({type(sim['number_of_simulations_per_step']).__name__})")
print(f"  number_of_simulations_per_write: {sim['number_of_simulations_per_write']!r} ({type(sim['number_of_simulations_per_write']).__name__})")
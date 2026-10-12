from pathlib import Path
import re
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead_d1_candidate_attr.v").read_text(errors="replace")
dff_cells = set(re.findall(r'\$_(?:SDFF|DFF|DFFE|SDFFE)\w*', text))
print(f"DFF cell types in 7/19 13:24 netlist: {dff_cells}")
print(f"DFFE count: {text.count('DFFE')}")
print(f"DFF_ count: {text.count('DFF_')}")
print(f"SDFF count: {text.count('SDFF')}")
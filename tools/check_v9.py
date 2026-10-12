from pathlib import Path
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9.v").read_text(errors="replace")
import re
cells = set(re.findall(r'\$_\w+', text))
print("$_ cells:", sorted(cells))
n_xnor = text.lower().count("xnor")
print(f"xnor mentions (case-insensitive): {n_xnor}")
# Find lines with $_XNOR
for m in re.finditer(r'.*\$_XNOR\w*.*', text):
    print(m.group()[:200])
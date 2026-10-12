from pathlib import Path
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
data = Path(p).read_bytes()
# Find all "comprises" instances
import re
for m in re.finditer(rb'comprises', data):
    pos = m.start()
    # Show context
    ctx = data[max(0,pos-30):pos+15]
    print(f"comprises at {pos}: ...{ctx}...")
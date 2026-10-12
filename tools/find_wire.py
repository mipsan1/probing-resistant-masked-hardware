from pathlib import Path
import re
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9_xform2.v").read_text(errors="replace")
# Find wire[ patterns
matches = list(re.finditer(r"wire\[(\d+):(\d+)\]", text))
print(f"matches: {len(matches)}")
for m in matches[:5]:
    print(f"  {m.group()}")
# Look for the wire I just added
for m in re.finditer(r"zero_const_32", text):
    print(f"  zero_const_32 at {m.start()}: {text[max(0,m.start()-30):m.end()+30]!r}")
from pathlib import Path
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9_xform.v").read_text(errors="replace")
lines = text.split("\n")
for i, l in enumerate(lines):
    if "32'h00000000" in l:
        print(f"line {i}: {l[:200]}")
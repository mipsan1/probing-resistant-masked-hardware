from pathlib import Path
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead_d1_candidate_attr.v").read_text(errors="replace")
print(f"xnor lowercase: {text.count('xnor')}")
print(f"XNOR uppercase: {text.count('XNOR')}")
print(f"$_XNOR_ count: {text.count('$_XNOR_')}")
print(f"$_XOR_ count: {text.count('$_XOR_')}")
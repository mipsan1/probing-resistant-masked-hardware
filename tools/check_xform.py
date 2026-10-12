from pathlib import Path
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9_xform.v").read_text(errors="replace")
idx = text.find("NOT")
ctx = text[max(0,idx-5):idx+10]
print(f"NOT context: {ctx!r}")
raw = ctx.encode("utf-8")
print(f"raw bytes: {raw!r}")
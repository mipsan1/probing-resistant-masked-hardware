from pathlib import Path
text = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\synth\prolead\circuit_v9_xform.v").read_text(errors="replace")
# Find 32'h00000000 or its xform
for needle in [b"32'h00000000", b"32'b0", b"1'b0"]:
    idx = text.encode("utf-8").find(needle)
    print(f"{needle}: at {idx}")
    if idx >= 0:
        # Show context
        ctx = text[max(0,idx-80):idx+150]
        print(f"  context: {ctx!r}")
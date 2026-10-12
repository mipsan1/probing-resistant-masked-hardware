from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"
data = TEX.read_bytes()

# Just find "comprises" and try variations
needle = b"comprises\r\nreports"
print(f"Needle: {needle!r}, len={len(needle)}, count={data.count(needle)}")

# Try with single \
OLD = b"(\\texttt{syn/prolead/circuit\\_d2\\_struct.v}) comprises\r\nreports"
print(f"OLD: {OLD!r}, len={len(OLD)}")
# Compare against actual bytes around offset 74297
actual = data[74297-49:74297+10]
print(f"Actual (around comprises): {actual!r}")
print(f"Actual hex: {actual.hex()}")
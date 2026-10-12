from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"
data = TEX.read_bytes()

# Fix: L1343 starts with "5{,}536$..." -- should be "$25{,}536$..."
OLD = b"instantiates the following fixed probe set on the post-barrier netlist:\r\n5{,}536$"
NEW = b"instantiates the following fixed probe set on the post-barrier netlist:\r\n$25{,}536$"
print(f"OLD: {OLD!r}, len={len(OLD)}, occurrences={data.count(OLD)}")
if data.count(OLD) != 1:
    raise SystemExit("Expected exactly 1")
new_data = data.replace(OLD, NEW, 1)
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
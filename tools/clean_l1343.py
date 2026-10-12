from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"
data = TEX.read_bytes()

# Use raw bytes literal with single backslashes where the file has single backslashes.
# JSON source uses 2 backslashes for 1 actual backslash in the python bytes.
# So "\\\\texttt" in JSON -> "\\\\texttt" Python source -> b"\\\\texttt" bytes = "\\texttt" (2 actual \)
# That's wrong because file has "\texttt" (1 actual \).
# Need: 1 actual \ in bytes -> in JSON source: "\\\\\\\\" = 4 chars -> Python sees 2 chars "\\" -> bytes 1 \
# Simpler: use the file extraction approach
needle = b"batch).  The netlist"
idx = data.find(needle)
OLD = data[idx:idx+72]  # The whole orphan line + newline
print(f"OLD: {OLD!r}, len={len(OLD)}, occurrences={data.count(OLD)}")
# Replace with clean sentence
NEW = b"batch).  The PROLEAD configuration instantiates the following fixed probe set on the post-barrier netlist:\r\n"
if data.count(OLD) != 1:
    raise SystemExit("Expected exactly 1")
new_data = data.replace(OLD, NEW, 1)
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
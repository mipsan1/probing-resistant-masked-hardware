from pathlib import Path
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
data = Path(p).read_bytes()
# Find batch).  The netlist
needle = b"batch).  The netlist"
idx = data.find(needle)
print(f"needle at {idx}")
print(f"50 bytes after: {data[idx:idx+80]!r}")

# Find unique paren-close before "circuit_d2_struct.v"
target = b"circuit\\_d2\\_struct.v}"
idx2 = data.find(target)
print(f"target at {idx2}")
# Show 60 bytes before
print(f"60 before / 30 after: {data[idx2-60:idx2+30]!r}")
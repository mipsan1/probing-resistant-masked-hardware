from pathlib import Path
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
data = Path(p).read_bytes()

# Find "comprises" and show 100 bytes before/after
idx = data.find(b"comprises")
print(f"comprises at offset {idx}")
print(f"60 bytes before to 20 after:")
chunk = data[idx-60:idx+20]
print(f"Hex: {chunk.hex()}")
print(f"Repr: {chunk!r}")

# Try matching the actual bytes
needle1 = data[idx-50:idx+13]  # everything from 50 back through "comprises"
print(f"\nactual 50-prefix: {needle1!r}")
print(f"occurrences: {data.count(needle1)}")

# Now construct OLD exactly
OLD = data[idx-50:idx] + b"\r\nreports"
print(f"\nConstructed OLD: {OLD!r}")
print(f"occurrences: {data.count(OLD)}")
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
with open(p, 'rb') as f:
    data = f.read()
idx = data.find(b'comprises')
print(f"'comprises' at offset {idx}")
# Show bytes around it
chunk = data[idx:idx+30]
print(f"Bytes: {chunk!r}")
print(f"Hex: {chunk.hex()}")
# Try variations
print(f"\nSearching various forms:")
for s in [b"comprises\r\nreports", b"comprises\nreports", b"comprises\reports", b"comprises reports"]:
    print(f"  {s!r}: {data.count(s)}")
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
with open(p, 'rb') as f:
    data = f.read()

# Find "(circuit_d2_struct.v}) comprises" - the L1343 line
needle = b'circuit\\_d2\\_struct.v}) comprises'
idx = data.find(needle)
print(f"Marker at offset {idx}, len={len(needle)}")

# Capture 8 lines starting from the "("
start = data.rfind(b'(', 0, idx)
print(f"Start '(' at offset {start}")

# Read 8 lines
end = start
for _ in range(8):
    nl = data.find(b'\r\n', end)
    if nl < 0:
        break
    end = nl + 2
print(f"Range: {start} - {end}")
chunk = data[start:end]
print(repr(chunk))
print(f"\nLength: {len(chunk)} bytes")
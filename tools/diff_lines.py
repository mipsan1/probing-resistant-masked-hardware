p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
with open(p, 'rb') as f:
    data = f.read()

# Find the 25,536 marker and extract surrounding lines
marker = b'$25{,}536$ standard probes'
idx = data.find(marker)
print(f"Marker at offset {idx}")
# Go back to start of that line
line_start = data.rfind(b'\r\n', 0, idx) + 2
# Read next 5 lines
end = line_start
lines = []
for _ in range(8):
    nl = data.find(b'\r\n', end)
    if nl < 0:
        break
    lines.append(data[end:nl])
    end = nl + 2

print("\nActual lines from data:")
for i, line in enumerate(lines):
    print(f"  {i}: {line!r}")
    print(f"     hex: {line[:60].hex()}")
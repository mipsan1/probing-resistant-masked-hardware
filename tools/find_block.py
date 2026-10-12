p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
with open(p, 'rb') as f:
    data = f.read()

# Show 8 lines starting at offset 74259 (which is what the hex dump showed as the start of "comprises\r\n$25{,}536...")
start = 74259
end = start
for _ in range(8):
    nl = data.find(b'\r\n', end)
    if nl < 0:
        break
    end = nl + 2
print(f"Range: {start} - {end}")
print(f"Bytes ({end-start}):")
chunk = data[start:end]
print(repr(chunk))
import sys
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
with open(p, 'rb') as f:
    data = f.read()
# Find the 25,536 block
needle = b'25{,}536'
idx = data.find(needle)
print(f'First match at offset {idx}')
chunk = data[idx-50:idx+800]
for i in range(0, len(chunk), 64):
    line = chunk[i:i+64]
    hexs = ' '.join(f'{b:02x}' for b in line)
    asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in line)
    print(f'{idx-50+i:6d} | {hexs}')
    print(f'         | {asc}')
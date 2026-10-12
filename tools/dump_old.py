from pathlib import Path
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
data = Path(p).read_bytes()
needle = b"batch).  The netlist"
idx = data.find(needle)
chunk = data[idx:idx+72]
print(f"Bytes ({len(chunk)}): {chunk!r}")
print(f"Hex: {chunk.hex()}")
# Test OLD
OLD = b"batch).  The netlist\r\n(\\\\texttt{syn/prolead/circuit\\\\_d2\\\\_struct.v}) \r\n"
print(f"\nOLD: {OLD!r}, len={len(OLD)}")
print(f"OLD hex: {OLD.hex()}")
print(f"OLD count: {data.count(OLD)}")
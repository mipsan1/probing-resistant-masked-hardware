import sys
p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
with open(p, 'rb') as f:
    data = f.read()

OLD = (
    "(\\texttt{syn/prolead/circuit\\_d2\\_struct.v}) comprises\r\n"
    "$25{,}536$ standard probes (extended $29{,}184$), so the\r\n"
    "na\\\"ive order-2 probing space is $25{,}536 \\times $25{,}535 / 2\r\n"
    "\\approx 3.26 \\times 10^{8}$ sets.  PROLEAD's\r\n"
    "\\texttt{minimize\\_probing\\_sets: trivial} reduces the\r\n"
    "distinct same-cycle univariate-2 probe-pair space to\r\n"
    "$17{,}157$ unique sets (which is the figure reported below as\r\n"
    "N).  \\textit{Note:} an early $4$-batch pre-sweep flagged $4$ sets because the \\texttt{expected\\_output} field of that configuration was set incorrectly; the corrected configuration and the full sweep below supersede it.\r\n"
)

old_bytes = OLD.encode("utf-8")
print(f"OLD bytes length: {len(old_bytes)}")
print(f"Occurrences in data: {data.count(old_bytes)}")
# Show first 200 bytes of OLD
print("OLD hex dump (first 200):")
for i in range(0, min(200, len(old_bytes)), 32):
    line = old_bytes[i:i+32]
    hexs = " ".join(f"{b:02x}" for b in line)
    print(f"  {i:3d} | {hexs}")
# If 0 occurrences, find where the difference starts
if data.count(old_bytes) == 0:
    # Try shorter prefix to find mismatch
    for n in range(len(old_bytes), 50, -10):
        prefix = old_bytes[:n]
        if data.count(prefix):
            print(f"Prefix of {n} bytes matches 0")
            break
    else:
        print("No matching prefix found, checking per-line:")
        for i, line in enumerate(OLD.split("\r\n")):
            lb = line.encode("utf-8")
            print(f"  Line {i} ({len(lb)}B): {data.count(lb)} occurrences")
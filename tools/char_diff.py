p = r'C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29\manuscript\manuscript.tex'
with open(p, 'rb') as f:
    data = f.read()

needle = b'circuit\\_d2\\_struct.v}) comprises'
idx = data.find(needle)
start = data.rfind(b'(', 0, idx)
end = start
for _ in range(8):
    nl = data.find(b'\r\n', end)
    end = nl + 2
actual = data[start:end]

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

print(f"actual len: {len(actual)}")
print(f"old_bytes len: {len(old_bytes)}")

# Char-by-char comparison
print("\nMismatches:")
for i in range(min(len(actual), len(old_bytes))):
    if actual[i] != old_bytes[i]:
        print(f"  pos {i}: actual={actual[i]:02x} ({chr(actual[i]) if 32<=actual[i]<127 else '?'}), old={old_bytes[i]:02x} ({chr(old_bytes[i]) if 32<=old_bytes[i]<127 else '?'})")
        # Show context
        s = max(0, i-20)
        e = min(len(actual), i+20)
        print(f"    actual context: {actual[s:e]!r}")
        s = max(0, i-20)
        e = min(len(old_bytes), i+20)
        print(f"    old context:    {old_bytes[s:e]!r}")
        break

if len(actual) != len(old_bytes):
    print(f"\nLength mismatch after {min(len(actual), len(old_bytes))} bytes")
    n = min(len(actual), len(old_bytes))
    print(f"  actual tail: {actual[n:]!r}")
    print(f"  old tail:    {old_bytes[n:]!r}")
from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"
data = TEX.read_bytes()

# The reference to "full $25,536 \times 25,535 / 2$" is misleading since that
# is the SYN-NETLIST space, not the Tier-3 placed space. The actual full
# Tier-3 same-cycle pair space (before minimization) is 6,384 x 6,383 / 2 =
# 20.4M. Fix that.
OLD = b"the full $25{,}536 \\times 25{,}535 / 2 \\approx 3.26 \\times 10^{8}$ sets"
NEW = b"the corresponding syn-netlist same-cycle pair space of $25{,}536 \\times 25{,}535 / 2 \\approx 3.26 \\times 10^{8}$ sets, nor the placed-Tier-3 pair space of $6{,}384 \\times 6{,}383 / 2 \\approx 2.04 \\times 10^{7}$"
print(f"OLD: {OLD!r}, occurrences={data.count(OLD)}")
if data.count(OLD) != 1:
    raise SystemExit("Expected exactly 1")
new_data = data.replace(OLD, NEW, 1)
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
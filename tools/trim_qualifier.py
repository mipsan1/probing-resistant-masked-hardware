from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"
data = TEX.read_bytes()

# Trim: remove standalone "PROLEAD's\r\n" line and trim qualifier end to merge
OLD = b"placed-Tier-3 pair space of $6{,}384 \\times 6{,}383 / 2 \\approx 2.04 \\times 10^{7}$.\r\nPROLEAD's\r\n"
NEW = b"placed-Tier-3 pair space of $6{,}384 \\times 6{,}383 / 2 \\approx 2.04 \\times 10^{7}$.  PROLEAD's\r\n"
print(f"OLD: {OLD!r}, occurrences={data.count(OLD)}")
if data.count(OLD) != 1:
    raise SystemExit("Expected exactly 1")
new_data = data.replace(OLD, NEW, 1)
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
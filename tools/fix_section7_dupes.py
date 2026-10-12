#!/usr/bin/env python3
"""Fix the residual duplicate lines from the §7 patch.

The first patch inserted a qualifier after L1343 but didn't remove the now-
replaced text "$25,536 standard probes (extended $29,184$), so the\n
naive order-2 probing space is $25,536 \times...PROLEAD's".

We now delete the 2 duplicate lines that the qualifier already covers.
"""
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"

# Find the duplicate pair. After the first patch, L1348 starts with
# "$25{,}536$ standard probes (extended $29{,}184$), so the" followed by
# "na\"ive order-2 probing space is $25{,}536 \\times 25{,}535 / 2" then
# "\\approx 3.26 \\times 10^{8}$ sets.  PROLEAD's".
DUP_OLD = (
    b"$25{,}536$ standard probes (extended $29{,}184$), so the\r\n"
    b"na\\\"ive order-2 probing space is $25{,}536 \\times 25{,}535 / 2\r\n"
    b"\\approx 3.26 \\times 10^{8}$ sets.  PROLEAD's\r\n"
)
# Replace with just "PROLEAD's" (already in qualifier end), but we need to
# keep the trailing \r\n because the next line starts the proper PROLEAD
# description. We want to leave the next line (\texttt{minimize\_probing\_sets: trivial})
# intact, so just delete the dupes entirely (the qualifier already says
# "PROLEAD's" as its last word, then the next line continues correctly).
DUP_NEW = b""

data = TEX.read_bytes()
count = data.count(DUP_OLD)
print(f"DUP block occurrences: {count}")
if count != 1:
    raise SystemExit(f"Expected 1, got {count}")

new_data = data.replace(DUP_OLD, DUP_NEW, 1)
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
#!/usr/bin/env python3
"""Apply §7 d=2 qualifier patch to manuscript.tex (UTF-8 CRLF)."""
from pathlib import Path
import sys

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"

# Build OLD by extracting the exact 8-line block from the file
data = TEX.read_bytes()
needle = b"circuit\\_d2\\_struct.v}) comprises"
idx = data.find(needle)
start = data.rfind(b"(", 0, idx)
end = start
for _ in range(8):
    nl = data.find(b"\r\n", end)
    end = nl + 2
OLD = data[start:end]
print(f"OLD block: {len(OLD)} bytes from offset {start}-{end}")

# New block: keep the original L1344-L1350 PROLEAD configuration reporting
# intact (lines 2..7 of OLD) but insert a 13-line qualifier BEFORE them that
# (a) clarifies the syn-netlist figures are separate from the Tier-3 config
# (b) explicitly states 42 families / 6,384 probes / 17,157 pairs
# (c) documents the single-share-index cone structural property.
INSERT_AFTER_LINE = 1  # after line 1 (the "$25{,}536 standard probes..." line), before "naive order-2..."

LINES = OLD.split(b"\r\n")
# Sanity: 9 segments (8 lines + trailing empty)
assert len(LINES) == 9, f"Expected 9 segments, got {len(LINES)}"

QUALIFIER = (
    b"reports\r\n"
    b"$25{,}536$ standard probes (extended $29{,}184$) at the gate level; this is a property of the synthesized structural netlist and does not constrain the Tier-3 PROLEAD configuration below, which is applied to the post-barrier design netlist.  The Tier-3 evaluation (\\texttt{prolead\\_results/tier3\\_d2\\_masked}) instantiates a fixed probe set of $42$ probe families over all $19$ clock cycles, totalling $6{,}384$ placed probes, and the same-cycle univariate-2 probe-pair space reduces to $17{,}157$ unique pairs.\r\n"
    b"\\textit{Probe-set structure.}  All $42$ probe families correspond to single-share-index cones after the register barriers: the three \\texttt{aff\\_inv} affine-network outputs, the $9$ diagonal multiplier products \\texttt{m{\\_}p00/p11/p22}, and the $30$ squarer share-products \\texttt{sq\\_x{\\_}s0..s6}.  Any same-cycle pair of placed probes therefore shares at most one share index, so the placed configuration is structurally incapable of exercising a cross-share $3$-share-index probe combination.  The flat $0/17{,}157$ verdict below reflects the structural coverage of the placed probe set and not an empirical statement about the full $25{,}536 \\times 25{,}535 / 2 \\approx 3.26 \\times 10^{8}$ sets.\r\n"
    b"PROLEAD's"
)
# We need to split the FIRST line (which currently ends in " comprises") and
# turn it into "comprises\r\n<reports $25,536...>" -- actually we just append
# the qualifier after the first line of OLD, keeping the rest.

# Replace the OLD block with: original 8 lines but with the qualifier inserted
# after line 0 (the "(...comprises" line).
new_lines = [LINES[0], QUALIFIER] + LINES[1:]
NEW = b"\r\n".join(new_lines)

print(f"NEW block: {len(NEW)} bytes")

new_data = data[:start] + NEW + data[end:]
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
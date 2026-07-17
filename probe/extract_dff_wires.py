#!/usr/bin/env python3
"""
extract_dff_wires.py

Parse a Yosys-synthesized Verilog netlist and extract:
  1. The names of all DFF Q wires (the LHS of every always @(posedge clk) block)
  2. The names of all DFF D wires (the RHS of the same blocks; these are
     the combinational stage outputs)

Yosys writes each register as a separate always block. When the block has
no reset, the body is one line: `Q <= D;`. When it has a reset, the body
is two lines:
    if (!rst_n) Q <= RST;
    else Q <= D;
Both forms are *not* wrapped in begin/end.

Usage:
  python3 extract_dff_wires.py <netlist.v> <output_prefix>
"""

import re
import sys

ELSE_ASSIGN = re.compile(r'else\s+(\S+)\s*<=\s*([^;]+);')
PLAIN_ASSIGN = re.compile(r'^\s*(\S+)\s*<=\s*([^;]+);', re.MULTILINE)
RESET_ASSIGN = re.compile(r'if\s*\(\s*!\s*rst_n\s*\)\s*(\S+)\s*<=')


def parse_netlist(path):
    """Yield (q_wire, d_expr) for every DFF in the netlist."""
    with open(path, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        # Start of a DFF block?
        if 'always' in line and 'posedge' in line:
            # Determine block length: 1 line (no reset) or 2 lines (with reset)
            j = i + 1
            block = [line]
            # Read body until next "always @" or end of file
            while j < len(lines) and 'always' not in lines[j]:
                block.append(lines[j])
                j += 1
            # Process this block
            yield from _process_block(block)
            i = j
        else:
            i += 1


def _process_block(block):
    body = ''.join(block[1:])  # skip the always line
    m = ELSE_ASSIGN.search(body)
    if m:
        yield (m.group(1).strip(), m.group(2).strip())
        return
    # No `else` branch — look for a single non-reset assignment after the
    # reset `if (!rst_n)` line
    in_reset = False
    for ln in block[1:]:
        s = ln.strip()
        if RESET_ASSIGN.search(ln):
            in_reset = True
            continue
        if in_reset and '<=' in s:
            m = PLAIN_ASSIGN.search(s)
            if m:
                yield (m.group(1).strip(), m.group(2).strip())
                return
    # Fallback: single non-reset assignment
    for ln in block[1:]:
        if '<=' in ln:
            m = PLAIN_ASSIGN.search(ln.strip())
            if m:
                yield (m.group(1).strip(), m.group(2).strip())
                return


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <netlist.v> <output_prefix>", file=sys.stderr)
        sys.exit(1)

    netlist_path = sys.argv[1]
    prefix = sys.argv[2]

    q_wires = set()
    d_wires = set()
    pairs = []

    for q, d in parse_netlist(netlist_path):
        q = q.strip()
        d = d.strip()
        if q:
            q_wires.add(q)
            d_wires.add(d)
            pairs.append((q, d))

    with open(f"{prefix}_q.txt", 'w') as f:
        for q in sorted(q_wires):
            f.write(q + '\n')

    with open(f"{prefix}_d.txt", 'w') as f:
        for d in sorted(d_wires):
            f.write(d + '\n')

    with open(f"{prefix}_stages.txt", 'w') as f:
        for q, d in pairs:
            f.write(f"{q} = {d}\n")

    print(f"Extracted {len(pairs)} DFF pairs from {netlist_path}")
    print(f"  -> {prefix}_q.txt        ({len(q_wires)} unique Q wires)")
    print(f"  -> {prefix}_d.txt        ({len(d_wires)} unique D wires)")
    print(f"  -> {prefix}_stages.txt  ({len(pairs)} DFFs)")


if __name__ == '__main__':
    main()

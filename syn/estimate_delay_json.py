#!/usr/bin/env python3
"""
estimate_delay_json.py
======================
Compute critical-path delay of a Yosys-flattened gate-level netlist
using a unit-delay model for the generic Yosys cell library.

Strategy: forward BFS relaxation.  Start with arrival = 0 on all
primary-input bits and DFF Q outputs.  Then iteratively propagate
arrival forward through combinational cells (in any order) until no
change.  The maximum arrival over DFF D inputs and primary outputs
is the critical-path delay.

1 unit ≈ 50 ps at 65 nm CMOS (typical 2-input NAND, fanout-of-4).

Also traces back the deepest DFF input's combinational fan-in cone
and prints the chain of cells, which lets the user identify the
sub-module (e.g.\ gf\_mul, gf\_exp) that is on the critical path.
"""
import json
import sys
from collections import defaultdict

DELAY = {
    "$_NOT_":     1,
    "$_BUF_":     1,
    "$_AND_":     1,
    "$_NAND_":    1,
    "$_OR_":      1,
    "$_NOR_":     1,
    "$_XOR_":     2,
    "$_XNOR_":    2,
    "$_ANDNOT_":  1,
    "$_ORNOT_":   1,
    "$_MUX_":     2,
    "$_NMUX_":    2,
    "$_AOI3_":    2,
    "$_OAI3_":    2,
    "$_AOI4_":    2,
    "$_OAI4_":    2,
}


def main(path):
    with open(path) as f:
        netlist = json.load(f)

    mod_name = next(
        k for k in netlist["modules"] if k != "manifest"
    )
    mod = netlist["modules"][mod_name]
    cells = mod["cells"]
    ports = mod["ports"]

    # Filter out $scopeinfo (these are not real gates)
    real = {c: ci for c, ci in cells.items() if ci["type"] != "$scopeinfo"}

    # ----- Arrival initialization -----
    arrival = {}

    for pname, pbits in ports.items():
        if pbits.get("direction") == "input":
            for b in pbits["bits"]:
                arrival[b] = 0

    for cname, c in real.items():
        if c["type"].startswith("$_DFF") or c["type"] == "$dff":
            for q in c["connections"].get("Q", []):
                arrival[q] = 0

    # ----- Forward propagation -----
    changed = True
    iters = 0
    while changed and iters < 1000:
        changed = False
        iters += 1
        for cname, c in real.items():
            ctype = c["type"]
            d = DELAY.get(ctype, 1)
            if ctype.startswith("$_DFF") or ctype == "$dff":
                d_bits = c["connections"].get("D", [])
                for db in d_bits:
                    a_in = arrival.get(db, 0)
                    if a_in > arrival.get(db, -1):
                        arrival[db] = a_in
            else:
                data_in = []
                for p, bits in c["connections"].items():
                    if p in ("Y", "Q", "O", "OUT"):
                        continue
                    data_in.extend(bits)
                if not data_in:
                    continue
                if not all(b in arrival for b in data_in):
                    continue
                a_in = max(arrival[b] for b in data_in)
                out_bits = c["connections"].get("Y", [])
                if not out_bits:
                    for p, bits in c["connections"].items():
                        if p in ("Y", "Q", "O", "OUT"):
                            out_bits = bits
                            break
                for ob in out_bits:
                    new_a = a_in + d
                    if new_a > arrival.get(ob, -1):
                        arrival[ob] = new_a
                        changed = True

    # ----- Critical path metrics -----
    dff_d = []
    for cname, c in real.items():
        ctype = c["type"]
        if ctype.startswith("$_DFF") or ctype == "$dff":
            for db in c["connections"].get("D", []):
                dff_d.append((db, arrival.get(db, 0), cname))
    po = []
    for pname, pbits in ports.items():
        if pbits.get("direction") == "output":
            for b in pbits["bits"]:
                po.append((b, arrival.get(b, 0), pname))

    crit = max(
        [a for _, a, _ in dff_d] +
        [a for _, a, _ in po] +
        [0]
    )

    # Cell breakdown
    cell_counts = {}
    for c in real.values():
        cell_counts[c["type"]] = cell_counts.get(c["type"], 0) + 1

    UNIT_PS = 50  # 50 ps per unit (typical 2-input NAND, 65 nm CMOS)
    print(f"Module: {mod_name}")
    print(f"Real cells: {len(real)}")
    for t in sorted(cell_counts, key=lambda x: -cell_counts[x]):
        print(f"  {t:18s} {cell_counts[t]:6d}")
    print()
    print(f"Critical-path delay: {crit} unit-delay")
    print(f"                    ≈ {crit * UNIT_PS / 1000:.1f} ns  (assuming {UNIT_PS} ps/unit, 65 nm CMOS)")
    print(f"                    ≈ {crit * UNIT_PS:.0f} ps")
    print()
    print("Top-5 deepest DFF data inputs (unit delay):")
    for w, a, c in sorted(dff_d, key=lambda x: -x[1])[:5]:
        print(f"  wire {w:8d}  {a:5d} units  ({a * UNIT_PS:.0f} ps)  (DFF: {c})")
    print()
    print("Top-5 deepest primary outputs (unit delay):")
    for w, a, p in sorted(po, key=lambda x: -x[1])[:5]:
        print(f"  {p:12s} wire {w:8d}  {a:5d} units  ({a * UNIT_PS:.0f} ps)")
    print()

    # ----- Traceback of the deepest combinational path -----
    if dff_d:
        target_w, target_a, target_c = max(dff_d, key=lambda x: x[1])
        print(f"Traceback of deepest DFF input (wire {target_w}, "
              f"{target_a} units, DFF = {target_c}):")
        # Build producer map
        producer = {}
        for cname, c in real.items():
            for p, bits in c["connections"].items():
                if p in ("Y", "Q", "O", "OUT"):
                    for b in bits:
                        producer[b] = cname
        # Walk back
        cur = target_w
        chain = [(cur, "D", target_c)]
        depth = 0
        while cur in producer and depth < target_a + 5:
            cname = producer[cur]
            ctype = real[cname]["type"]
            ins = {}
            for p, bits in real[cname]["connections"].items():
                if p in ("Y", "Q", "O", "OUT"):
                    continue
                ins[p] = bits
            data_in = []
            for p, bits in ins.items():
                if p in ("CLK", "C", "EN", "E", "ARST", "R", "SRST"):
                    continue
                if ctype.startswith("$_DFF") and p != "D":
                    continue
                data_in.extend(bits)
            if not data_in:
                break
            prev_w = max(data_in, key=lambda b: arrival.get(b, 0))
            chain.append((prev_w, ctype, cname))
            cur = prev_w
            depth += 1
        for w, t, c in reversed(chain):
            try:
                w_str = f"{w:8d}"
            except (TypeError, ValueError):
                w_str = str(w)
            try:
                c_short = str(c)[:30]
            except (TypeError, ValueError):
                c_short = "?"
            print(f"  wire {w_str}  <- {t:10s} ({c_short})")
    print()
    print(f"Convergence: {iters} iterations, "
          f"{'converged' if not changed else 'NOT converged'}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "syn/masked_aes_round1_flat.json"
    main(path)

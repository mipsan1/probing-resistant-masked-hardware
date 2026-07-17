#!/usr/bin/env python3
"""
estimate_delay.py
=================
Estimate critical-path delay of the gate-level netlist using a
unit-delay model for the generic Yosys/ABC cell library.

The model assumes each combinational gate contributes the following
relative delay (normalized to a 2-input NAND):

    gate             delay (units)   rationale
    ---------------  -------------   ----------------------------------
    $_NOT_           1               inverter
    $_AND_ / $_NAND_ 1               2-input
    $_OR_ / $_NOR_   1               2-input
    $_XOR_ / $_XNOR_ 2               2-input with internal carry
    $_MUX_           2               select + 2 paths
    $_ANDNOT_/$_ORNOT_ 1            AOI variant
    $_DFF_*_         0 (register)    no combinational contribution
    $_BUF_           1               wire/buffer

This is a coarse model.  The actual delay depends on the
technology library (drive strength, fanout, wire load).  For a 65 nm
CMOS standard-cell library, one "unit" corresponds to roughly 100 ps
(2-input NAND with 4x drive, fanout-of-4 load, typical wire).

To compute the critical path, we perform a topological traversal of
the synthesized netlist, starting at every DFF/Q output, walking the
combinational fanout cone, accumulating per-gate delay, and stopping
at the next DFF/D input or primary output.  The longest path is the
critical path.

Usage:
    yosys -s synth_round1.ys   # generates syn/masked_aes_round1_syn.v
    python3 syn/estimate_delay.py syn/masked_aes_round1_syn.v
"""
import os
import re
import sys
from collections import defaultdict, deque


# ----------------------------------------------------------------------------
# Per-cell unit delay
# ----------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------
# Parser for the yosys-emitted gate-level netlist.
#
# Format (example):
#     $_AND_ u1 (.A(a), .B(b), .Y(y));
#     $_DFFE_PN0P_ u2 (.D(d), .CLK(clk), .EN(en), .Q(q));
# ----------------------------------------------------------------------------
CELL_RE = re.compile(
    r"^\s*(\$\S+)\s+(\S+)\s*\((.*)\);", re.MULTILINE
)
PORT_RE = re.compile(r"\.(\w+)\s*\(\s*([^)]*?)\s*\)")
WIRE_RE = re.compile(r"\bwire\s+(?:\[[^\]]+\]\s+)?(\w+)\s*;")
INPUT_RE = re.compile(r"\binput(?:\s+\w+)?\s*(?:\[[^\]]+\]\s*)?(\w+)\s*;")
OUTPUT_RE = re.compile(r"\boutput(?:\s+\w+)?\s*(?:\[[^\]]+\]\s*)?(\w+)\s*;")


def parse_netlist(path):
    """Return (gates, dffs, primary_inputs, primary_outputs).

    gates  : dict cell_name -> {type, in_ports: {port: net}, out_port: net}
    dffs   : dict cell_name -> {clock, in, out}  (single-bit FFs only)
    primary_inputs, primary_outputs : set of net names
    """
    with open(path) as f:
        text = f.read()

    gates = {}
    dffs = {}
    primary_inputs = set()
    primary_outputs = set()

    for m in CELL_RE.finditer(text):
        cell_type, cell_name, port_str = m.groups()
        ports = dict(PORT_RE.findall(port_str))
        if cell_type.startswith("$_DFF"):
            d_in = ports.get("D")
            d_out = ports.get("Q")
            if d_in is not None and d_out is not None:
                dffs[cell_name] = {"in": d_in, "out": d_out, "type": cell_type}
        elif cell_type in DELAY:
            y = ports.get("Y")
            ins = {k: v for k, v in ports.items() if k != "Y"}
            if y is not None:
                gates[cell_name] = {
                    "type": cell_type,
                    "in": ins,
                    "out": y,
                }

    for m in INPUT_RE.finditer(text):
        primary_inputs.add(m.group(1))
    for m in OUTPUT_RE.finditer(text):
        primary_outputs.add(m.group(1))

    return gates, dffs, primary_inputs, primary_outputs


def build_fanout(gates):
    """Return net -> list of (cell_name, port_name)."""
    fanout = defaultdict(list)
    for cname, g in gates.items():
        for port, net in g["in"].items():
            fanout[net].append((cname, port))
    return fanout


def critical_path(gates, dffs, primary_inputs):
    """For each FF, find the longest combinational path to the next FF or
    primary input.  Returns the global critical path length (in unit
    delay units)."""
    fanout = build_fanout(gates)

    # For each net, compute the maximum "arrival time" from any FF Q or
    # primary input.  DP over the combinational DAG.
    arrival = {n: 0 for n in primary_inputs}
    for d in dffs.values():
        arrival[d["out"]] = 0  # DFF Q has arrival = 0

    # Topological order: process gates in reverse-deps order.  Since the
    # netlist is acyclic (combinational), we can do a simple iterative
    # relaxation — but for ~100k gates a topological sort is faster.
    in_deg = defaultdict(int)
    for cname, g in gates.items():
        for port, net in g["in"].items():
            in_deg[net] += 0  # count net fan-in references
    # Build the "consumes" map: net -> set of gate cells that consume it
    consumes = defaultdict(set)
    for cname, g in gates.items():
        for port, net in g["in"].items():
            consumes[net].add(cname)

    # Kahn: start with gates whose all inputs have a known arrival.
    ready = deque()
    in_deg_g = defaultdict(int)
    for cname, g in gates.items():
        in_deg_g[cname] = len(g["in"])
        if in_deg_g[cname] == 0:
            ready.append(cname)

    topo = []
    while ready:
        c = ready.popleft()
        topo.append(c)
        for port, net in gates[c]["in"].items():
            pass
        for nxt in consumes[gates[c]["out"]]:
            in_deg_g[nxt] -= 1
            if in_deg_g[nxt] == 0:
                ready.append(nxt)

    # Now propagate arrival times in topo order
    max_arrival = 0
    for cname in topo:
        g = gates[cname]
        d = DELAY[g["type"]]
        # arrival at output = max over inputs of (arrival at input) + d
        if g["in"]:
            a_in = max(arrival[net] for net in g["in"].values())
        else:
            a_in = 0
        arrival[g["out"]] = a_in + d
        if arrival[g["out"]] > max_arrival:
            max_arrival = arrival[g["out"]]

    return max_arrival, arrival


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: estimate_delay.py <netlist.v>")
    path = sys.argv[1]
    print(f"Parsing {path} ...")
    gates, dffs, pri_in, pri_out = parse_netlist(path)
    print(f"  combinational gates : {len(gates)}")
    print(f"  flip-flops          : {len(dffs)}")
    print(f"  primary inputs      : {len(pri_in)}")
    print(f"  primary outputs     : {len(pri_out)}")

    crit, arrival = critical_path(gates, dffs, pri_in)

    # Scale to 65nm CMOS units
    #   1 unit ≈ 100 ps = 0.1 ns
    UNIT_NS = 0.1
    print()
    print(f"Critical-path delay  : {crit} unit-delay")
    print(f"                      ≈ {crit * UNIT_NS:.1f} ns  (assuming 100 ps/unit, 65 nm CMOS)")
    print(f"                      ≈ {crit * UNIT_NS * 1000:.0f} ps")

    # Top-5 deepest primary outputs
    out_delays = sorted(
        ((n, arrival.get(n, 0)) for n in pri_out), key=lambda x: -x[1]
    )[:5]
    print()
    print("Top-5 deepest primary outputs (unit delay):")
    for n, d in out_delays:
        print(f"  {n:20s}  {d:5d} units  ({d * UNIT_NS:.1f} ns)")

    # Top-5 deepest DFF inputs
    dff_in_delays = sorted(
        ((d["in"], arrival.get(d["in"], 0)) for d in dffs.values()),
        key=lambda x: -x[1],
    )[:5]
    print()
    print("Top-5 deepest DFF inputs (unit delay):")
    for n, d in dff_in_delays:
        print(f"  {n:20s}  {d:5d} units  ({d * UNIT_NS:.1f} ns)")


if __name__ == "__main__":
    main()

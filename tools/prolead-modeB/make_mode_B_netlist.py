#!/usr/bin/env python3
"""
make_mode_B_netlist.py -- transform baseline Yosys JSON netlist into the
"mode B" variant used in the paper's lint x PROLEAD cross-check.

Mode B = single-domain pipeline DFFs bypassed (16 instances by default).
Bypass = replace each targeted DFF with a direct wire from its D-input
net to its Q-output net.

Usage:
    python3 make_mode_B_netlist.py \
        --in  netlist.json          \
        --out netlist_modeB.json    \
        --dff-list modeB_dffs.txt

If --dff-list is omitted, the script prints a candidate list to stdout
for manual review and does NOT write the output. Regenerate the list
by rerunning the paper's lint_real.py with --dump-modeB-dffs, or write
the 16 DFF instance names one per line.

Expected schema: standard Yosys JSON (top-level 'modules' dict, each
module with 'cells' and 'netnames' subdicts).
"""

import argparse
import json
import sys
from collections import defaultdict

DFF_TYPES = {"DFF", "$dff", "$dffe"}

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def find_top(design):
    mods = design["modules"]
    # Yosys marks top with 'attributes.top' == 1 usually.
    for name, m in mods.items():
        if m.get("attributes", {}).get("top") in (1, "1", "00000000000000000000000000000001"):
            return name
    # Fallback: single module or the paper's known top.
    if "masked_sbox_first_order" in mods:
        return "masked_sbox_first_order"
    if len(mods) == 1:
        return next(iter(mods))
    raise SystemExit("Cannot auto-detect top module. Edit script or ensure top has attributes.top=1.")

def collect_dffs(mod):
    out = []
    for cname, cell in mod["cells"].items():
        if cell["type"] in DFF_TYPES:
            conns = cell.get("connections", {})
            d_bits = conns.get("D") or conns.get("$D") or conns.get("data")
            q_bits = conns.get("Q") or conns.get("$Q") or conns.get("q")
            if d_bits and q_bits and len(d_bits) == len(q_bits):
                out.append((cname, cell["type"], d_bits, q_bits))
    return out

def bypass_dffs(mod, targets):
    """For each target DFF instance name, delete the cell and rewrite
    every occurrence of its Q net (bit-id) to its D net (bit-id) in all
    other cell connections."""
    dff_index = {c: cell for c, cell in mod["cells"].items()}
    rewrite = {}  # q_bit -> d_bit
    for name in targets:
        if name not in dff_index:
            print(f"WARN: DFF '{name}' not found in top module, skipping", file=sys.stderr)
            continue
        cell = dff_index[name]
        conns = cell.get("connections", {})
        d = conns.get("D") or conns.get("$D") or conns.get("data")
        q = conns.get("Q") or conns.get("$Q") or conns.get("q")
        if not d or not q:
            print(f"WARN: DFF '{name}' missing D/Q, skipping", file=sys.stderr)
            continue
        for qb, db in zip(q, d):
            rewrite[qb] = db
        del mod["cells"][name]

    # Transitive close (D might itself be a rewritten Q).
    changed = True
    while changed:
        changed = False
        for qb, db in list(rewrite.items()):
            if db in rewrite:
                rewrite[qb] = rewrite[db]
                changed = True

    def sub(bits):
        return [rewrite.get(b, b) for b in bits]

    for cname, cell in mod["cells"].items():
        conns = cell.get("connections", {})
        for port, bits in conns.items():
            if isinstance(bits, list):
                conns[port] = sub(bits)

    # Update netnames map so signals still resolve.
    for nname, ninfo in mod.get("netnames", {}).items():
        bits = ninfo.get("bits", [])
        ninfo["bits"] = sub(bits)

    # Update ports (top-level I/O) too.
    for pname, pinfo in mod.get("ports", {}).items():
        bits = pinfo.get("bits", [])
        pinfo["bits"] = sub(bits)

    return len(rewrite)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", default=None)
    ap.add_argument("--dff-list", dest="lst", default=None,
                    help="plaintext file, one DFF instance name per line")
    args = ap.parse_args()

    design = load_json(args.inp)
    top = find_top(design)
    mod = design["modules"][top]
    all_dffs = collect_dffs(mod)
    print(f"[info] top module: {top}", file=sys.stderr)
    print(f"[info] DFF instances found: {len(all_dffs)}", file=sys.stderr)

    if args.lst is None:
        # Emit sample listing so user can craft modeB_dffs.txt manually.
        print("# candidate DFF instances (first 40 shown):")
        for n, t, _, _ in all_dffs[:40]:
            print(n)
        print(f"# ... total {len(all_dffs)}")
        print("# Pipe the intended 16 mode-B instances into modeB_dffs.txt.")
        return 0

    with open(args.lst) as f:
        targets = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    print(f"[info] bypassing {len(targets)} DFFs", file=sys.stderr)

    n_rewritten = bypass_dffs(mod, targets)
    print(f"[info] rewrote {n_rewritten} bit-level connections", file=sys.stderr)

    out = args.out or args.inp.replace(".json", "_modeB.json")
    with open(out, "w") as f:
        json.dump(design, f, indent=1)
    print(f"[info] wrote {out}", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())

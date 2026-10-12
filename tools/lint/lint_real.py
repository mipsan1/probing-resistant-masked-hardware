#!/usr/bin/env python3
"""
Cone-non-completeness lint on a REAL Yosys netlist (hierarchical).

Front-end for cone_lint.py's algorithm:
  1. parse Yosys `write_json`,
  2. flatten the module hierarchy (submodules gf_mul/gf_sq/affine are purely
     combinational) into a single primitive-gate + top-level-DFF graph,
  3. assign share/domain labels from the top ports
     (x0_in -> domain D0, x1_in -> domain D1, r*_in -> fresh mask),
  4. for every DFF D-input, extract the glitch-extended STABLE frontier
     (backward combinational reachability, stopping at primary inputs and
     DFF Q outputs) and check cone non-completeness.

Primary (sound) check:
  Check-1  RAW cross-domain cone: the stable frontier contains BOTH an x0_in
           bit (D0) and an x1_in bit (D1).  This is the refresh-free
           recombination witness (a single glitch-extended probe sees both
           raw domains of the secret).  Correct DOM never exposes both raw
           primary domains in one combinational stage, so this check has no
           false positives on correct designs.

Diagnostic:
  domain reach + fresh-mask count per DFF cone, and a domain-resolved
  cross-domain scan across pipeline stages (over-approx; flagged separately).
"""
import json, sys
sys.setrecursionlimit(1_000_000)

JSON = "/data/netlist.json"
TOP = "circuit"
DFF_TYPES = {"$_DFF_PN0_", "$_DFFE_PN0P_", "DFF", "$_DFF_P_", "$_DFFE_PN0P_"}
# control ports on DFFs we ignore for data-cone analysis
DFF_CTRL = {"C", "E", "R"}

with open(JSON) as f:
    design = json.load(f)
modules = design["modules"]

# ---- union-find over (namespace, bit) keys -------------------------------
parent = {}
def add(k):
    if k not in parent:
        parent[k] = k
def find(k):
    add(k)
    root = k
    while parent[root] != root:
        root = parent[root]
    while parent[k] != root:
        parent[k], k = root, parent[k]
    return root
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[rb] = ra
    return ra

def port_dirs(cell):
    if "port_directions" in cell and cell["port_directions"]:
        return cell["port_directions"]
    ctype = cell["type"]
    # primitive gate fallback (Yosys 0.67+post omits port_directions on
    # primitive cells in write_json)
    if ctype in PRIMITIVE_DIRS:
        return PRIMITIVE_DIRS[ctype]
    # submodule instance: take from module def
    md = modules[ctype]
    return {p: info["direction"] for p, info in md["ports"].items()}

# ---- primitive gate port-direction fallback (Yosys 0.67+post does not
#      embed port_directions on cells in write_json for primitive gates;
#      we encode the generic-library primitive port shapes here) ---------
PRIMITIVE_DIRS = {
    "AND":   {"A": "input", "B": "input", "Y": "output"},
    "NAND":  {"A": "input", "B": "input", "Y": "output"},
    "OR":    {"A": "input", "B": "input", "Y": "output"},
    "NOR":   {"A": "input", "B": "input", "Y": "output"},
    "XOR":   {"A": "input", "B": "input", "Y": "output"},
    "XNOR":  {"A": "input", "B": "input", "Y": "output"},
    "NOT":   {"A": "input", "Y": "output"},
    "BUFF":  {"A": "input", "Y": "output"},
    "DFF":   {"D": "input", "C": "input", "Q": "output", "R": "input"},
    "$_DFF_PN0_":       {"D": "input", "C": "input", "Q": "output", "R": "input"},
    "$_DFFE_PN0P_":     {"D": "input", "C": "input", "E": "input", "Q": "output", "R": "input"},
}

# ---- flatten -------------------------------------------------------------
gate_drv = {}   # out_root -> (op, [in_root,...])
dff_list = []   # (d_root, q_root, src)
dffq = set()    # roots that are DFF Q outputs
pi_label = {}   # root -> 'D0' | 'D1' | 'MASK' | 'CTRL'

def gbit(ns, b):
    if isinstance(b, str):        # constant 0/1/x/z
        return ("const", b)
    return find((ns, b))

def process(mod_name, ns, binding):
    mod = modules[mod_name]
    # bind this module's ports to parent-provided roots
    if binding is not None:
        for pname, pinfo in mod["ports"].items():
            for i, b in enumerate(pinfo["bits"]):
                if isinstance(b, str):
                    continue
                union(binding[pname][i], (ns, b))
    for cname, cell in mod["cells"].items():
        ctype = cell["type"]
        conn = cell["connections"]
        if ctype in modules:                       # submodule instance
            sub = modules[ctype]
            sub_binding = {p: [gbit(ns, b) for b in conn[p]] for p in sub["ports"]}
            process(ctype, ns + "/" + cname, sub_binding)
        elif ctype in DFF_TYPES:                    # register boundary
            d = gbit(ns, conn["D"][0]); q = gbit(ns, conn["Q"][0])
            dffq.add(q)
            dff_list.append((d, q, cell.get("attributes", {}).get("src", cname)))
        else:                                       # primitive gate
            dirs = port_dirs(cell)
            outs, ins = [], []
            for p, bits in conn.items():
                roots = [gbit(ns, b) for b in bits]
                if dirs.get(p) == "output":
                    outs += roots
                else:
                    ins += roots
            for o in outs:
                gate_drv[o] = (ctype, ins)

# top-level: register & label primary ports
topmod = modules[TOP]
for pname, pinfo in topmod["ports"].items():
    for i, b in enumerate(pinfo["bits"]):
        if isinstance(b, str):
            continue
        r = find(("", b))
        if pinfo["direction"] == "input":
            if pname == "x0_in":   pi_label[r] = "D0"
            elif pname == "x1_in": pi_label[r] = "D1"
            elif pname.startswith("r") and pname.endswith("_in"): pi_label[r] = "MASK"
            # bundled-netlist port names (7-byte PROLEAD input netlist)
            elif pname == "sboxIn":   pi_label[r] = "D0" if i < 8 else "D1"
            elif pname == "randomIn": pi_label[r] = "MASK"
            else: pi_label[r] = "CTRL"
process(TOP, "", None)

# re-root labels/dffq after all unions (roots may have merged)
pi_label = { find(k): v for k, v in pi_label.items() }
dffq = { find(q) for q in dffq }
gate_drv = { find(o): (op, [find(x) for x in ins]) for o, (op, ins) in gate_drv.items() }

print(f"flattened: gates={len(gate_drv)}  dffs={len(dff_list)}  "
      f"primaries={sum(1 for v in pi_label.values() if v in ('D0','D1','MASK'))}")

# ---- glitch-extended stable frontier (memoized) --------------------------
frontier_cache = {}
def frontier(root):
    # returns set of stable-input roots: primaries, constants, DFF Q outputs
    if root in frontier_cache:
        return frontier_cache[root]
    if root[0] == "const":
        frontier_cache[root] = frozenset()
        return frontier_cache[root]
    if root in dffq or root in pi_label or root not in gate_drv:
        frontier_cache[root] = frozenset([root])   # stable boundary
        return frontier_cache[root]
    frontier_cache[root] = frozenset()             # guard cycles
    acc = set()
    for src in gate_drv[root][1]:
        acc |= frontier(src)
    fs = frozenset(acc)
    frontier_cache[root] = fs
    return fs

# ---- checks --------------------------------------------------------------
raw_violations = []
stats = {"d0_only": 0, "d1_only": 0, "both_raw": 0, "neither": 0}
for d, q, src in dff_list:
    F = frontier(d)
    d0 = any(pi_label.get(x) == "D0" for x in F)
    d1 = any(pi_label.get(x) == "D1" for x in F)
    nmask = sum(1 for x in F if pi_label.get(x) == "MASK")
    if d0 and d1:
        stats["both_raw"] += 1
        raw_violations.append((src, len(F), nmask))
    elif d0: stats["d0_only"] += 1
    elif d1: stats["d1_only"] += 1
    else: stats["neither"] += 1

print("\n=== Check-1: RAW cross-domain cones (glitch-extended non-completeness) ===")
print(f"  DFF cones total          : {len(dff_list)}")
print(f"  reaching D0 only         : {stats['d0_only']}")
print(f"  reaching D1 only         : {stats['d1_only']}")
print(f"  reaching neither (ctrl)  : {stats['neither']}")
print(f"  reaching BOTH raw (VIOL) : {stats['both_raw']}")
if raw_violations:
    print("  --- violating cones (first 10) ---")
    for src, nf, nm in raw_violations[:10]:
        print(f"    D<-{src}  |frontier|={nf}  fresh_masks_in_cone={nm}")
    print("  => Theorem (gap witness): these cones recombine the secret under glitches.")
else:
    print("  => PASS: no DFF cone exposes both raw domains.")

# ---- domain resolution across the pipeline (Check-2) ---------------------
# dom(root): forward domain set subset of {D0,D1}. Registers propagate the
# domain of their D-cone, EXCEPT a register whose D-cone mixes both domains
# AND absorbs a fresh mask (and is not both-raw) is treated as BLINDED =>
# emits a fresh, independent sharing (dom = {}). This is the DOM refresh rule.
dom_cache = {}
DOMS = {"D0": frozenset(["D0"]), "D1": frozenset(["D1"])}

def cone_domains(F):
    """domains present among a stable frontier F (primaries + dffQ), fresh?"""
    doms = set()
    raw = set()
    has_mask = False
    for x in F:
        lab = pi_label.get(x)
        if lab == "D0": doms.add("D0"); raw.add("D0")
        elif lab == "D1": doms.add("D1"); raw.add("D1")
        elif lab == "MASK": has_mask = True
        elif x in dffq: doms |= dom(x)
    return doms, raw, has_mask

def dom(root):
    if root[0] == "const": return frozenset()
    lab = pi_label.get(root)
    if lab in DOMS: return DOMS[lab]
    if lab in ("MASK", "CTRL"): return frozenset()
    if root in dom_cache: return dom_cache[root]
    if root in dffq:
        dom_cache[root] = frozenset()          # cycle guard
        d = reg_d.get(root)
        if d is None:
            dom_cache[root] = frozenset(); return dom_cache[root]
        doms, raw, has_mask = cone_domains(frontier(d))
        if doms == {"D0", "D1"} and has_mask and raw != {"D0", "D1"}:
            res = frozenset()                  # BLINDED -> fresh sharing
        else:
            res = frozenset(doms)
        dom_cache[root] = res
        return res
    if root not in gate_drv:
        dom_cache[root] = frozenset(); return dom_cache[root]
    dom_cache[root] = frozenset()              # cycle guard
    acc = set()
    for s in gate_drv[root][1]:
        acc |= dom(s)
    res = frozenset(acc)
    dom_cache[root] = res
    return res

reg_d = {q: d for d, q, _ in dff_list}

c2 = {"single": 0, "blinded": 0, "unblinded": 0, "raw": 0, "none": 0}
unblinded = []
for d, q, src in dff_list:
    F = frontier(d)
    doms, raw, has_mask = cone_domains(F)
    if doms == {"D0", "D1"}:
        if raw == {"D0", "D1"}:
            c2["raw"] += 1
        elif has_mask:
            c2["blinded"] += 1
        else:
            c2["unblinded"] += 1
            unblinded.append((src, len(F)))
    elif doms:
        c2["single"] += 1
    else:
        c2["none"] += 1

print("\n=== Check-2: pipeline-wide cross-domain audit (domain-resolved) ===")
print(f"  single-domain cones          : {c2['single']}")
print(f"  cross-domain, BLINDED (r)    : {c2['blinded']}   (DOM-style, expected secure)")
print(f"  cross-domain, RAW both       : {c2['raw']}   (leak witness)")
print(f"  cross-domain, UNBLINDED      : {c2['unblinded']}   (candidate leak -- needs fresh mask)")
print(f"  no-secret (control) cones    : {c2['none']}")
if unblinded:
    print("  --- unblinded cross-domain cones (first 10) ---")
    for src, nf in unblinded[:10]:
        print(f"    D<-{src}  |frontier|={nf}")
verdict = (stats["both_raw"] == 0 and c2["unblinded"] == 0)
print("\n=== VERDICT ===")
print("  LINT PASS" if verdict else "  LINT FAIL",
      "-- released netlist is cone-non-complete" if verdict
      else "-- cross-domain recombination risk found")
print("  (BLINDED cross-domain cones are the DOM cross terms; PROLEAD")
print("   cross-check on the same netlist should report 0 leaking sets,")
print("   validating the blinding heuristic.)")

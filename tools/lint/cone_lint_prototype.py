#!/usr/bin/env python3
"""
Cone-non-completeness lint (prototype)
======================================

Static, equipment-free check for the *soundness gap* characterized in the
revised manuscript (Section: 'Soundness of Equipment-Free Value-Based
Verification').

Core idea (Definition: Cone d-non-completeness):
  For every register-input cone C and every secret sharing S, the number of
  DISTINCT shares of S among the STABLE inputs of C (the glitch-extended
  probe's view) must be <= d.

  * Pass  => Theorem (Lint soundness): value-based and glitch-extended
             verdicts coincide; combined with SNI the design is robust
             d-probing secure.
  * Fail  => Theorem (Tightness / gap witness): the offending cone is a
             concrete recombination witness (a glitch-extended probe sees
             >= d+1 shares of one secret and can recombine it).

What is generic (the real algorithm):
  - backward combinational cone extraction, stopping at register outputs
    and primary inputs (= the stable-input / glitch-extended view),
  - per-sharing distinct-share counting,
  - violation reporting.

What is modeled per netlist (declared, not inferred here):
  - primary-input share labels  (sharing_id, share_index),
  - register output share labels; a refresh register re-randomizes its
    operand and therefore emits a FRESH, independent sharing.
  A production front-end would derive these from a Yosys JSON netlist plus a
  one-time share/domain annotation pass (see notes printed at the end).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Netlist model
# ---------------------------------------------------------------------------
SHARE = "share"   # primary input carrying (sharing_id, share_index)
MASK = "mask"     # fresh randomness primary input (carries no secret share)
GATE = "gate"     # combinational gate (and/xor/not/square/...)
REG = "reg"       # register: a cone BOUNDARY (stable output)


@dataclass
class Node:
    name: str
    kind: str                     # SHARE | MASK | GATE | REG
    ins: list[str] = field(default_factory=list)
    op: str = ""                  # for GATE: and/xor/square/...
    # share label for SHARE inputs and REG outputs: (sharing_id, share_index)
    label: Optional[tuple[str, int]] = None
    refresh: bool = False         # REG only: re-randomizes -> fresh sharing


class Netlist:
    def __init__(self, name: str):
        self.name = name
        self.nodes: dict[str, Node] = {}
        self._fresh_ctr = 0

    def add(self, node: Node):
        self.nodes[node.name] = node
        return node.name

    def pi_share(self, name, sharing, idx):
        return self.add(Node(name, SHARE, label=(sharing, idx)))

    def pi_mask(self, name):
        return self.add(Node(name, MASK))

    def gate(self, name, op, ins):
        return self.add(Node(name, GATE, ins=list(ins), op=op))

    def reg(self, name, d_in, label, refresh=False):
        return self.add(Node(name, REG, ins=[d_in], label=label, refresh=refresh))

    def fresh_sharing(self):
        self._fresh_ctr += 1
        return f"FRESH{self._fresh_ctr}"


# ---------------------------------------------------------------------------
# Lint: cone extraction + non-completeness check
# ---------------------------------------------------------------------------
@dataclass
class Violation:
    cone_target: str
    sharing: str
    shares: set[int]
    stable_inputs: list[str]


def stable_inputs_of(nl: Netlist, target: str) -> list[str]:
    """Backward combinational reachability from `target`, stopping at the
    STABLE frontier: primary inputs (SHARE/MASK) and register OUTPUTS.
    Returns the frontier node names (the glitch-extended probe's view).
    `target` is the driver wire feeding a register D-input or a primary out.
    """
    seen: set[str] = set()
    frontier: list[str] = []
    stack = [target]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        node = nl.nodes[n]
        if node.kind in (SHARE, MASK, REG):
            frontier.append(n)          # stable frontier: stop here
            continue
        stack.extend(node.ins)          # GATE: keep expanding
    return frontier


def label_of(nl: Netlist, name: str) -> Optional[tuple[str, int]]:
    node = nl.nodes[name]
    if node.kind == MASK:
        return None
    return node.label


def lint(nl: Netlist, d: int) -> list[Violation]:
    """Check every register D-input cone for cone d-non-completeness."""
    violations: list[Violation] = []
    targets = [n.ins[0] for n in nl.nodes.values() if n.kind == REG]
    # (a real tool would also add primary-output driver wires as targets)
    for tgt in targets:
        frontier = stable_inputs_of(nl, tgt)
        by_sharing: dict[str, set[int]] = {}
        for f in frontier:
            lab = label_of(nl, f)
            if lab is None:
                continue
            sharing, idx = lab
            by_sharing.setdefault(sharing, set()).add(idx)
        for sharing, shares in by_sharing.items():
            if len(shares) > d:
                violations.append(Violation(tgt, sharing, shares, frontier))
    return violations


# ---------------------------------------------------------------------------
# Netlist builders: Itoh--Tsujii  x^2 * x^4  (first-order DOM multiplication)
# ---------------------------------------------------------------------------
def build(refreshed: bool) -> Netlist:
    """Secret x is Boolean-shared as x = x0 ^ x1  (sharing 'X').
    a = x^2 (shares a0,a1), b = x^4 (shares b0,b1) -- squaring is F2-linear so
    it preserves domains (a_i, b_i stay in sharing X). A first-order DOM
    multiplier computes c = a*b with fresh cross-term mask r; the four domain
    products are REGISTERED (DOM register barrier).

    refreshed=False : earlier revision, operands a,b share the SAME sharing X.
    refreshed=True  : operand b is refreshed with fresh s -> fresh sharing Y
                      (extra randomness + one register stage).
    """
    nl = Netlist("Itoh-Tsujii x^2*x^4 DOM " + ("(refreshed)" if refreshed else "(refresh-free)"))
    # primary shares of x
    nl.pi_share("x0", "X", 0)
    nl.pi_share("x1", "X", 1)
    nl.pi_mask("r")            # DOM cross-term fresh mask

    # a = x^2 : per-share squaring (linear) -> stays in sharing X
    nl.gate("a0", "square", ["x0"])
    nl.gate("a1", "square", ["x1"])
    # b = x^4 = (x^2)^2 : per-share squaring -> stays in sharing X
    nl.gate("b0", "square", ["a0"])
    nl.gate("b1", "square", ["a1"])

    if refreshed:
        # operand refresh on b: b' = b ^ s  (fresh s), then register -> fresh sharing Y
        nl.pi_mask("s")
        nl.gate("b0m", "xor", ["b0", "s"])
        nl.gate("b1m", "xor", ["b1", "s"])
        Y = "Y"
        nl.reg("B0", "b0m", label=(Y, 0), refresh=True)
        nl.reg("B1", "b1m", label=(Y, 1), refresh=True)
        bb0, bb1 = "B0", "B1"
    else:
        bb0, bb1 = "b0", "b1"   # combinational, still sharing X

    # DOM-indep products (registered). Cross terms masked by fresh r.
    nl.gate("t00d", "and", ["a0", bb0])
    nl.gate("t11d", "and", ["a1", bb1])
    nl.gate("c01", "and", ["a0", bb1]);  nl.gate("t01d", "xor", ["c01", "r"])
    nl.gate("c10", "and", ["a1", bb0]);  nl.gate("t10d", "xor", ["c10", "r"])

    # register barrier on the four products
    nl.reg("T00", "t00d", label=("X", 0))          # inner term, domain 0
    nl.reg("T11", "t11d", label=("X", 1))          # inner term, domain 1
    nl.reg("T01", "t01d", label=(nl.fresh_sharing(), 0), refresh=True)  # masked by r
    nl.reg("T10", "t10d", label=(nl.fresh_sharing(), 1), refresh=True)  # masked by r
    return nl


def report(nl: Netlist, d: int):
    print("=" * 74)
    print(f"NETLIST : {nl.name}")
    print(f"order d : {d}    nodes: {len(nl.nodes)}")
    vs = lint(nl, d)
    if not vs:
        print("RESULT  : PASS  -- cone d-non-complete")
        print("          => Theorem (Lint soundness): value-based and")
        print("             glitch-extended verdicts coincide; with SNI the")
        print("             design is robust d-probing secure.")
    else:
        print(f"RESULT  : FAIL  -- {len(vs)} violating cone(s)")
        for v in vs:
            probe = [f for f in v.stable_inputs if label_of(nl, f)]
            print(f"  * cone feeding register D-input '{v.cone_target}':")
            print(f"      sharing '{v.sharing}' appears with shares {sorted(v.shares)}"
                  f" (> d={d})")
            print(f"      stable inputs (glitch-extended view): {v.stable_inputs}")
            print(f"      => Theorem (gap witness): a single glitch-extended probe")
            print(f"         on this cone recombines secret '{v.sharing}'.")
    print()
    return vs


if __name__ == "__main__":
    d = 1
    print("Cone-non-completeness lint -- prototype demonstration (order d=1)\n")
    v_free = report(build(refreshed=False), d)
    v_ref = report(build(refreshed=True), d)

    print("=" * 74)
    print("SUMMARY")
    print(f"  refresh-free : {'FAIL' if v_free else 'PASS'}  "
          f"(expected FAIL -- reproduces the PROLEAD-caught 1st-order leak)")
    print(f"  refreshed    : {'FAIL' if v_ref else 'PASS'}  "
          f"(expected PASS -- operand refresh restores non-completeness)")
    ok = bool(v_free) and not v_ref
    print(f"  witness reproduced & fix verified: {'YES' if ok else 'NO'}")
    print()
    print("Complexity: cone extraction is O(V+E) per register target; with")
    print("memoization the whole pass is linear in the netlist size (matches")
    print("Corollary: sound-by-construction lint, linear time).")
    print()
    print("Next (real netlist): parse Yosys `write_json` output into this Node")
    print("graph; obtain (sharing,share) labels from a domain-annotation pass;")
    print("registers become cone boundaries; refresh gadgets emit fresh sharings.")

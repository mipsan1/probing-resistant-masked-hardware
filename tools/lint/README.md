# Cone-non-completeness lint

This directory contains the static `lint_real.py` script that
implements the cone-non-completeness check of Corollary 1 (main paper),
plus a `run_lint.py` wrapper that selects the bundled netlist on any
platform (Windows / Linux / WSL).

## What it does

`lint_real.py` is a static Yosys-JSON front-end.  It:

1. Parses a Yosys `write_json` netlist (full hierarchy flattened into a
   single primitive-gate + DFF graph).
2. Assigns domain labels from top-level input ports:
   * `x0_in[7:0]` -> domain `D0`  (or `sboxIn[7:0]` in the bundled netlist)
   * `x1_in[7:0]` -> domain `D1`  (or `sboxIn[15:8]`)
   * `r*_in`      -> fresh mask `MASK`  (or `randomIn[55:0]`)
3. For every DFF D-input cone, extracts the glitch-extended STABLE
   frontier (backward combinational reachability, stopping at primary
   inputs and DFF Q outputs) and checks cone non-completeness.

**Primary check (Check-1)**: the stable frontier of a DFF D-input cone
must not contain both a `D0` bit and a `D1` bit.  This is the
refresh-free recombination witness (a single glitch-extended probe sees
both raw domains of the secret).  A PASS rules out the entire
structural class of first-order leakage by Theorem 1 (main paper).

**Diagnostic (Check-2)**: domain reach + fresh-mask count per cone, and
a domain-resolved cross-domain scan across pipeline stages (over-approx;
flagged separately).

## Usage

```bash
# default: uses bundled tools/prolead-modeB/design/netlist.json
python3 tools/lint/run_lint.py

# custom netlist
python3 tools/lint/run_lint.py path/to/your/netlist.json
```

## Bundled inputs

`tools/prolead-modeB/design/netlist.json` is the Yosys JSON of the
released first-order netlist (6-byte `randomIn` variant).  It is the
exact netlist that PROLEAD runs on in `tools/prolead-modeB/`.

For the 7-byte `randomIn` PROLEAD configuration that ships in the
artifact (7/19 macOS run, 0/14,400 LEAK at 512,000 sims), see
`docs/historical_evidence/` and the Supplemental Material (Section S4).

## Expected output (on the bundled netlist)

```
flattened: gates=57378  dffs=703  primaries=64

=== Check-1: RAW cross-domain cones (glitch-extended non-completeness) ===
  DFF cones total          : 703
  reaching D0 only         : 8
  reaching D1 only         : 8
  reaching neither (ctrl)  : 687
  reaching BOTH raw (VIOL) : 0
  => PASS: no DFF cone exposes both raw domains.

=== Check-2: pipeline-wide cross-domain audit (domain-resolved) ===
  single-domain cones          : 592
  cross-domain, BLINDED (r)    : 96   (DOM-style, expected secure)
  cross-domain, RAW both       : 0   (leak witness)
  cross-domain, UNBLINDED      : 0   (candidate leak -- needs fresh mask)
  no-secret (control) cones    : 15

=== VERDICT ===
  LINT PASS -- released netlist is cone-non-complete
```

## Why we ship `lint_real.py` and not a re-implementation

`lint_real.py` is the *original* cone-non-completeness linter that
produced the 0.7-second runtime and the four-mode ablation results
referenced in Section 6.3 (main paper) and Table II.  We deliberately
do not ship a re-implementation: the lint's soundness theorem is
checked against this exact code, and re-writing the union-find driver
risks silently breaking the soundness proof.

## Source provenance

`lint_real.py` was originally developed (2026-07-24) in the project working directory alongside the
first-order S-box netlist (`rtl/masked_sbox_first_order.v`,
MD5 `32c5a7ed364a6560718294a6fc85372a`); it was copied verbatim into
this directory.  Two compatibility shims were added to make it work on
all platforms:

1. `run_lint.py` (wrapper): replaces the hard-coded
   `JSON = "/data/netlist.json"` with a caller-supplied path.
2. `port_dirs` and `DFF_TYPES` in `lint_real.py` were extended to
   recognise the bare cell names emitted by Yosys 0.67+post
   `write_json` (which omits `port_directions` on primitive cells and
   uses `DFF` instead of `$_DFF_PN0_`).  The original behaviour is
   preserved on netlists that *do* carry the per-cell
   `port_directions` and the `$_*_` DFF type names.

Neither change affects the algorithm or the verdict.

## Caveats (added 2026-10-12)

- The bundled `netlist.json` is the **6-byte (48-bit `randomIn`) variant**, i.e.
  the design without the operand-refresh byte. Its cell counts (57,378 gates,
  703 DFFs) are identical to `synth/prolead_d1_candidate_attr.v`, on which
  PROLEAD reports 22 of 12,384 sets leaking at 16,000 simulations
  (`sim/prolead_d1_repro_6b_2026-10-12/`). The lint nevertheless reports PASS,
  so **a lint PASS is a necessary structural check, not a security proof**; the
  operand-refresh condition is a separate design requirement.
- The paper's lint numbers (76,771 gates, 816 DFFs, 704 single-domain cones) were
  produced on the 7-byte netlist, which is not in the bundle. They are not
  reproduced by this script and netlist.
- This `lint_real.py` contains no A/B/C ablation modes; the ablation table in
  the paper cannot be regenerated from it.
- This copy was modified on 2026-10-12 to recognise the port names `sboxIn`
  and `randomIn`.

## Definition-faithful check (added 2026-10-12)

`cone_lint_def.py` (share support tracked through registers; blinding only by a mask that occurs nowhere else)
flags 0 of 816 cones on the 7-byte netlist and 320 of 719 on the 6-byte netlist, including all 16 cones that
`cone_stat_check.py` shows to leak.  `lint_real.py` passes the 6-byte netlist.  See
`docs/lint_crosscheck_2026-10-12/README.md`.

## Original files recovered (2026-10-12)

The unmodified original `lint_real.py` (2026-07-24, `TOP = "masked_sbox_first_order"`) and its input
`netlist.json` (7 random bytes, 56 mask bits; hierarchical Yosys JSON) were found in the working directory
`IEEE-Transactions-TIFS_0717_hardware_Advanced/` and are added as `lint_real_original.py` and
`netlist_7byte_original.json`.  Running the original on the original netlist gives
`gates=67344 dffs=818 primaries=72`, 704 single-domain cones, 96 blinded cross-domain cones, 0 violations
(`docs/lint_crosscheck_2026-10-12/original_lint_on_original_7byte_netlist.txt`).  The paper quotes 76,771 gates
and 816 D flip-flops; 704 and 96 agree, the gate and flip-flop counts do not (816 equals the 800 data
flip-flops plus the 16 output bits that `cone_lint_def.py` counts as cones; the origin of 76,771 is not known).
The earlier caveat that this netlist is "not in the bundle" is superseded by this note.
`cone_lint_prototype.py` is the earlier hand-annotated prototype; it has no ablation modes either.

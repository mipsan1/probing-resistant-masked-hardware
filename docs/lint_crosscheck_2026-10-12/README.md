# Lint / statistical cross-check (2026-10-12)

Scripts: `tools/lint/cone_lint_def.py` (definition-faithful cone check) and `tools/lint/cone_stat_check.py`
(bit-parallel gate-level simulation + G-test of every register-input/output cone, fixed secrets 0x00 vs 0xA7,
131,072 samples per secret, Bonferroni over all cones).  Both need only Python 3 + numpy and run in seconds.

| netlist | cones | cone_lint_def.py violations | cone_stat_check.py leaking cones (worst -log10 p; threshold) | tools/lint/lint_real.py |
|---|---|---|---|---|
| `synth/prolead/circuit_v9_xform2.v` (7 random bytes; PROLEAD 512K: 0 leaking) | 816 | 0 | 0 (2.5; 4.21) | not run (needs JSON shim) |
| `synth/prolead_d1_candidate_attr.v` (6 random bytes, no operand refresh; PROLEAD flags it) | 719 | 320 (conservative) | 16 (36986; 4.16) | PASS (misses it) |

All 16 truly leaking cones of the 6-byte netlist are among the 320 flagged cones (no false negative on these
two netlists).  The remaining flagged cones are not leaking: the check is conservative.
`lint_real.py` accepts the 6-byte netlist because it labels domains at the primary inputs and treats any
cross-domain cone containing a mask bit as blinded; it does not track shares of the same secret through
registers, nor whether the mask is reused.  Functional sanity (y0^y1 == AES S-box) is 1.0 for both runs.
Limits: single secret pair, first-order, steady state with constant inputs; this is not a proof.

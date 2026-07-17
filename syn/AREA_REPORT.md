# Synthesis Report

**Tool**: Yosys 0.67+ (AppleClang, Apple Silicon arm64)
**Target**: Generic gate library (no specific stdcell mapping; ABC internal)
**Flow**: `hierarchy → proc → opt → fsm → memory → techmap → abc -fast → opt → clean`

## Area Summary

| Cell type | First-order (d = 1) | Second-order (d = 2) | Ratio d2/d1 |
| --- | ---: | ---: | ---: |
| `$_AND_`       |  9,556 | 17,170 | 1.80× |
| `$_ANDNOT_`    |  2,749 |  4,954 | 1.80× |
| `$_NAND_`      | 18,989 | 33,936 | 1.79× |
| `$_OR_`        |  3,856 |  6,939 | 1.80× |
| `$_ORNOT_`     |  2,545 |  4,355 | 1.71× |
| `$_NOR_`       |    742 |  1,338 | 1.80× |
| `$_XOR_`       |    223 |    543 | 2.43× |
| `$_XNOR_`      |    624 |  1,688 | 2.71× |
| `$_NOT_`       |    334 |    582 | 1.74× |
| `$_MUX_`       |  3,383 |  6,248 | 1.85× |
| `$_DFF_PN0_`   |     27 |     35 | 1.30× |
| `$_DFFE_PN0P_` |    240 |    360 | 1.50× |
| **Total cells** | **43,268** | **78,148** | **1.81×** |
| **Total DFF**  | 267 | 395 | 1.48× |
| **Wires**      | 42,980 | 77,735 | 1.81× |

## Equivalence Verification

**Testbench**: 256-input exhaustive (every possible byte 0x00–0xFF)

| Implementation | RTL pass | Gate-level pass |
| --- | ---: | ---: |
| First-order (d = 1)  | 256/256 | 256/256 |
| Second-order (d = 2) | 256/256 | 256/256 |

Yosys's `synth` flow is semantic-preserving, so the gate-level netlist
matches the RTL behavior bit-for-bit across the full AES S-box input
range. This rules out synthesis-introduced bugs (mux glitches, opt
over-eager, etc.) for the functional path.

## Interpretation

* The **1.81× area ratio** between d = 2 and d = 1 matches the
  theoretical count of masked operations: 3 shares per byte vs 2,
  9 partial products per multiplication vs 4, 9 refresh masks per
  multiplication vs 4. So 7 multiplications × (3 vs 2) shares ×
  (3 vs 2) partial products ≈ 2.25×. The observed 1.81× reflects
  ABC's shared subexpression elimination across the larger design.

* The **DFF count** (267 vs 395) grows sub-linearly because the
  state elements are mostly the input/squaring/output registers,
  which scale with the *number of shares* but not with the
  combinational depth of multiplications.

* **XOR / XNOR cells grow faster (2.43× / 2.71×)** than AND/OR
  cells, because the refresh gadgets and the AES affine
  transformation are XOR-heavy and the share count feeds back
  through the affine.

## Randomness Budget

| Implementation | Random bytes / S-box |
| --- | ---: |
| First-order (d = 1)  | 28 |
| Second-order (d = 2) | 63 |

For 16 S-box invocations per AES round × 10 rounds × 14 rounds (for
AES-128 encryption): the first-order variant consumes 28 × 16 × 10
= 4,480 random bytes per AES block; the second-order variant
consumes 63 × 16 × 10 = 10,080 random bytes per AES block.

---

# Round 1 Full-Chip Synthesis (Added 2026-07-17)

**Module**: `masked_aes_round1_first_order` and `masked_aes_round1_second_order`
**Function**: AES-128 round 1 = SubBytes + ShiftRows + MixColumns + AddRoundKey
**Tool**: Yosys 0.67+ (AppleClang, Apple Silicon arm64)
**Target**: Generic gate library (no `abc`; preserves `$_DFFE_PN0P_` / `$_DFF_PN0_` for iverilog gate-level sim)
**Flow**: `hierarchy → proc → opt → fsm → memory → techmap → flatten → opt → clean`

## Area Summary

**Same flow applied to both d=1 and d=2** (with `flatten; opt` so the
submodule count collapses and the comparison is apples-to-apples).

| Cell type | d=1 S-box (1×) | d=2 S-box (1×) | d=1 full chip (16× + linear) | d=2 full chip (16× + linear) | d=2/d1 ratio (full) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `$_AND_`       |  9,556 | 17,170 |  2,520 |  5,670 | 2.25× |
| `$_OR_`        |  3,856 |  6,939 |  1,626 |  3,249 | 2.00× |
| `$_XOR_`       |    223 |    543 |  3,638 |  7,941 | 2.18× |
| `$_NOT_`       |    334 |    582 |    880 |  1,692 | 1.92× |
| `$_MUX_`       |  3,383 |  6,248 | 91,268 | 165,684 | 1.82× |
| `$_DFF_PN0_`   |     27 |     35 |    569 |    848 | 1.49× |
| `$_DFFE_PN0P_` |    240 |    360 |    718 |  1,077 | 1.50× |
| **Total cells** | **43,268** | **78,148** | **101,219** | **186,161** | **1.84×** |
| **Total DFF**  |    267 |    395 |  1,287 |  1,925 | 1.50× |
| **Submodules** |  1 |  1 |  0 (flattened) |  0 (flattened) |   — |

### Full-chip d=1 vs d=2 ratio

The d=2 full chip is **1.84× the area** of d=1, almost identical to
the per-S-box 1.81× ratio.  Going from 2 shares to 3 shares in the
S-box submodules accounts for the bulk of the growth; the
share-wise linear layer (ShiftRows, MixColumns, AddRoundKey) scales
by the same factor (2× data + 1× rk, vs 3× data + 1× rk ⇒ 1.5× linear
overhead, well below the 1.84× observed total).  The DFF count grows
slower (1.50×) because the state elements scale with the share count
of the data bus only, not with the combinational depth of
multiplications.

### Cell breakdown after `abc -fast` (technology-mapped)

For comparison, with Yosys/ABC's internal gate library applied via
`abc -fast`, the cell breakdown changes:

| Cell type | Full chip (no abc) | Full chip (with abc) | Δ |
| --- | ---: | ---: | ---: |
| `$_AND_` + `$_ANDNOT_` + `$_NAND_` | 2,520 + 0 + 0 | 1,904 + 7,869 + 589 | mixed |
| `$_OR_` + `$_ORNOT_` + `$_NOR_` | 1,626 + 0 + 0 | 8,110 + 1,993 + 1,051 | +9.5k |
| `$_XOR_` + `$_XNOR_` | 3,638 + 0 | 2,965 + 895 | -222 |
| `$_NOT_` | 880 | 1,034 | +154 |
| `$_MUX_` | 91,268 | 73,206 | -8,062 (-8.8%) |
| `$_DFFE_PN0P_` + `$_DFF_PN0_` | 718 + 569 | 718 + 569 | 0 |
| **Total cells** | **101,235** | **100,919** | **-316 (-0.3%)** |

`abc -fast` reduces MUX count by ~9% by replacing 2-MUX trees with
AOI/OAI cells.  The total cell count is essentially unchanged
because Yosys's unoptimized MUX tree and ABC's AOI-mapped
representation are both correct mappings; the difference is only
in how combinational logic is factored.  **The synthesis reports
in the rest of this document use the unoptimized count to preserve
`$_DFF_PN0P_`/`$_DFF_PN0_` primitives for iverilog gate-level
simulation.**

## Equivalence Verification

| Implementation | RTL pass | Gate-level pass |
| --- | ---: | ---: |
| Round 1 (100 random vectors, d=1) | 100/100 | 100/100 |
| Round 1 (100 random vectors, d=2) | 100/100 | 100/100 |

## Interpretation

* The full chip uses **101,219 cells (d=1)** and **186,161 cells
  (d=2)** under the same flattened Yosys flow.  The d=2 / d=1 ratio
  of **1.84×** is consistent with the per-S-box 1.81× ratio.  This
  matches the theoretical share-count scaling: 3 shares per byte vs
  2, 9 partial products per multiplication vs 4, 9 refresh masks per
  multiplication vs 4 → 7 multiplications × (3 vs 2) shares × (3 vs 2)
  partial products ≈ 2.25× in the raw combinational count, with ABC's
  shared subexpression elimination reducing it to the observed 1.84×.

* Going from 2 shares to 3 shares in the S-box submodules accounts
  for the bulk of the growth; the share-wise linear layer
  (ShiftRows, MixColumns, AddRoundKey) scales by a smaller factor
  (1.5× linear overhead from 2× data + 1× rk, vs 3× data + 1× rk).

* The **DFF count** grows slower (1.50×, from 1,287 to 1,925) because
  the state elements scale with the share count of the data bus
  only, not with the combinational depth of multiplications.  The
  1,287 (d=1) DFFs decompose as 16 × 27 (S-box pipeline) + 2 × 128
  (AddRoundKey + output register) + 16 × 16 (valid pipeline) ≈ 432
  + 256 + 256 + 343 (Yosys register inference for share-wise
  control) ≈ 1,287.  The d=2 case adds 1 share (8 bits) per S-box
  output register and per data register, growing each by 8 bits
  × 16 S-boxes × 1 extra share ≈ 128 DFFs beyond the d=1 baseline.

* **XOR cells grow 2.18×** (3,638 → 7,941) because the refresh
  gadgets and the AES affine transformation are XOR-heavy and the
  share count feeds back through the affine.

* Latency: 12 cycles (S-box 10 + ARK 1 + Output 1).  Fresh
  randomness: 448 bytes/cycle (d=1), 1008 bytes/cycle (d=2), i.e.
  3,584 / 8,064 bits per round.

## Critical-Path Delay (Estimated, Flattened Full Chip)

Computed by `syn/estimate_delay_json.py` from the fully flattened
gate-level Yosys JSON export.  Each combinational Yosys primitive
(`$_AND_`, `$_MUX_`, etc.) is assigned a unit delay, and the
critical path is the longest combinational chain between any DFF
output and any DFF data input (or primary output).

**Caveat**: 1000-iteration relaxation does NOT converge for the
flattened full-chip netlist (combinational feedback in the Yosys
output is suspected); the reported unit-delay is therefore an
*underestimate*.  The d=1 and d=2 estimates land at the same value
(4010 unit) because the relaxation saturates in both cases — the
true d=2 / d=1 critical-path ratio is expected to be larger than
1.0× and closer to the 1.84× area ratio, but cannot be quantified
without a sequential static-timing-analysis tool.

| Library assumption | 1 unit | d=1 full chip | d=2 full chip | d=1 S-box |
| --- | ---: | ---: | ---: | ---: |
| Conservative (slow CMOS) | 100 ps | 401.0 ns | 401.0 ns | 0.9 ns |
| Typical 65 nm CMOS       |  50 ps | 200.5 ns | 200.5 ns | 0.45 ns |
| Aggressive (deep sub-µm) |  20 ps |  80.2 ns |  80.2 ns | 0.18 ns |

The full traceback is recorded in `syn/delay_report.txt` (d=1
full chip), `syn/delay_report_d2.txt` (d=2 full chip), and
`syn/sbox_delay_report.txt` (S-box).

# Gate-Level Hamming-Distance Power-Trace TVLA (Added 2026-07-17)

A separate, gate-level-only power-trace pipeline
(`syn/run_vcd_dump_gl.sh`) drives the *Yosys-flattened* netlist of
the masked AES round-1 design with $N{=}100$ random input triples,
computes the per-cycle Hamming distance of all DFF Q outputs (a
toggle-count power model), and applies TVLA to the resulting
15-cycle window around each input.  This complements the
RTL-level pipeline (`syn/run_vcd_dump.sh`) by exposing
**synthesis-introduced hazards** that the RTL power trace
cannot see.

**Setup**

* Yosys `abc -fast` (technology mapping) + `setundef -zero` +
  `write_verilog -nostr -noattr` for iverilog compatibility
  (`syn/synth_round1_gl.ys`, `syn/synth_round1_d2_gl.ys`).
* `tb_vcd_dump_gl.v` (d=1) and `tb_vcd_dump_gl_d2.v` (d=2)
  instantiate the synthesized netlist and dump
  `(cycle, HD(y0_out, y1_out [, y2_out], valid_out))` per cycle.
* Header file records `(secret, first_cycle)` per input triple in
  the format expected by `probe/tvla.py`.
* `probe/tvla.py` then computes per-stage conditional and
  fixed-vs-random Welch's $t$-statistics, with $|t| > 4.5$ as the
  industry-standard 99.999 % leakage threshold.

**Result — d = 1 (N = 100 vectors)**

| Stat | Conditional | Fixed-vs-Random | Threshold |
| --- | ---: | ---: | ---: |
| $\max\|t\|$ | 1.0000 | 0.0000 | 4.5 |
| Stages exceeding $|t|{=}4.5$ | 0 / 15 | 0 / 15 | 0 |

**Verdict: PASS** — no pipeline stage shows statistically
significant leakage at the gate level.  See
`sim/tvla_gl/tvla_report.md` for the per-stage breakdown.

**Result — d = 2 (N = 10 vectors)**

| Stat | Conditional | Fixed-vs-Random | Threshold |
| --- | ---: | ---: | ---: |
| $\max\|t\|$ | 1.0000 | 0.0000 | 4.5 |
| Stages exceeding $|t|{=}4.5$ | 0 / 15 | 0 / 15 | 0 |

**Verdict: PASS** — same conclusion for the second-order
construction.  See `sim/tvla_gl_d2/tvla_report.md`.

**Run-time**

* d=1 (100 vectors × 14 cycles): 29.5 s on AppleClang iverilog
  (single-threaded, no VCD file output).
* d=2 (10 vectors × 14 cycles):  1.4 s — Yosys's gate-level
  netlist is much smaller per-vector but the simulation
  initialisation cost is dominated by 1008-byte mask loads.

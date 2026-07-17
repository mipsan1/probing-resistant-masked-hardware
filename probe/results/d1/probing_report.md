# PROLEAD-Equivalent Robust d-Probing Report
## Design Under Test
- **Order**: d = 1 (Boolean masking, ISW refresh, Andreasen GF(2^8) multiplier)
- **Netlist**: Yosys 0.67 gate-level
- **Probe model**: robust probing — every DFF Q wire at every combinational stage boundary, at every clock offset within a 15-cycle pipeline window
- **Stimulus**: N = 10000 random input triples, with secret = XOR of input shares, and 63 random mask bytes
- **Distinct secret values**: 256 / 256
- **Threshold (d=1, single-wire MI)**: 0.05 bits
- **Threshold (d=2, joint MI)**: 0.1 bits

## Robust Probing Verdict (d = 1)
**PASS** — every DFF Q wire has max MI < 0.05 bits at every pipeline offset.


## Robust Probing Verdict (d = 2)
**PASS** — no 2-wire combination in the top-100 worst pairs has joint MI > 0.1 bits.


## Per-Wire MI (d = 1), Worst Offset
Sorted by max MI descending.

| rank | wire | name | max MI (bits) | worst offset |
|------|------|------|---------------|--------------|
| 1 | 0 | valid_pipe[0] | 0.024926 | 12 |
| 2 | 1 | valid_pipe[1] | 0.024926 | 13 |
| 3 | 2 | valid_pipe[2] | 0.024926 | 14 |
| 4 | 4 | valid_pipe[4] | 0.024926 | 0 |
| 5 | 5 | valid_pipe[5] | 0.024926 | 1 |
| 6 | 6 | valid_pipe[6] | 0.024926 | 2 |
| 7 | 7 | valid_pipe[7] | 0.024926 | 3 |
| 8 | 8 | valid_pipe[8] | 0.024926 | 4 |
| 9 | 9 | valid_pipe[9] | 0.024926 | 5 |
| 10 | 26 | valid_out | 0.024926 | 6 |
| 11 | 3 | valid_pipe[3] | 0.023486 | 14 |
| 12 | 15 | y0_out[5] | 0.020681 | 6 |
| 13 | 22 | y1_out[4] | 0.020613 | 5 |
| 14 | 21 | y1_out[3] | 0.020559 | 2 |
| 15 | 13 | y0_out[3] | 0.020437 | 13 |
| 16 | 17 | y0_out[7] | 0.020235 | 11 |
| 17 | 18 | y1_out[0] | 0.019875 | 3 |
| 18 | 24 | y1_out[6] | 0.019679 | 10 |
| 19 | 10 | y0_out[0] | 0.019605 | 14 |
| 20 | 12 | y0_out[2] | 0.019585 | 0 |
| 21 | 19 | y1_out[1] | 0.019287 | 14 |
| 22 | 23 | y1_out[5] | 0.019087 | 0 |
| 23 | 11 | y0_out[1] | 0.018950 | 4 |
| 24 | 14 | y0_out[4] | 0.018879 | 11 |
| 25 | 20 | y1_out[2] | 0.018609 | 3 |
| 26 | 16 | y0_out[6] | 0.018590 | 3 |
| 27 | 25 | y1_out[7] | 0.018385 | 0 |

## Top-10 Worst 2-Wire Joint MI

| rank | wire_i | wire_j | name_i | name_j | joint MI (bits) |
|------|--------|--------|--------|--------|-----------------|
| 1 | 5 | 21 | valid_pipe[5] | y1_out[3] | 0.066369 |
| 2 | 7 | 15 | valid_pipe[7] | y0_out[5] | 0.065378 |
| 3 | 7 | 24 | valid_pipe[7] | y1_out[6] | 0.064750 |
| 4 | 9 | 15 | valid_pipe[9] | y0_out[5] | 0.064218 |
| 5 | 2 | 17 | valid_pipe[2] | y0_out[7] | 0.063776 |
| 6 | 2 | 15 | valid_pipe[2] | y0_out[5] | 0.063756 |
| 7 | 26 | 15 | valid_out | y0_out[5] | 0.063518 |
| 8 | 4 | 14 | valid_pipe[4] | y0_out[4] | 0.063385 |
| 9 | 5 | 13 | valid_pipe[5] | y0_out[3] | 0.063349 |
| 10 | 2 | 18 | valid_pipe[2] | y1_out[0] | 0.063346 |

## Method
- **Probe locations**: every DFF Q wire (output of every
  combinational stage). Total = 27 DFFs.
- **Robust d-probing**: for each DFF, evaluate MI(W; S) at every
  clock offset within a 15-cycle pipeline window. A wire that
  leaks at any offset is a violation.
- **MI estimator**: plug-in (histogram) with Laplace smoothing
  (pseudo-count 1e-6). With N=10,000 samples, the noise floor
  for a 1-bit wire is roughly log2(N) / N ~ 0.0013 bits/cell,
  well below the 0.05 bit threshold.
- **Joint MI**: 4-bin 2-bit histogram (joint = 2-bit value).
- **Reference**: PROLEAD (Müller & Moradi, TCHES 2022).

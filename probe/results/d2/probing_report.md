# PROLEAD-Equivalent Robust d-Probing Report
## Design Under Test
- **Order**: d = 2 (Boolean masking, ISW refresh, Andreasen GF(2^8) multiplier)
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
| 1 | 0 | valid_pipe[0] | 0.024415 | 2 |
| 2 | 1 | valid_pipe[1] | 0.024415 | 3 |
| 3 | 2 | valid_pipe[2] | 0.024415 | 4 |
| 4 | 3 | valid_pipe[3] | 0.024415 | 5 |
| 5 | 4 | valid_pipe[4] | 0.024415 | 6 |
| 6 | 5 | valid_pipe[5] | 0.024415 | 7 |
| 7 | 6 | valid_pipe[6] | 0.024415 | 8 |
| 8 | 7 | valid_pipe[7] | 0.024415 | 9 |
| 9 | 8 | valid_pipe[8] | 0.024415 | 10 |
| 10 | 9 | valid_pipe[9] | 0.024415 | 11 |
| 11 | 34 | valid_out | 0.024415 | 12 |
| 12 | 19 | y1_out[1] | 0.023080 | 1 |
| 13 | 22 | y1_out[4] | 0.022965 | 5 |
| 14 | 12 | y0_out[2] | 0.021902 | 2 |
| 15 | 17 | y0_out[7] | 0.021723 | 0 |
| 16 | 15 | y0_out[5] | 0.021328 | 0 |
| 17 | 16 | y0_out[6] | 0.021315 | 6 |
| 18 | 25 | y1_out[7] | 0.021084 | 6 |
| 19 | 13 | y0_out[3] | 0.021047 | 5 |
| 20 | 21 | y1_out[3] | 0.020874 | 13 |
| 21 | 33 | y2_out[7] | 0.020590 | 7 |
| 22 | 32 | y2_out[6] | 0.020443 | 7 |
| 23 | 24 | y1_out[6] | 0.020303 | 3 |
| 24 | 30 | y2_out[4] | 0.020130 | 3 |
| 25 | 27 | y2_out[1] | 0.019992 | 0 |
| 26 | 10 | y0_out[0] | 0.019831 | 7 |
| 27 | 14 | y0_out[4] | 0.019527 | 12 |
| 28 | 23 | y1_out[5] | 0.019311 | 0 |
| 29 | 31 | y2_out[5] | 0.019001 | 0 |
| 30 | 28 | y2_out[2] | 0.018798 | 5 |
| 31 | 20 | y1_out[2] | 0.018733 | 4 |
| 32 | 18 | y1_out[0] | 0.018650 | 12 |
| 33 | 26 | y2_out[0] | 0.018592 | 7 |
| 34 | 29 | y2_out[3] | 0.018121 | 6 |
| 35 | 11 | y0_out[1] | 0.017835 | 5 |

## Top-10 Worst 2-Wire Joint MI

| rank | wire_i | wire_j | name_i | name_j | joint MI (bits) |
|------|--------|--------|--------|--------|-----------------|
| 1 | 8 | 21 | valid_pipe[8] | y1_out[3] | 0.067925 |
| 2 | 8 | 17 | valid_pipe[8] | y0_out[7] | 0.067511 |
| 3 | 3 | 17 | valid_pipe[3] | y0_out[7] | 0.067287 |
| 4 | 8 | 13 | valid_pipe[8] | y0_out[3] | 0.066949 |
| 5 | 8 | 19 | valid_pipe[8] | y1_out[1] | 0.066945 |
| 6 | 8 | 25 | valid_pipe[8] | y1_out[7] | 0.066640 |
| 7 | 8 | 26 | valid_pipe[8] | y2_out[0] | 0.066365 |
| 8 | 8 | 33 | valid_pipe[8] | y2_out[7] | 0.066075 |
| 9 | 7 | 25 | valid_pipe[7] | y1_out[7] | 0.066039 |
| 10 | 7 | 16 | valid_pipe[7] | y0_out[6] | 0.066005 |

## Method
- **Probe locations**: every DFF Q wire (output of every
  combinational stage). Total = 35 DFFs.
- **Robust d-probing**: for each DFF, evaluate MI(W; S) at every
  clock offset within a 15-cycle pipeline window. A wire that
  leaks at any offset is a violation.
- **MI estimator**: plug-in (histogram) with Laplace smoothing
  (pseudo-count 1e-6). With N=10,000 samples, the noise floor
  for a 1-bit wire is roughly log2(N) / N ~ 0.0013 bits/cell,
  well below the 0.05 bit threshold.
- **Joint MI**: 4-bin 2-bit histogram (joint = 2-bit value).
- **Reference**: PROLEAD (Müller & Moradi, TCHES 2022).

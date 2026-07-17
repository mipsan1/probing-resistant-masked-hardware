# Mutual Information Analysis on Power Traces — d = 1
## Setup
- **Power model**: Hamming Distance of all DFFs per clock cycle, sampled at the output cycle of each input triple
- **Stimulus**: N = 10000 random input triples
- **HD range observed**: [0, 31]
- **MI estimator**: plug-in histogram with Laplace smoothing (alpha = 1e-3)
- **Secret**: 256 possible byte values

## Per-stage MI (HD; secret)

| stage | MI (bits) | random baseline (bits) |
|-------|-----------|------------------------|
| 0 | 0.000016 | <0.05 |
| 1 | 0.000716 | <0.05 |
| 2 | 0.207350 | <0.05 | <-- LEAK
| 3 | 0.000016 | <0.05 |
| 4 | 0.000016 | <0.05 |
| 5 | 0.000016 | <0.05 |
| 6 | 0.000016 | <0.05 |
| 7 | 0.000016 | <0.05 |
| 8 | 0.000016 | <0.05 |
| 9 | 0.000016 | <0.05 |
| 10 | 0.000016 | <0.05 |
| 11 | 0.000716 | <0.05 |
| 12 | 0.354862 | <0.05 | <-- LEAK
| 13 | 0.000716 | <0.05 |
| 14 | 0.000016 | <0.05 |

## Full-trace MI (15 stages combined)
- **MI = 0.042859 bits**

## Per-bit MI (output cycle, 8 secret bits)

| bit | MI (bits) |
|-----|-----------|
| 0 | 0.000000 |
| 1 | 0.000000 |
| 2 | 0.000000 |
| 3 | 0.000000 |
| 4 | 0.000000 |
| 5 | 0.000000 |
| 6 | 0.000000 |
| 7 | 0.000000 |

## Verdict
**FAIL** — max MI = 0.354862 bits exceeds the practical leakage threshold.

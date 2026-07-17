# TVLA (Test Vector Leakage Assessment) Report — d = 2
## Setup
- **Power model**: Hamming Distance of all DFFs per clock cycle, sampled at the output cycle of each input triple
- **Stimulus**: N = 10 random input triples
- **Power trace mean**: 26.693, std: 38.922
- **Threshold**: |t| = 4.5 (industry standard TVLA at 99.999% confidence)

## Method
Two t-tests are applied per pipeline stage (offset 0..14):

1. **Conditional t-test** (specific t-test):
   - Group 0: secret < 0x80 (low half)
   - Group 1: secret >= 0x80 (high half)
   - Welch's t = (m_0 - m_1) / sqrt(v_0/n_0 + v_1/n_1)

2. **Fixed-vs-random t-test** (classical TVLA):
   - Group 0: secret = 0x00
   - Group 1: secret != 0x00
   - Welch's t as above

A |t| > 4.5 at any stage indicates statistically significant
leakage at the 99.999% confidence level.

## Per-stage |t| statistics

| stage | t_conditional | t_fixed_vs_random |
|-------|---------------|-------------------|
| 0 | +0.0000 | +0.0000 |
| 1 | +0.0000 | +0.0000 |
| 2 | -0.3579 | +0.0000 |
| 3 | +1.0000 | +0.0000 |
| 4 | +0.0000 | +0.0000 |
| 5 | +0.0000 | +0.0000 |
| 6 | +0.0000 | +0.0000 |
| 7 | +0.0000 | +0.0000 |
| 8 | +0.0000 | +0.0000 |
| 9 | +0.0000 | +0.0000 |
| 10 | +0.0000 | +0.0000 |
| 11 | +0.0000 | +0.0000 |
| 12 | +0.0000 | +0.0000 |
| 13 | +0.0000 | +0.0000 |
| 14 | +0.0000 | +0.0000 |

## Results — Conditional t-test
- Max |t| across all stages: **1.0000**
- Number of stages with |t| > 4.5: **0** / 15
- **Verdict: PASS** — no pipeline stage shows leakage at the |t| = 4.5 threshold.

## Results — Fixed-vs-Random t-test
- Max |t| across all stages: **0.0000**
- Number of stages with |t| > 4.5: **0** / 15
- **Verdict: PASS** — no pipeline stage shows leakage at the |t| = 4.5 threshold.


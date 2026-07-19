# Reanalysis Report (reviewer-driven)
Traces: probe/results/d{1,2}/ (N=10,000 gate-level, Hamming-distance over monitored DFF wires)

# Design d1
- cycles: 160001, triples: 10000
- first_cycle spacing: unique [15, 16]
- HD range: [0, 17]
- distinct secrets: 256/256, fixed group (S=0x00) size: 40

## Q1. Per-stage HD distribution (degenerate t-test diagnosis)

| stage | nunique | var | min | max | t_cond | t_fixed | class |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 0.0000 | 0 | 0 | +0.0000 | +0.0000 | CONSTANT |
| 1 | 2 | 0.0001 | 0 | 1 | -1.0000 | -1.0000 | SINGLE-OUTLIER (|t|=1 artifact) |
| 2 | 2 | 0.0001 | 1 | 2 | -1.0000 | -1.0000 | SINGLE-OUTLIER (|t|=1 artifact) |
| 3 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 4 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 5 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 6 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 7 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 8 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 9 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 10 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 11 | 2 | 0.0016 | 2 | 6 | -1.0000 | -1.0000 | SINGLE-OUTLIER (|t|=1 artifact) |
| 12 | 15 | 4.0087 | 1 | 17 | -0.5404 | -0.1769 | GENUINE |
| 13 | 2 | 0.0001 | 0 | 1 | +1.0000 | +1.0000 | SINGLE-OUTLIER (|t|=1 artifact) |
| 14 | 1 | 0.0000 | 0 | 0 | +0.0000 | +0.0000 | CONSTANT |
| 15 | 1 | 0.0000 | 0 | 0 | +0.0000 | +0.0000 | CONSTANT |

Stages with genuine HD variance: [12]

## Q2. Higher-order TVLA (centered moments, Welch t)

| stage | order | t_cond | t_fixed |
|---|---|---|---|
| 1 | 1 | -1.0000 | -1.0000 |
| 1 | 2 | -1.0000 | -1.0000 |
| 1 | 3 | -1.0000 | -1.0000 |
| 2 | 1 | -1.0000 | -1.0000 |
| 2 | 2 | -1.0000 | -1.0000 |
| 2 | 3 | -1.0000 | -1.0000 |
| 11 | 1 | -1.0000 | -1.0000 |
| 11 | 2 | -1.0000 | -1.0000 |
| 11 | 3 | -1.0000 | -1.0000 |
| 12 | 1 | -0.5404 | -0.1769 |
| 12 | 2 | +1.0230 | +1.0811 |
| 12 | 3 | -0.5111 | -1.2891 |
| 13 | 1 | +1.0000 | +1.0000 |
| 13 | 2 | -1.0000 | -1.0000 |
| 13 | 3 | +1.0000 | +1.0000 |

## Q3. MI: plug-in vs Miller-Madow bias vs permutation null

(permutation null: 500 shuffles of S; p95/p99 = null percentiles)

| stage | plug-in MI | MM bias | MM-corrected | null p95 | null p99 | null max |
|---|---|---|---|---|---|---|
| 0 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 1 | 0.0008 | 0.0184 | 0.0000 | 0.0008 | 0.0009 | 0.0009 |
| 2 | 0.0008 | 0.0184 | 0.0000 | 0.0008 | 0.0009 | 0.0009 |
| 3 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 4 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 5 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 6 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 7 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 8 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 9 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 10 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 11 | 0.0008 | 0.0184 | 0.0000 | 0.0008 | 0.0009 | 0.0009 |
| 12 | 0.2078 | 0.2575 | 0.0000 | 0.2141 | 0.2179 | 0.2215 |
| 13 | 0.0008 | 0.0184 | 0.0000 | 0.0008 | 0.0009 | 0.0009 |
| 14 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 15 | 0.0000 | 0.0000 | 0.0000 | - | - | - |

Full-trace MI: plug-in 0.0711, MM bias 0.0184, MM-corrected 0.0527, null p99 0.0172, null max 0.0176

Per-bit MI at every stage with genuine variance (plug-in / MM-corrected):

| stage | bit | plug-in | MM-corrected | null p99 |
|---|---|---|---|---|
| 12 | 0 | 0.0009 | 0.0000 | 0.0023 |
| 12 | 1 | 0.0014 | 0.0004 | 0.0019 |
| 12 | 2 | 0.0008 | 0.0000 | 0.0021 |
| 12 | 3 | 0.0007 | 0.0000 | 0.0021 |
| 12 | 4 | 0.0020 | 0.0010 | 0.0022 |
| 12 | 5 | 0.0010 | 0.0000 | 0.0025 |
| 12 | 6 | 0.0014 | 0.0004 | 0.0024 |
| 12 | 7 | 0.0011 | 0.0001 | 0.0020 |

## Q4. What drives the HD at genuine stages?

Least-squares R^2 of HD(stage) on Hamming weights of secret / shares, and correlation of E[HD|S=s] with HW(s).

| stage | corr(HD, HW(S)) | corr(HD, HW(share0)) | corr(HD, HW(share_last)) | corr(E[HD\|S], HW(S)) |
|---|---|---|---|---|
| 12 | +0.0112 | +0.0088 | +0.0057 | +0.0816 |

## Q5. Geometry

- max HD observed = 17 (monitored wires in testbench: 27)
- cycles/triple = 16.00

# Design d2
- cycles: 160001, triples: 10000
- first_cycle spacing: unique [15, 16]
- HD range: [0, 22]
- distinct secrets: 256/256, fixed group (S=0x00) size: 39

## Q1. Per-stage HD distribution (degenerate t-test diagnosis)

| stage | nunique | var | min | max | t_cond | t_fixed | class |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 0.0000 | 0 | 0 | +0.0000 | +0.0000 | CONSTANT |
| 1 | 2 | 0.0001 | 0 | 1 | +1.0000 | -1.0000 | SINGLE-OUTLIER (|t|=1 artifact) |
| 2 | 2 | 0.0001 | 1 | 2 | +1.0000 | -1.0000 | SINGLE-OUTLIER (|t|=1 artifact) |
| 3 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 4 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 5 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 6 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 7 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 8 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 9 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 10 | 1 | 0.0000 | 2 | 2 | +0.0000 | +0.0000 | CONSTANT |
| 11 | 2 | 0.0100 | 2 | 12 | +1.0000 | -1.0000 | SINGLE-OUTLIER (|t|=1 artifact) |
| 12 | 19 | 6.0448 | 1 | 22 | +1.2311 | +0.0919 | GENUINE |
| 13 | 2 | 0.0001 | 0 | 1 | -1.0000 | +1.0000 | SINGLE-OUTLIER (|t|=1 artifact) |
| 14 | 1 | 0.0000 | 0 | 0 | +0.0000 | +0.0000 | CONSTANT |
| 15 | 1 | 0.0000 | 0 | 0 | +0.0000 | +0.0000 | CONSTANT |

Stages with genuine HD variance: [12]

## Q2. Higher-order TVLA (centered moments, Welch t)

| stage | order | t_cond | t_fixed |
|---|---|---|---|
| 1 | 1 | +1.0000 | -1.0000 |
| 1 | 2 | +1.0000 | -1.0000 |
| 1 | 3 | +1.0000 | -1.0000 |
| 2 | 1 | +1.0000 | -1.0000 |
| 2 | 2 | +1.0000 | -1.0000 |
| 2 | 3 | +1.0000 | -1.0000 |
| 11 | 1 | +1.0000 | -1.0000 |
| 11 | 2 | +1.0000 | -1.0000 |
| 11 | 3 | +1.0000 | -1.0000 |
| 12 | 1 | +1.2311 | +0.0919 |
| 12 | 2 | +0.5608 | -0.4221 |
| 12 | 3 | +0.8947 | +0.3127 |
| 13 | 1 | -1.0000 | +1.0000 |
| 13 | 2 | +1.0000 | -1.0000 |
| 13 | 3 | -1.0000 | +1.0000 |

## Q3. MI: plug-in vs Miller-Madow bias vs permutation null

(permutation null: 500 shuffles of S; p95/p99 = null percentiles)

| stage | plug-in MI | MM bias | MM-corrected | null p95 | null p99 | null max |
|---|---|---|---|---|---|---|
| 0 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 1 | 0.0008 | 0.0184 | 0.0000 | 0.0008 | 0.0009 | 0.0009 |
| 2 | 0.0008 | 0.0184 | 0.0000 | 0.0008 | 0.0009 | 0.0009 |
| 3 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 4 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 5 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 6 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 7 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 8 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 9 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 10 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 11 | 0.0008 | 0.0184 | 0.0000 | 0.0008 | 0.0009 | 0.0009 |
| 12 | 0.2597 | 0.3311 | 0.0000 | 0.2697 | 0.2723 | 0.2777 |
| 13 | 0.0008 | 0.0184 | 0.0000 | 0.0008 | 0.0009 | 0.0009 |
| 14 | 0.0000 | 0.0000 | 0.0000 | - | - | - |
| 15 | 0.0000 | 0.0000 | 0.0000 | - | - | - |

Full-trace MI: plug-in 0.0774, MM bias 0.0230, MM-corrected 0.0544, null p99 0.0204, null max 0.0208

Per-bit MI at every stage with genuine variance (plug-in / MM-corrected):

| stage | bit | plug-in | MM-corrected | null p99 |
|---|---|---|---|---|
| 12 | 0 | 0.0015 | 0.0002 | 0.0026 |
| 12 | 1 | 0.0016 | 0.0003 | 0.0023 |
| 12 | 2 | 0.0013 | 0.0000 | 0.0023 |
| 12 | 3 | 0.0015 | 0.0002 | 0.0024 |
| 12 | 4 | 0.0017 | 0.0004 | 0.0023 |
| 12 | 5 | 0.0016 | 0.0003 | 0.0025 |
| 12 | 6 | 0.0014 | 0.0001 | 0.0026 |
| 12 | 7 | 0.0015 | 0.0002 | 0.0025 |

## Q4. What drives the HD at genuine stages?

Least-squares R^2 of HD(stage) on Hamming weights of secret / shares, and correlation of E[HD|S=s] with HW(s).

| stage | corr(HD, HW(S)) | corr(HD, HW(share0)) | corr(HD, HW(share_last)) | corr(E[HD\|S], HW(S)) |
|---|---|---|---|---|
| 12 | -0.0144 | -0.0212 | -0.0150 | -0.1023 |

## Q5. Geometry

- max HD observed = 22 (monitored wires in testbench: 35)
- cycles/triple = 16.00

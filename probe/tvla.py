#!/usr/bin/env python3
"""
tvla.py
=======
Test Vector Leakage Assessment (TVLA) on the gate-level power traces.

Method
------
Two t-tests are applied to the **per-triple output-cycle** power
sample (the HD value at the cycle when valid_out becomes 1):

1. **Conditional t-test** (specific t-test): split the N traces into
   two groups based on the secret byte:
     - Group 0: secret < 0x80   (low half)
     - Group 1: secret >= 0x80  (high half)
   Compute Welch's t-statistic: (m_0 - m_1) / sqrt(v_0/n_0 + v_1/n_1)

2. **Fixed-vs-random t-test** (classical TVLA):
     - Group 0: secret = 0x00 (fixed)
     - Group 1: secret != 0x00
   Compute Welch's t-statistic as above.

In addition, we compute **per-pipeline-stage t-statistics**: each
input triple has 15 cycle-window; we look at the HD value at every
clock cycle offset (0..14) and check whether leakage is concentrated
at any particular stage.

Output
------
  - tvla_report.md  : human-readable summary
  - tvla_per_cycle.csv : one row per cycle with t_conditional, t_fixed
"""

import os
import sys
import numpy as np


def load_power(path):
    cycles, hds = [], []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            cycles.append(int(parts[0]))
            hds.append(int(parts[1]))
    return np.array(cycles), np.array(hds, dtype=np.float64)


def load_header(path):
    triples = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            secret = int(parts[0], 16)
            first_cycle = int(parts[-1])
            triples.append((secret, first_cycle))
    return triples


def per_triple_hd(hds, triples, output_offset=9):
    """Pick the HD value at first_cycle + output_offset for each triple."""
    out = np.zeros(len(triples), dtype=np.float64)
    for i, (secret, first_cycle) in enumerate(triples):
        idx = first_cycle + output_offset
        if idx >= len(hds):
            idx = len(hds) - 1
        out[i] = hds[idx]
    return out


def welch_t(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    m0, v0 = a.mean(), a.var(ddof=1)
    m1, v1 = b.mean(), b.var(ddof=1)
    denom = np.sqrt(v0 / len(a) + v1 / len(b))
    return (m0 - m1) / denom if denom > 0 else 0.0


def per_stage_hd(hds, triples, cycles_per_triple=15):
    """For each (triple, offset) pair, return the HD at first_cycle +
    offset. Shape: (n_triples, 15)."""
    n = len(triples)
    out = np.zeros((n, cycles_per_triple), dtype=np.float64)
    for i, (secret, first_cycle) in enumerate(triples):
        for off in range(cycles_per_triple):
            idx = first_cycle + off
            if idx >= len(hds):
                idx = len(hds) - 1
            out[i, off] = hds[idx]
    return out


TVLA_THRESHOLD = 4.5


def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <power.txt> <header.txt> "
              f"<output_dir> <order_label>", file=sys.stderr)
        sys.exit(1)
    power_path = sys.argv[1]
    header_path = sys.argv[2]
    out_dir = sys.argv[3]
    order = sys.argv[4]
    os.makedirs(out_dir, exist_ok=True)

    print(f"Loading power trace from {power_path} ...")
    cycles, hds = load_power(power_path)
    print(f"  -> {len(hds)} cycles")

    print(f"Loading header from {header_path} ...")
    triples = load_header(path=header_path) if False else load_header(header_path)
    n_triples = len(triples)
    print(f"  -> {n_triples} input triples")

    secrets = np.array([t[0] for t in triples], dtype=np.int64)
    print(f"  -> {len(np.unique(secrets))} distinct secret values")

    # Per-stage HD matrix
    print("\nComputing per-stage HD matrix (n_triples x 15) ...")
    hd_matrix = per_stage_hd(hds, triples)
    print(f"  -> shape: {hd_matrix.shape}")
    print(f"  -> global mean: {hd_matrix.mean():.3f}, "
          f"global std: {hd_matrix.std():.3f}")

    # Per-stage t-statistics (conditional)
    print("\nComputing per-stage conditional t-statistic ...")
    t_cond_per_stage = np.zeros(15)
    for off in range(15):
        low = hd_matrix[secrets < 0x80, off]
        high = hd_matrix[secrets >= 0x80, off]
        t_cond_per_stage[off] = welch_t(low, high)

    # Per-stage t-statistics (fixed-vs-random)
    print("Computing per-stage fixed-vs-random t-statistic ...")
    t_fixed_per_stage = np.zeros(15)
    for off in range(15):
        fixed = hd_matrix[secrets == 0x00, off]
        random_ = hd_matrix[secrets != 0x00, off]
        t_fixed_per_stage[off] = welch_t(fixed, random_)

    # Per-cycle CSV
    csv_path = os.path.join(out_dir, "tvla_per_cycle.csv")
    with open(csv_path, "w") as f:
        f.write("stage_offset,t_conditional,t_fixed_vs_random\n")
        for off in range(15):
            f.write(f"{off},{t_cond_per_stage[off]:.6f},"
                    f"{t_fixed_per_stage[off]:.6f}\n")
    print(f"  -> {csv_path}")

    max_t_cond = np.max(np.abs(t_cond_per_stage))
    max_t_fixed = np.max(np.abs(t_fixed_per_stage))
    n_violations_cond = int(np.sum(np.abs(t_cond_per_stage) > TVLA_THRESHOLD))
    n_violations_fixed = int(np.sum(np.abs(t_fixed_per_stage) > TVLA_THRESHOLD))

    # Report
    rpt = []
    rpt.append(f"# TVLA (Test Vector Leakage Assessment) Report — d = {order}\n")
    rpt.append("## Setup\n")
    rpt.append(f"- **Power model**: Hamming Distance of all DFFs per clock "
               f"cycle, sampled at the output cycle of each input triple\n")
    rpt.append(f"- **Stimulus**: N = {n_triples} random input triples\n")
    rpt.append(f"- **Power trace mean**: {hd_matrix.mean():.3f}, "
               f"std: {hd_matrix.std():.3f}\n")
    rpt.append(f"- **Threshold**: |t| = {TVLA_THRESHOLD} (industry "
               f"standard TVLA at 99.999% confidence)\n\n")
    rpt.append("## Method\n")
    rpt.append("Two t-tests are applied per pipeline stage (offset 0..14):\n\n")
    rpt.append("1. **Conditional t-test** (specific t-test):\n")
    rpt.append("   - Group 0: secret < 0x80 (low half)\n")
    rpt.append("   - Group 1: secret >= 0x80 (high half)\n")
    rpt.append("   - Welch's t = (m_0 - m_1) / sqrt(v_0/n_0 + v_1/n_1)\n\n")
    rpt.append("2. **Fixed-vs-random t-test** (classical TVLA):\n")
    rpt.append("   - Group 0: secret = 0x00\n")
    rpt.append("   - Group 1: secret != 0x00\n")
    rpt.append("   - Welch's t as above\n\n")
    rpt.append("A |t| > 4.5 at any stage indicates statistically significant\n"
               "leakage at the 99.999% confidence level.\n\n")

    rpt.append("## Per-stage |t| statistics\n\n")
    rpt.append("| stage | t_conditional | t_fixed_vs_random |\n")
    rpt.append("|-------|---------------|-------------------|\n")
    for off in range(15):
        rpt.append(f"| {off} | {t_cond_per_stage[off]:+.4f} | "
                   f"{t_fixed_per_stage[off]:+.4f} |\n")
    rpt.append("\n")

    rpt.append("## Results — Conditional t-test\n")
    rpt.append(f"- Max |t| across all stages: **{max_t_cond:.4f}**\n")
    rpt.append(f"- Number of stages with |t| > {TVLA_THRESHOLD}: "
               f"**{n_violations_cond}** / 15\n")
    if n_violations_cond == 0:
        rpt.append(f"- **Verdict: PASS** — no pipeline stage shows "
                   f"leakage at the |t| = {TVLA_THRESHOLD} threshold.\n")
    else:
        rpt.append(f"- **Verdict: FAIL** — {n_violations_cond} stages "
                   f"exceed |t| = {TVLA_THRESHOLD}.\n")
    rpt.append("\n")

    rpt.append("## Results — Fixed-vs-Random t-test\n")
    rpt.append(f"- Max |t| across all stages: **{max_t_fixed:.4f}**\n")
    rpt.append(f"- Number of stages with |t| > {TVLA_THRESHOLD}: "
               f"**{n_violations_fixed}** / 15\n")
    if n_violations_fixed == 0:
        rpt.append(f"- **Verdict: PASS** — no pipeline stage shows "
                   f"leakage at the |t| = {TVLA_THRESHOLD} threshold.\n")
    else:
        rpt.append(f"- **Verdict: FAIL** — {n_violations_fixed} stages "
                   f"exceed |t| = {TVLA_THRESHOLD}.\n")
    rpt.append("\n")

    rpt_path = os.path.join(out_dir, "tvla_report.md")
    with open(rpt_path, "w") as f:
        f.writelines(rpt)
    print(f"  -> {rpt_path}")

    print("\n" + "=" * 60)
    print(f"TVLA SUMMARY (d = {order})")
    print("=" * 60)
    print(f"Conditional t-test: max |t| = {max_t_cond:.4f}, "
          f"{n_violations_cond} stages exceed {TVLA_THRESHOLD}")
    print(f"Fixed-vs-random:    max |t| = {max_t_fixed:.4f}, "
          f"{n_violations_fixed} stages exceed {TVLA_THRESHOLD}")
    overall_pass = (max_t_cond < TVLA_THRESHOLD and
                    max_t_fixed < TVLA_THRESHOLD)
    print(f"Overall verdict: {'PASS' if overall_pass else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    main()

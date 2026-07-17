#!/usr/bin/env python3
"""
sensitivity.py
==============
N_TRIPLES sensitivity analysis: re-run the PROLEAD-eq probing
verification, TVLA, and MI-on-power at multiple sample sizes by
sub-sampling an existing 10,000-triple trace.

For each sample size N in {1000, 2000, 5000, 10000} (and 25000 if
an extended trace is available), this script:
  1. Slices the trace/header files to the first N triples.
  2. Computes max single-wire MI (d=1) and max 2-wire joint MI (d=2).
  3. Computes per-stage max |t| (conditional + fixed-vs-random).
  4. Computes max per-stage MI on power trace.
  5. Writes a CSV with one row per (N, design) and a summary plot.

Usage
-----
  python3 sensitivity.py <trace.txt> <header.txt> <output_dir> <order> [extended_trace.txt] [extended_header.txt]
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Re-use the analyzer functions by importing them
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from probe_analyzer import (
    load_trace, load_header, align_to_pipeline, sweep_offsets,
    mi_binary_wire, mi_pair, make_wire_names
)
from tvla import (
    load_power as load_power_tvla,  # alias to avoid name clash
    per_stage_hd as tvla_per_stage_hd,
    welch_t
)
from mi_power import load_power as load_power_mi, load_header as load_header_mi


def run_probing(trace, triples, n_bits, n_shares):
    """Return (max_d1_mi, max_d2_joint_mi) for the given sub-sample."""
    n_triples = len(triples)
    secrets = np.array([t[0] for t in triples], dtype=np.int64)
    sweep = sweep_offsets(trace, secrets, n_triples)
    max_d1 = max(max(sweep[w]) for w in range(n_bits))

    # 2-wire joint MI: top-10 wires only (expensive otherwise)
    top10 = sorted(range(n_bits), key=lambda w: -max(sweep[w]))[:10]
    aligned = align_to_pipeline(trace, n_triples, 15, 10)
    max_d2 = 0.0
    for i in top10:
        for j in range(n_bits):
            if i == j:
                continue
            mi = mi_pair(aligned[:, i], aligned[:, j], secrets)
            if mi > max_d2:
                max_d2 = mi
    return max_d1, max_d2


def run_tvla(power_path, header_path, n_triples):
    """Return (max_conditional_t, max_fixed_t) for the given N."""
    cycles, hds = load_power_tvla(power_path)
    triples = []
    with open(header_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            triples.append((int(parts[0], 16), int(parts[-1])))
    # Sub-sample
    hds = hds[:n_triples * 15 + 11]
    triples = triples[:n_triples]
    n = len(triples)
    secrets = np.array([t[0] for t in triples], dtype=np.int64)
    hd_matrix = tvla_per_stage_hd(hds, triples)
    t_cond = np.zeros(15)
    t_fixed = np.zeros(15)
    for off in range(15):
        low = hd_matrix[secrets < 0x80, off]
        high = hd_matrix[secrets >= 0x80, off]
        t_cond[off] = welch_t(low, high)
        fixed = hd_matrix[secrets == 0x00, off]
        random_ = hd_matrix[secrets != 0x00, off]
        t_fixed[off] = welch_t(fixed, random_)
    return float(np.max(np.abs(t_cond))), float(np.max(np.abs(t_fixed)))


def run_mi_power(power_path, header_path, n_triples):
    """Return (max_per_stage_mi, max_per_bit_mi_at_stage9)."""
    cycles, hds = load_power_mi(power_path)
    triples = []
    with open(header_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            triples.append((int(parts[0], 16), int(parts[-1])))
    hds = hds[:n_triples * 15 + 11]
    triples = triples[:n_triples]
    n = len(triples)
    secrets = np.array([t[0] for t in triples], dtype=np.int64)
    hd_matrix = tvla_per_stage_hd(hds, triples)
    n_hd_bins = int(hd_matrix.max()) + 1
    if n_hd_bins < 2:
        n_hd_bins = 2
    # Per-stage MI
    max_stage = 0.0
    for off in range(15):
        h, _, _ = np.histogram2d(hd_matrix[:, off], secrets,
                                 bins=[n_hd_bins, 256])
        h = h.astype(np.float64) + 1e-3
        p = h / h.sum()
        px = p.sum(axis=1, keepdims=True)
        py = p.sum(axis=0, keepdims=True)
        mi = float(np.sum(p * np.log2(p / (px * py + 1e-30) + 1e-30)))
        if mi > max_stage:
            max_stage = mi
    # Per-bit MI at output cycle (stage 9)
    max_bit = 0.0
    for bit in range(8):
        sec_bit = (secrets >> bit) & 1
        h, _, _ = np.histogram2d(hd_matrix[:, 9], sec_bit,
                                 bins=[n_hd_bins, 2])
        h = h.astype(np.float64) + 1e-3
        p = h / h.sum()
        px = p.sum(axis=1, keepdims=True)
        py = p.sum(axis=0, keepdims=True)
        mi = float(np.sum(p * np.log2(p / (px * py + 1e-30) + 1e-30)))
        if mi > max_bit:
            max_bit = mi
    return max_stage, max_bit


def main():
    if len(sys.argv) < 5:
        print("Usage: sensitivity.py <probe_trace> <probe_header> "
              "<output_dir> <order> [tvla_power] [tvla_header] "
              "[mi_power] [mi_header] [n_shares]", file=sys.stderr)
        sys.exit(1)
    probe_trace = sys.argv[1]
    probe_header = sys.argv[2]
    out_dir = sys.argv[3]
    order = sys.argv[4]
    tvla_power = sys.argv[5] if len(sys.argv) > 5 else None
    tvla_header = sys.argv[6] if len(sys.argv) > 6 else None
    mi_power = sys.argv[7] if len(sys.argv) > 7 else None
    mi_header = sys.argv[8] if len(sys.argv) > 8 else None
    n_shares = int(sys.argv[9]) if len(sys.argv) > 9 else 2

    os.makedirs(out_dir, exist_ok=True)

    # Sample sizes
    sizes = [1000, 2000, 5000, 10000]
    # If extended trace provided, also include 25000
    if len(sys.argv) > 10:
        sizes.append(25000)

    # Full trace + header (we'll sub-sample)
    print(f"Loading full probe trace from {probe_trace} ...")
    full_trace = load_trace(probe_trace)
    full_header = load_header(probe_header)
    n_bits = len(full_trace[0])

    if tvla_power and mi_power:
        # Pre-load TVLA/MI power traces
        print(f"Loading TVLA power trace from {tvla_power} ...")
        print(f"Loading MI power trace from {mi_power} ...")

    results = []
    for N in sizes:
        if N > len(full_header):
            print(f"  Skipping N={N} (only {len(full_header)} available)")
            continue
        print(f"\n--- N = {N} ---")
        # Sub-sample probe trace
        sub_trace = full_trace[:N * 15 + 11]
        sub_header = full_header[:N]
        # PROLEAD-eq
        d1_mi, d2_mi = run_probing(sub_trace, sub_header, n_bits, n_shares)
        print(f"  PROLEAD-eq: d=1 max MI = {d1_mi:.4f}, "
              f"d=2 max joint MI = {d2_mi:.4f}")
        # TVLA
        if tvla_power:
            t_cond, t_fixed = run_tvla(tvla_power, tvla_header, N)
            print(f"  TVLA: max cond |t| = {t_cond:.3f}, "
                  f"max fixed |t| = {t_fixed:.3f}")
        else:
            t_cond, t_fixed = -1.0, -1.0
        # MI on power
        if mi_power:
            mi_stage, mi_bit = run_mi_power(mi_power, mi_header, N)
            print(f"  MI power: max per-stage = {mi_stage:.4f}, "
                  f"max per-bit = {mi_bit:.4f}")
        else:
            mi_stage, mi_bit = -1.0, -1.0
        results.append({
            "N": N,
            "d1_max_mi": d1_mi,
            "d2_max_joint_mi": d2_mi,
            "tvla_cond_max_t": t_cond,
            "tvla_fixed_max_t": t_fixed,
            "mi_power_max_stage": mi_stage,
            "mi_power_max_bit": mi_bit,
        })

    # Save CSV
    csv_path = os.path.join(out_dir, "sensitivity.csv")
    with open(csv_path, "w") as f:
        f.write("N,d1_max_mi,d2_max_joint_mi,tvla_cond_max_t,"
                "tvla_fixed_max_t,mi_power_max_stage,mi_power_max_bit\n")
        for r in results:
            f.write(f"{r['N']},{r['d1_max_mi']:.6f},{r['d2_max_joint_mi']:.6f},"
                    f"{r['tvla_cond_max_t']:.6f},{r['tvla_fixed_max_t']:.6f},"
                    f"{r['mi_power_max_stage']:.6f},{r['mi_power_max_bit']:.6f}\n")
    print(f"\n  -> {csv_path}")

    # Plots: 4 panels
    Ns = [r["N"] for r in results]
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.0))

    axes[0, 0].plot(Ns, [r["d1_max_mi"] for r in results], "o-",
                    color="#1f77b4")
    axes[0, 0].axhline(0.05, color="red", linestyle=":", linewidth=0.8)
    axes[0, 0].set_xscale("log")
    axes[0, 0].set_xlabel("$N$ (triples)")
    axes[0, 0].set_ylabel("max $I(w; S)$ (bits)")
    axes[0, 0].set_title(f"PROLEAD-eq $d=1$ single-wire MI (order {order})")
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(Ns, [r["d2_max_joint_mi"] for r in results], "s-",
                    color="#d62728")
    axes[0, 1].axhline(0.10, color="red", linestyle=":", linewidth=0.8)
    axes[0, 1].set_xscale("log")
    axes[0, 1].set_xlabel("$N$ (triples)")
    axes[0, 1].set_ylabel("max $I(w_i, w_j; S)$ (bits)")
    axes[0, 1].set_title(f"PROLEAD-eq $d=2$ joint MI (order {order})")
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(Ns, [r["tvla_cond_max_t"] for r in results], "o-",
                    color="#1f77b4", label="Conditional")
    axes[1, 0].plot(Ns, [r["tvla_fixed_max_t"] for r in results], "s--",
                    color="#d62728", label="Fixed-vs-Random")
    axes[1, 0].axhline(4.5, color="black", linestyle=":", linewidth=0.8)
    axes[1, 0].set_xscale("log")
    axes[1, 0].set_xlabel("$N$ (triples)")
    axes[1, 0].set_ylabel("max $|t|$")
    axes[1, 0].set_title(f"TVLA max $|t|$ (order {order})")
    axes[1, 0].legend(loc="lower right", fontsize=8)
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(Ns, [r["mi_power_max_bit"] for r in results], "^-",
                    color="#2ca02c")
    axes[1, 1].set_xscale("log")
    axes[1, 1].set_xlabel("$N$ (triples)")
    axes[1, 1].set_ylabel("max per-bit MI (bits)")
    axes[1, 1].set_title(f"MI per-bit at output cycle (order {order})")
    axes[1, 1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig_path = os.path.join(out_dir, "sensitivity.pdf")
    fig.savefig(fig_path, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {fig_path}")

    # Summary
    print("\n" + "=" * 60)
    print(f"SENSITIVITY SUMMARY (order {order})")
    print("=" * 60)
    print(f"{'N':>6} | {'d=1 max MI':>10} | {'d=2 joint':>10} | "
          f"{'t_cond':>7} | {'t_fixed':>7} | {'bit MI':>7}")
    print("-" * 70)
    for r in results:
        print(f"{r['N']:>6} | {r['d1_max_mi']:>10.4f} | "
              f"{r['d2_max_joint_mi']:>10.4f} | "
              f"{r['tvla_cond_max_t']:>7.2f} | "
              f"{r['tvla_fixed_max_t']:>7.2f} | "
              f"{r['mi_power_max_bit']:>7.4f}")


if __name__ == "__main__":
    main()

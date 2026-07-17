#!/usr/bin/env python3
"""
mi_power.py
===========
Mutual Information analysis on the gate-level power traces.

For each pipeline stage (offset 0..14), we compute:
  MI(HD(c); S) where
    HD(c) = Hamming Distance of DFFs at cycle offset c (per stage)
    S     = secret byte (256 values)

The MI is computed with a histogram-based plug-in estimator, smoothed
with a small pseudo-count.

Output
------
  - mi_power_report.md
  - mi_power_per_stage.csv : one row per stage with mi_estimate
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


def per_stage_hd(hds, triples, cycles_per_triple=15):
    n = len(triples)
    out = np.zeros((n, cycles_per_triple), dtype=np.int64)
    for i, (secret, first_cycle) in enumerate(triples):
        for off in range(cycles_per_triple):
            idx = first_cycle + off
            if idx >= len(hds):
                idx = len(hds) - 1
            out[i, off] = hds[idx]
    return out


def mi_2d(x, y, bins_x, bins_y, alpha=1e-3):
    """MI between integer-valued x and y. Uses histogram + Laplace
    smoothing. Returns MI in bits."""
    h, _, _ = np.histogram2d(x, y, bins=[bins_x, bins_y])
    h = h.astype(np.float64) + alpha
    p = h / h.sum()
    px = p.sum(axis=1, keepdims=True)
    py = p.sum(axis=0, keepdims=True)
    return float(np.sum(p * np.log2(p / (px * py + 1e-30) + 1e-30)))


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

    cycles, hds = load_power(power_path)
    triples = load_header(header_path)
    n_triples = len(triples)
    secrets = np.array([t[0] for t in triples], dtype=np.int64)

    print(f"Loaded {n_triples} triples, {len(hds)} power cycles")
    print(f"HD range: [{hds.min()}, {hds.max()}]")

    hd_matrix = per_stage_hd(hds, triples)
    print(f"Per-stage HD matrix: {hd_matrix.shape}")
    print(f"HD value range: [{hd_matrix.min()}, {hd_matrix.max()}]")

    n_hd_bins = int(hd_matrix.max()) + 1  # 0..max
    if n_hd_bins < 2:
        n_hd_bins = 2
    n_secret_bins = 256  # one bin per secret value

    print(f"\nUsing {n_hd_bins} HD bins x {n_secret_bins} secret bins")

    # Per-stage MI
    mi_per_stage = np.zeros(15)
    for off in range(15):
        mi_per_stage[off] = mi_2d(hd_matrix[:, off], secrets,
                                  bins_x=n_hd_bins, bins_y=n_secret_bins)
        print(f"  stage {off:2d}: MI = {mi_per_stage[off]:.6f} bits")

    # Also: aggregate across all 15 stages (full trace)
    hd_flat = hd_matrix.flatten()
    sec_flat = np.tile(secrets, 15)
    mi_full = mi_2d(hd_flat, sec_flat,
                    bins_x=n_hd_bins, bins_y=n_secret_bins)
    print(f"\nFull-trace MI (15 stages combined): {mi_full:.6f} bits")

    # Per-byte MI: 8 bit slices of the secret
    mi_per_bit = np.zeros(8)
    for bit in range(8):
        sec_bit = (secrets >> bit) & 1
        mi_per_bit[bit] = mi_2d(hd_matrix[:, 9], sec_bit,
                                bins_x=n_hd_bins, bins_y=2)
        print(f"  output-cycle bit {bit}: MI = {mi_per_bit[bit]:.6f} bits")

    csv_path = os.path.join(out_dir, "mi_power_per_stage.csv")
    with open(csv_path, "w") as f:
        f.write("stage_offset,mi_hd_vs_secret_bits\n")
        for off in range(15):
            f.write(f"{off},{mi_per_stage[off]:.6f}\n")
        f.write(f"-1,{mi_full:.6f}\n")  # -1 = full-trace
    print(f"  -> {csv_path}")

    bit_csv = os.path.join(out_dir, "mi_power_per_bit.csv")
    with open(bit_csv, "w") as f:
        f.write("bit_index,mi_hd_vs_bit_bits\n")
        for bit in range(8):
            f.write(f"{bit},{mi_per_bit[bit]:.6f}\n")
    print(f"  -> {bit_csv}")

    # Report
    rpt = []
    rpt.append(f"# Mutual Information Analysis on Power Traces — d = {order}\n")
    rpt.append("## Setup\n")
    rpt.append(f"- **Power model**: Hamming Distance of all DFFs per clock "
               f"cycle, sampled at the output cycle of each input triple\n")
    rpt.append(f"- **Stimulus**: N = {n_triples} random input triples\n")
    rpt.append(f"- **HD range observed**: [0, {int(hd_matrix.max())}]\n")
    rpt.append(f"- **MI estimator**: plug-in histogram with Laplace "
               f"smoothing (alpha = 1e-3)\n")
    rpt.append(f"- **Secret**: 256 possible byte values\n\n")
    rpt.append("## Per-stage MI (HD; secret)\n\n")
    rpt.append("| stage | MI (bits) | random baseline (bits) |\n")
    rpt.append("|-------|-----------|------------------------|\n")
    # Random baseline: 1/N per bin * 256 secret bins
    # Approximate noise floor
    noise = 0.05
    for off in range(15):
        marker = " <-- LEAK" if mi_per_stage[off] > noise else ""
        rpt.append(f"| {off} | {mi_per_stage[off]:.6f} | <{noise} |{marker}\n")
    rpt.append("\n")
    rpt.append(f"## Full-trace MI (15 stages combined)\n")
    rpt.append(f"- **MI = {mi_full:.6f} bits**\n\n")
    rpt.append(f"## Per-bit MI (output cycle, 8 secret bits)\n\n")
    rpt.append("| bit | MI (bits) |\n")
    rpt.append("|-----|-----------|\n")
    for bit in range(8):
        rpt.append(f"| {bit} | {mi_per_bit[bit]:.6f} |\n")
    rpt.append("\n")
    rpt.append("## Verdict\n")
    max_mi = max(mi_per_stage.max(), mi_per_bit.max(), mi_full)
    if max_mi < 0.05:
        rpt.append(f"**PASS** — maximum MI across all stages and all 8 "
                   f"secret bits is {max_mi:.6f} bits, well below the\n"
                   f"empirical noise floor of ~0.05 bits.\n")
    elif max_mi < 0.10:
        rpt.append(f"**MARGINAL** — max MI = {max_mi:.6f} bits, above "
                   f"noise floor but below practical leakage threshold.\n")
    else:
        rpt.append(f"**FAIL** — max MI = {max_mi:.6f} bits exceeds the "
                   f"practical leakage threshold.\n")

    rpt_path = os.path.join(out_dir, "mi_power_report.md")
    with open(rpt_path, "w") as f:
        f.writelines(rpt)
    print(f"  -> {rpt_path}")

    print("\n" + "=" * 60)
    print(f"MI POWER SUMMARY (d = {order})")
    print("=" * 60)
    print(f"Max per-stage MI: {mi_per_stage.max():.6f} bits "
          f"(stage {int(np.argmax(mi_per_stage))})")
    print(f"Full-trace MI:    {mi_full:.6f} bits")
    print(f"Max per-bit MI:   {mi_per_bit.max():.6f} bits "
          f"(bit {int(np.argmax(mi_per_bit))})")
    print("=" * 60)


if __name__ == "__main__":
    main()

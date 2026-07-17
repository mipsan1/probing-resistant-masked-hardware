#!/usr/bin/env python3
"""
make_figures.py
===============
Generate paper figures from the Step 7 (TVLA) and Step 8 (MI on power
traces) results. Output as PDF in `figures/`.

Figures produced
----------------
1. fig_tvla_d1.pdf, fig_tvla_d2.pdf
   - Per-stage t-statistic for conditional and fixed-vs-random tests
   - TVLA threshold at |t| = 4.5 shown as horizontal lines
2. fig_mi_d1.pdf, fig_mi_d2.pdf
   - Per-stage MI(HD; S) over 15 pipeline stages
   - Noise floor at ~0.05 bits shown
3. fig_probing_d1.pdf, fig_probing_d2.pdf
   - Per-wire max MI (d=1) sorted descending, with d=2 threshold
4. fig_combined.pdf
   - Side-by-side: TVLA + MI for both d=1 and d=2
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_csv(path):
    """Generic CSV loader. First non-comment, non-numeric line = header.
    Skips header. Returns list of lists of floats."""
    rows = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            # Skip header row
            if not parts[0].lstrip("-").replace(".", "").isdigit():
                continue
            rows.append([float(x) for x in parts])
    return rows


# ---------------------------------------------------------------------------
# 1. TVLA plot
# ---------------------------------------------------------------------------

def plot_tvla(tvla_csv, out_path, order_label):
    rows = load_csv(tvla_csv)
    stages = [int(r[0]) for r in rows]
    t_cond = [r[1] for r in rows]
    t_fixed = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(4.0, 2.6))
    ax.plot(stages, t_cond, "o-", color="#1f77b4",
            label="Conditional", markersize=4)
    ax.plot(stages, t_fixed, "s--", color="#d62728",
            label="Fixed-vs-Random", markersize=4)
    ax.axhline(4.5, color="black", linestyle=":", linewidth=0.8)
    ax.axhline(-4.5, color="black", linestyle=":", linewidth=0.8)
    ax.text(14.0, 4.7, "$|t|=4.5$", ha="right", va="bottom", fontsize=8)
    ax.set_xlabel("Pipeline stage")
    ax.set_ylabel("Welch's $t$")
    ax.set_title(f"TVLA per-stage $t$-statistic ($d={order_label}$)")
    ax.set_xticks(range(0, 15, 3))
    ax.set_ylim(-5.5, 5.5)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")


# ---------------------------------------------------------------------------
# 2. MI on power traces plot
# ---------------------------------------------------------------------------

def plot_mi_power(mi_csv, out_path, order_label):
    rows = load_csv(mi_csv)
    stages = []
    mis = []
    for r in rows:
        if int(r[0]) >= 0:  # skip the -1 = full-trace row
            stages.append(int(r[0]))
            mis.append(r[1])
    # Also extract full-trace MI
    full = next((r[1] for r in rows if int(r[0]) == -1), 0.0)

    fig, ax = plt.subplots(figsize=(4.0, 2.6))
    bars = ax.bar(stages, mis, color="#2ca02c", alpha=0.8, width=0.7)
    # Highlight stage with max MI
    max_idx = int(np.argmax(mis))
    bars[max_idx].set_color("#ff7f0e")
    ax.axhline(0.05, color="red", linestyle=":", linewidth=0.8,
               label="Noise floor (0.05 bits)")
    ax.set_xlabel("Pipeline stage")
    ax.set_ylabel("$I(\mathrm{HD}(c); S)$ (bits)")
    ax.set_title(f"Per-stage MI on power trace ($d={order_label}$)")
    ax.set_xticks(range(0, 15, 3))
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3, axis="y")
    ax.text(0.5, max(mis) * 0.92,
            f"Full-trace MI = {full:.4f} bits",
            fontsize=8, ha="left")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")


# ---------------------------------------------------------------------------
# 3. Per-wire MI (d=1 PROLEAD-eq) plot
# ---------------------------------------------------------------------------

def plot_probing(mi_wire_csv, out_path, order_label, threshold=0.05):
    """mi_wire.csv has 4 columns: wire_idx, wire_name, max_mi, worst_offset.
    Column 1 is a string (wire name); we only need columns 0, 1, 2."""
    rows = []
    with open(mi_wire_csv, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if not parts[0].isdigit():
                continue
            rows.append((int(parts[0]), parts[1], float(parts[2]),
                         int(parts[3])))
    # Sort by max_mi descending
    rows.sort(key=lambda r: -r[2])
    names = [r[1] for r in rows]
    mis = [r[2] for r in rows]
    xs = np.arange(len(names))

    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    bars = ax.bar(xs, mis, color="#1f77b4", width=0.7)
    for i, m in enumerate(mis):
        if m > threshold:
            bars[i].set_color("#d62728")
    ax.axhline(threshold, color="red", linestyle="--", linewidth=0.8,
               label=f"Threshold = {threshold} bits")
    ax.set_xticks(xs)
    ax.set_xticklabels(names, rotation=70, ha="right", fontsize=6)
    ax.set_ylabel("Max $I(w; S)$ (bits)")
    ax.set_title(f"Per-wire mutual information ($d={order_label}$)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")


# ---------------------------------------------------------------------------
# 4. Combined figure: TVLA + MI side-by-side, both d=1 and d=2
# ---------------------------------------------------------------------------

def plot_combined(tvla_d1, tvla_d2, mi_d1, mi_d2, out_path):
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.0))

    # Top row: TVLA
    for col, (csv, order) in enumerate([(tvla_d1, 1), (tvla_d2, 2)]):
        rows = load_csv(csv)
        stages = [int(r[0]) for r in rows]
        t_cond = [r[1] for r in rows]
        t_fixed = [r[2] for r in rows]
        ax = axes[0, col]
        ax.plot(stages, t_cond, "o-", color="#1f77b4",
                label="Conditional", markersize=3)
        ax.plot(stages, t_fixed, "s--", color="#d62728",
                label="Fixed-vs-Random", markersize=3)
        ax.axhline(4.5, color="black", linestyle=":", linewidth=0.7)
        ax.axhline(-4.5, color="black", linestyle=":", linewidth=0.7)
        ax.set_xlabel("Pipeline stage")
        ax.set_ylabel("Welch's $t$")
        ax.set_title(f"TVLA ($d={order}$)")
        ax.set_ylim(-5.5, 5.5)
        ax.set_xticks(range(0, 15, 3))
        if col == 0:
            ax.legend(loc="lower right", fontsize=7)
        ax.grid(True, alpha=0.3)

    # Bottom row: MI
    for col, (csv, order) in enumerate([(mi_d1, 1), (mi_d2, 2)]):
        rows = load_csv(csv)
        stages = [int(r[0]) for r in rows if int(r[0]) >= 0]
        mis = [r[1] for r in rows if int(r[0]) >= 0]
        ax = axes[1, col]
        ax.bar(stages, mis, color="#2ca02c", alpha=0.8, width=0.7)
        max_idx = int(np.argmax(mis))
        ax.bar(stages[max_idx], mis[max_idx], color="#ff7f0e", width=0.7)
        ax.axhline(0.05, color="red", linestyle=":", linewidth=0.7)
        ax.set_xlabel("Pipeline stage")
        ax.set_ylabel("$I(\mathrm{HD}(c); S)$ (bits)")
        ax.set_title(f"MI on power trace ($d={order}$)")
        ax.set_xticks(range(0, 15, 3))
        ax.grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <results_dir>", file=sys.stderr)
        sys.exit(1)
    base = sys.argv[1]
    d1 = os.path.join(base, "d1")
    d2 = os.path.join(base, "d2")
    out_dir = os.path.join(os.path.dirname(base), "figures")
    os.makedirs(out_dir, exist_ok=True)

    print("Generating per-design TVLA plots ...")
    plot_tvla(os.path.join(d1, "tvla_per_cycle.csv"),
              os.path.join(out_dir, "fig_tvla_d1.pdf"), 1)
    plot_tvla(os.path.join(d2, "tvla_per_cycle.csv"),
              os.path.join(out_dir, "fig_tvla_d2.pdf"), 2)

    print("Generating per-design MI plots ...")
    plot_mi_power(os.path.join(d1, "mi_power_per_stage.csv"),
                  os.path.join(out_dir, "fig_mi_d1.pdf"), 1)
    plot_mi_power(os.path.join(d2, "mi_power_per_stage.csv"),
                  os.path.join(out_dir, "fig_mi_d2.pdf"), 2)

    print("Generating per-wire probing MI plots ...")
    plot_probing(os.path.join(d1, "mi_wire.csv"),
                 os.path.join(out_dir, "fig_probing_d1.pdf"), 1)
    plot_probing(os.path.join(d2, "mi_wire.csv"),
                 os.path.join(out_dir, "fig_probing_d2.pdf"), 2)

    print("Generating combined figure ...")
    plot_combined(
        os.path.join(d1, "tvla_per_cycle.csv"),
        os.path.join(d2, "tvla_per_cycle.csv"),
        os.path.join(d1, "mi_power_per_stage.csv"),
        os.path.join(d2, "mi_power_per_stage.csv"),
        os.path.join(out_dir, "fig_combined.pdf"),
    )

    print(f"\nAll figures saved to {out_dir}/")


if __name__ == "__main__":
    main()

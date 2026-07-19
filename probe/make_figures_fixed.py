#!/usr/bin/env python3
"""
make_figures_fixed.py
=====================
Regenerate the paper figures from the corrected (fixed-HD) traces and
bias-aware result CSVs in probe/results/reanalysis/{d1,d2}_fixed/.

Differences from the original figures:
  * MI panels show the plug-in MI bars together with the permutation-null
    99th percentile (red dashed), not the arbitrary 0.05-bit floor.
  * Probing panels show per-wire plug-in max MI with the max null p99.
  * TVLA panels are unchanged in layout but use corrected traces; stages
    with constant HD (zero variance, degenerate t) are marked.

Output: probe/figures_fixed/*.pdf
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "results", "reanalysis")
OUT = os.path.join(HERE, "figures_fixed")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"font.size": 9})


def load_tvla(tag):
    rows = np.loadtxt(os.path.join(BASE, f"{tag}_fixed", "tvla_per_cycle.csv"),
                      delimiter=",", skiprows=1)
    return rows[:, 0].astype(int), rows[:, 1], rows[:, 2]


def load_mi(tag):
    rows = np.loadtxt(os.path.join(BASE, f"{tag}_fixed", "mi_power_per_stage.csv"),
                      delimiter=",", skiprows=1)
    st = rows[rows[:, 0] >= 0]
    return st[:, 0].astype(int), st[:, 1], st[:, 2], st[:, 3]


def load_wire(tag):
    import csv as csvmod
    path = os.path.join(BASE, f"{tag}_fixed", "mi_wire.csv")
    with open(path) as f:
        rd = csvmod.DictReader(f)
        rows = list(rd)
    names = [r["wire_name"] for r in rows]
    mi = np.array([float(r["max_mi_plugin"]) for r in rows])
    mm = np.array([float(r["mi_mm_corrected"]) for r in rows])
    p99 = np.array([float(r["null_p99"]) for r in rows])
    return names, mi, mm, p99


def constant_stages(tag):
    """stages whose HD is (near-)constant: |t| degenerate."""
    st, mi, mm, p99 = load_mi(tag)
    # constant stages have plug-in MI ~< 0.001 and null p99 == 0
    return [s for s, m, p in zip(st, mi, p99) if p == 0.0]


def plot_tvla(tag, order):
    st, tc, tf = load_tvla(tag)
    const = set(constant_stages(tag))
    fig, ax = plt.subplots(figsize=(4.0, 2.6))
    ax.plot(st, tc, "o-", color="#1f77b4", label="Conditional", markersize=4)
    ax.plot(st, tf, "s--", color="#d62728", label="Fixed-vs-Random",
            markersize=4)
    for s in st:
        if s in const:
            ax.axvspan(s - 0.4, s + 0.4, color="gray", alpha=0.12)
    ax.axhline(4.5, color="black", linestyle=":", linewidth=0.8)
    ax.axhline(-4.5, color="black", linestyle=":", linewidth=0.8)
    ax.text(14.0, 4.7, "$|t|=4.5$", ha="right", va="bottom", fontsize=8)
    ax.set_xlabel("Pipeline stage")
    ax.set_ylabel("Welch's $t$")
    ax.set_title(f"TVLA per-stage $t$-statistic ($d={order}$), corrected HD")
    ax.set_xticks(range(0, 23, 3))
    ax.set_ylim(-5.5, 5.5)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    p = os.path.join(OUT, f"fig_tvla_{tag}.pdf")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {p}")


def plot_mi(tag, order):
    st, mi, mm, p99 = load_mi(tag)
    fig, ax = plt.subplots(figsize=(4.0, 2.6))
    bars = ax.bar(st, mi, color="#2ca02c", alpha=0.8, width=0.7,
                  label="plug-in MI")
    max_idx = int(np.argmax(mi))
    bars[max_idx].set_color("#ff7f0e")
    ax.bar(st, mm, color="#08519c", alpha=0.9, width=0.35,
           label="Miller–Madow corrected")
    p99max = p99.max()
    if p99max > 0:
        ax.axhline(p99max, color="red", linestyle="--", linewidth=0.9,
                   label=f"permutation null p99 ({p99max:.3f})")
    ax.set_xlabel("Pipeline stage")
    ax.set_ylabel("$I(\\mathrm{HD}(c); S)$ (bits)")
    ax.set_title(f"Per-stage MI on power trace ($d={order}$), corrected HD")
    ax.set_xticks(range(0, 23, 3))
    ax.legend(loc="upper right", fontsize=7.5, framealpha=0.9)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    p = os.path.join(OUT, f"fig_mi_{tag}.pdf")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {p}")


def plot_probing(tag, order):
    names, mi, mm, p99 = load_wire(tag)
    order_idx = np.argsort(-mi)
    names = [names[i] for i in order_idx]
    mi, mm, p99 = mi[order_idx], mm[order_idx], p99[order_idx]
    xs = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    ax.bar(xs, mi, color="#1f77b4", width=0.7, label="plug-in MI")
    ax.bar(xs, mm, color="#08519c", width=0.3, label="MM corrected")
    ax.axhline(p99.max(), color="red", linestyle="--", linewidth=0.8,
               label=f"null p99 max ({p99.max():.4f})")
    ax.set_xticks(xs)
    ax.set_xticklabels(names, rotation=70, ha="right", fontsize=6)
    ax.set_ylabel("Max $I(w; S)$ (bits)")
    ax.set_title(f"Per-wire mutual information ($d={order}$), bias-aware")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    p = os.path.join(OUT, f"fig_probing_{tag}.pdf")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {p}")


def plot_combined():
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.0))
    for col, (tag, order) in enumerate([("d1", 1), ("d2", 2)]):
        st, tc, tf = load_tvla(tag)
        ax = axes[0, col]
        ax.plot(st, tc, "o-", color="#1f77b4", label="Conditional",
                markersize=3)
        ax.plot(st, tf, "s--", color="#d62728", label="Fixed-vs-Random",
                markersize=3)
        ax.axhline(4.5, color="black", linestyle=":", linewidth=0.7)
        ax.axhline(-4.5, color="black", linestyle=":", linewidth=0.7)
        ax.set_xlabel("Pipeline stage")
        ax.set_ylabel("Welch's $t$")
        ax.set_title(f"TVLA ($d={order}$), corrected HD")
        ax.set_ylim(-5.5, 5.5)
        ax.set_xticks(range(0, 23, 3))
        if col == 0:
            ax.legend(loc="lower right", fontsize=7)
        ax.grid(True, alpha=0.3)

        st, mi, mm, p99 = load_mi(tag)
        ax = axes[1, col]
        ax.bar(st, mi, color="#2ca02c", alpha=0.8, width=0.7,
               label="plug-in MI")
        ax.bar(st, mm, color="#08519c", alpha=0.9, width=0.35,
               label="MM corrected")
        if p99.max() > 0:
            ax.axhline(p99.max(), color="red", linestyle="--", linewidth=0.7,
                       label="null p99")
        ax.set_xlabel("Pipeline stage")
        ax.set_ylabel("$I(\\mathrm{HD}(c); S)$ (bits)")
        ax.set_title(f"MI on power trace ($d={order}$), corrected HD")
        ax.set_xticks(range(0, 23, 3))
        if col == 0:
            ax.legend(loc="upper right", fontsize=7)
        ax.grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    p = os.path.join(OUT, "fig_combined.pdf")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {p}")


def plot_combined_d1():
    """d=1-only variant of the combined figure (fresh rerun data only;
    avoids mixing the stale d=2 panels into the new paper version)."""
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 2.6))
    st, tc, tf = load_tvla("d1")
    ax = axes[0]
    ax.plot(st, tc, "o-", color="#1f77b4", label="Conditional", markersize=3)
    ax.plot(st, tf, "s--", color="#d62728", label="Fixed-vs-Random",
            markersize=3)
    ax.axhline(4.5, color="black", linestyle=":", linewidth=0.7)
    ax.axhline(-4.5, color="black", linestyle=":", linewidth=0.7)
    ax.set_xlabel("Pipeline stage")
    ax.set_ylabel("Welch's $t$")
    ax.set_title("TVLA ($d=1$), 23-stage window")
    ax.set_ylim(-5.5, 5.5)
    ax.set_xticks(range(0, 23, 3))
    ax.legend(loc="lower right", fontsize=7)
    ax.grid(True, alpha=0.3)
    st, mi, mm, p99 = load_mi("d1")
    ax = axes[1]
    ax.bar(st, mi, color="#2ca02c", alpha=0.8, width=0.7, label="plug-in MI")
    ax.bar(st, mm, color="#08519c", alpha=0.9, width=0.35,
           label="MM corrected")
    if p99.max() > 0:
        ax.axhline(p99.max(), color="red", linestyle="--", linewidth=0.7,
                   label="null p99")
    ax.set_xlabel("Pipeline stage")
    ax.set_ylabel("$I(\\mathrm{HD}(c); S)$ (bits)")
    ax.set_title("MI on power trace ($d=1$), 23-stage window")
    ax.set_xticks(range(0, 23, 3))
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    p = os.path.join(OUT, "fig_combined_d1.pdf")
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {p}")


def main():
    print("Generating corrected TVLA plots ...")
    plot_tvla("d1", 1)
    plot_tvla("d2", 2)
    print("Generating corrected MI plots ...")
    plot_mi("d1", 1)
    plot_mi("d2", 2)
    print("Generating bias-aware probing plots ...")
    plot_probing("d1", 1)
    plot_probing("d2", 2)
    print("Generating combined figure ...")
    plot_combined()
    plot_combined_d1()
    print(f"\nAll figures saved to {OUT}/")


if __name__ == "__main__":
    main()

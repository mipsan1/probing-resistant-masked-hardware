#!/usr/bin/env python3
"""
sensitivity_fixed.py
====================
Sample-size sensitivity of the four reported metrics, recomputed on the
*corrected* HD power traces and regenerated DFF bit traces with proper
first_cycle alignment and Miller-Madow bias correction.

For N in {1000, 2000, 5000, 10000} (sub-sampling the same 10,000-triple
traces):
  (a) max single-wire plug-in MI + MM-corrected (bit trace)
  (b) max 2-wire joint plug-in MI + MM-corrected (bit trace, top-10 wires)
  (c) TVLA max |t| (conditional / fixed-vs-random, genuine-variance stages)
  (d) max per-bit MI on the power trace (plug-in + MM-corrected)

Outputs:
  probe/results/reanalysis/{tag}_fixed/sensitivity_fixed.csv
  probe/figures_fixed/fig_sensitivity_{d1,d2}.pdf
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reanalysis as R  # noqa: E402

BASE = os.path.join(HERE, "results", "reanalysis")
FIGDIR = os.path.join(HERE, "figures_fixed")
os.makedirs(FIGDIR, exist_ok=True)

SIZES = [1000, 2000, 5000, 10000]
N_OFF = 23  # new 17-cycle design: 23 cycles/triple spacing
OUT_STAGE = 18  # verified output stage (y0^y1 == SBOX(S), valid_out)


def load_bittrace(path):
    rows = np.loadtxt(path, dtype=str)
    return np.array([[int(c) for c in line] for line in rows], dtype=np.int8)


def panel_ab(bit, secrets, fc, N):
    """max single-wire MI (plug-in + MM at argmax) and max joint MI."""
    sec = secrets[:N]
    f = fc[:N]
    n_bits = bit.shape[1]
    per_wire_max = np.zeros(n_bits)
    for off in range(N_OFF):
        idx = np.minimum(f + off, bit.shape[0] - 1)
        al = bit[idx]
        for w in range(n_bits):
            mi, _, _ = R.mi_plugin(al[:, w], sec)
            if mi > per_wire_max[w]:
                per_wire_max[w] = mi
    w_max = int(np.argmax(per_wire_max))
    # MM correction at the worst wire/offset
    best = (0.0, 0.0)
    for off in range(N_OFF):
        idx = np.minimum(f + off, bit.shape[0] - 1)
        mi, bias, corr = R.mi_miller_madow(bit[idx, w_max], sec)
        if mi > best[0]:
            best = (mi, corr)
    single_plugin, single_mm = per_wire_max[w_max], best[1]

    top10 = np.argsort(-per_wire_max)[:10]
    idx = np.minimum(f + OUT_STAGE, bit.shape[0] - 1)
    al = bit[idx]
    joint_plugin, joint_mm = 0.0, 0.0
    for i in top10:
        for j in range(n_bits):
            if i == j:
                continue
            mi, bias, corr = R.mi_miller_madow(al[:, i] * 2 + al[:, j], sec)
            if mi > joint_plugin:
                joint_plugin, joint_mm = mi, corr
    return float(single_plugin), float(single_mm), \
        float(joint_plugin), float(joint_mm)


def panel_c(hd, secrets, fc, N):
    sec = secrets[:N]
    f = fc[:N]
    M = R.stage_matrix(hd, f, n_offsets=N_OFF)
    tc_max = tf_max = 0.0
    for off in range(N_OFF):
        col = M[:, off]
        if len(np.unique(col)) < 3:
            continue  # degenerate stage
        tc = abs(R.welch_t(col[sec < 0x80], col[sec >= 0x80]))
        tf = abs(R.welch_t(col[sec == 0x00], col[sec != 0x00]))
        tc_max, tf_max = max(tc_max, tc), max(tf_max, tf)
    return tc_max, tf_max, int((sec == 0).sum())


def panel_d(hd, secrets, fc, N):
    sec = secrets[:N]
    f = fc[:N]
    M = R.stage_matrix(hd, f, n_offsets=N_OFF)
    best_p, best_m = 0.0, 0.0
    for off in range(N_OFF):
        col = M[:, off]
        if len(np.unique(col)) < 3:
            continue
        for b in range(8):
            sb = (sec >> b) & 1
            mi, bias, corr = R.mi_miller_madow(col, sb)
            if mi > best_p:
                best_p, best_m = mi, corr
    return best_p, best_m


def run(tag, n_shares):
    cycles, hd = R.load_power(os.path.join(BASE, f"{tag}_power_fixed.txt"))
    rows = R.load_header(os.path.join(BASE, f"{tag}_header_fixed.txt"),
                         n_shares)
    sec_p = np.array([r[0] for r in rows], dtype=np.int64)
    fc = np.array([r[2] for r in rows], dtype=np.int64)
    bit = load_bittrace(os.path.join(BASE, f"{tag}_bittrace.txt"))
    # bit header rows are "secret s0 s1 [s2]" hex, no first_cycle column
    sec_b = np.array(
        [int(l.split()[0], 16) for l in
         open(os.path.join(BASE, f"{tag}_bitheader.txt"))
         if l.strip() and not l.startswith("#")], dtype=np.int64)

    out = []
    for N in SIZES:
        sp, sm, jp, jm = panel_ab(bit, sec_b, fc, N)
        tc, tf, nfix = panel_c(hd, sec_p, fc, N)
        bp, bm = panel_d(hd, sec_p, fc, N)
        out.append(dict(N=N, single_plugin=sp, single_mm=sm,
                        joint_plugin=jp, joint_mm=jm,
                        t_cond=tc, t_fixed=tf, fixed_group=nfix,
                        bit_plugin=bp, bit_mm=bm))
        print(f"  [{tag}] N={N}: wire {sp:.4f}/{sm:.4f} joint {jp:.4f}/{jm:.4f} "
              f"|t| {tc:.2f}/{tf:.2f} (nfix {nfix}) bit {bp:.4f}/{bm:.4f}")

    csv_path = os.path.join(BASE, f"{tag}_fixed", "sensitivity_fixed.csv")
    with open(csv_path, "w") as fh:
        fh.write("N,single_plugin,single_mm,joint_plugin,joint_mm,"
                 "t_cond,t_fixed,fixed_group,bit_plugin,bit_mm\n")
        for r in out:
            fh.write(",".join(str(r[k]) for k in
                              ["N", "single_plugin", "single_mm",
                               "joint_plugin", "joint_mm", "t_cond",
                               "t_fixed", "fixed_group", "bit_plugin",
                               "bit_mm"]) + "\n")
    print(f"  -> {csv_path}")
    return out


def make_figure(tag, order, res):
    Ns = [r["N"] for r in res]
    fig, axes = plt.subplots(2, 2, figsize=(7.5, 5.0))
    Ns_arr = np.array(Ns, dtype=float)

    # bias floors (plug-in estimator, this bin structure)
    floor_single = 255.0 / (2 * Ns_arr * np.log(2))          # 2x256 cells
    floor_joint = 3 * 255.0 / (2 * Ns_arr * np.log(2))       # 4x256 cells
    floor_bit = 24.0 / (2 * Ns_arr * np.log(2))              # ~25x2 cells

    ax = axes[0, 0]
    ax.plot(Ns, [r["single_plugin"] for r in res], "o-", color="#1f77b4",
            label="plug-in")
    ax.plot(Ns, [r["single_mm"] for r in res], "s--", color="#08519c",
            label="MM corrected")
    ax.plot(Ns, floor_single, ":", color="red",
            label="bias floor $(K{-}1)/2N\\ln2$")
    ax.set_xscale("log"); ax.set_xlabel("$N$ (triples)")
    ax.set_ylabel("max $I(w; S)$ (bits)")
    ax.set_title(f"(a) single-wire MI ($d={order}$)")
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

    ax = axes[0, 1]
    ax.plot(Ns, [r["joint_plugin"] for r in res], "o-", color="#d62728",
            label="plug-in")
    ax.plot(Ns, [r["joint_mm"] for r in res], "s--", color="#08519c",
            label="MM corrected")
    ax.plot(Ns, floor_joint, ":", color="red", label="bias floor")
    ax.set_xscale("log"); ax.set_xlabel("$N$ (triples)")
    ax.set_ylabel("max $I(w_i, w_j; S)$ (bits)")
    ax.set_title(f"(b) 2-wire joint MI ($d={order}$)")
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

    ax = axes[1, 0]
    ax.plot(Ns, [r["t_cond"] for r in res], "o-", color="#1f77b4",
            label="Conditional")
    ax.plot(Ns, [r["t_fixed"] for r in res], "s--", color="#d62728",
            label="Fixed-vs-Random")
    ax.axhline(4.5, color="black", linestyle=":", linewidth=0.8)
    ax.set_xscale("log"); ax.set_xlabel("$N$ (triples)")
    ax.set_ylabel("max $|t|$")
    ax.set_title(f"(c) TVLA max $|t|$ ($d={order}$)")
    ax.legend(fontsize=7, loc="lower right"); ax.grid(True, alpha=0.3)

    ax = axes[1, 1]
    ax.plot(Ns, [r["bit_plugin"] for r in res], "^-", color="#2ca02c",
            label="plug-in")
    ax.plot(Ns, [r["bit_mm"] for r in res], "v--", color="#08519c",
            label="MM corrected")
    ax.plot(Ns, floor_bit, ":", color="red", label="bias floor")
    ax.set_xscale("log"); ax.set_xlabel("$N$ (triples)")
    ax.set_ylabel("max per-bit MI (bits)")
    ax.set_title(f"(d) per-bit MI on power trace ($d={order}$)")
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3)

    fig.tight_layout()
    path = os.path.join(FIGDIR, f"fig_sensitivity_{tag}.pdf")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {path}")


def main():
    for tag, order, ns in [("d1", 1, 2)]:  # d1-only rerun; d2 outputs untouched
        print(f"=== {tag} ===")
        res = run(tag, ns)
        make_figure(tag, order, res)


if __name__ == "__main__":
    main()

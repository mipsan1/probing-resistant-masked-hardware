#!/usr/bin/env python3
"""
reanalysis.py
=============
Reviewer-driven reanalysis of the TVLA / MI results reported in the
manuscript, on the *real* N=10,000 gate-level traces:

  probe/results/d1/fo_power.txt      (cycle, hd)   d=1
  probe/results/d1/fo_power_header.txt  (secret s0 s1 first_cycle)
  probe/results/d2/d2_power.txt      (cycle, hd)   d=2
  probe/results/d2/d2_power_header.txt  (secret s0 s1 s2 first_cycle)

Answers five questions:

  Q1. Why are the reported max|t| values exactly 0 / +/-1.0000 ?
      -> per-stage HD variance / unique-value diagnostics; classify each
         stage as constant, single-outlier (degenerate t), or genuine.

  Q2. Higher-order TVLA: centered 2nd- and 3rd-moment Welch t-tests
      (Schneider-Moradi style), conditional and fixed-vs-random splits.

  Q3. Are the reported MI values (0.025 wire-MI, 0.21/0.35 stage-MI)
      distinguishable from plug-in estimator bias?
      -> Miller-Madow-corrected MI + permutation null distribution
         (500 shuffles, 95th/99th percentile).

  Q4. What drives the stage-12 (and stage-2) MI spike?
      -> least-squares decomposition of HD(stage) onto HW(S), HW(s0),
         HW(s1) (resp. s2), and constants; plus null-test of the
         conditional means.

  Q5. Trace geometry: cycles per triple, alignment, max HD vs. the
      number of monitored wires.

Output: probe/results/reanalysis/reanalysis_report.md + console summary.
"""

import os
import numpy as np

RNG = np.random.default_rng(20260719)
N_PERM = 500

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "results", "reanalysis")
os.makedirs(OUT, exist_ok=True)

DESIGNS = [
    ("d1", os.environ.get("D1_POWER",
                          os.path.join(HERE, "results", "d1", "fo_power.txt")),
     os.environ.get("D1_HEADER",
                    os.path.join(HERE, "results", "d1", "fo_power_header.txt")),
     2),
    ("d2", os.environ.get("D2_POWER",
                          os.path.join(HERE, "results", "d2", "d2_power.txt")),
     os.environ.get("D2_HEADER",
                    os.path.join(HERE, "results", "d2", "d2_power_header.txt")),
     3),
]


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------

def load_power(path):
    data = np.loadtxt(path, dtype=np.int64)
    return data[:, 0], data[:, 1]


def load_header(path, n_shares):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            secret = int(p[0], 16)
            shares = [int(x, 16) for x in p[1:1 + n_shares]]
            first_cycle = int(p[-1])
            rows.append((secret, shares, first_cycle))
    return rows


def stage_matrix(hd, first_cycles, n_offsets=16):
    n = len(first_cycles)
    out = np.zeros((n, n_offsets), dtype=np.float64)
    for i, fc in enumerate(first_cycles):
        for off in range(n_offsets):
            idx = fc + off
            out[i, off] = hd[idx] if idx < len(hd) else hd[-1]
    return out


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------

def welch_t(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    m0, v0 = a.mean(), a.var(ddof=1)
    m1, v1 = b.mean(), b.var(ddof=1)
    den = np.sqrt(v0 / len(a) + v1 / len(b))
    return (m0 - m1) / den if den > 0 else 0.0


def hw8(v):
    return np.array([bin(int(x)).count("1") for x in v], dtype=np.float64)


def mi_plugin(x, y):
    """plug-in MI (bits) on empirical joint, no smoothing."""
    x = np.asarray(x)
    y = np.asarray(y)
    ux = np.unique(x)
    uy = np.unique(y)
    xi = np.searchsorted(ux, x)
    yi = np.searchsorted(uy, y)
    Kx, Ky = len(ux), len(uy)
    joint = np.zeros((Kx, Ky))
    np.add.at(joint, (xi, yi), 1.0)
    joint /= joint.sum()
    px = joint.sum(1, keepdims=True)
    py = joint.sum(0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = joint * np.log2(joint / (px * py))
    t[~np.isfinite(t)] = 0.0
    return float(t.sum()), Kx, Ky


def mi_miller_madow(x, y):
    mi, Kx, Ky = mi_plugin(x, y)
    bias = ((Kx - 1) * (Ky - 1)) / (2.0 * len(x) * np.log(2))
    return mi, bias, max(0.0, mi - bias)


def mi_perm_null(x, y, n_perm=N_PERM):
    """null distribution of plug-in MI under independence (shuffle y)."""
    y = np.asarray(y)
    nulls = np.empty(n_perm)
    for k in range(n_perm):
        nulls[k], _, _ = mi_plugin(x, RNG.permutation(y))
    return nulls


# ---------------------------------------------------------------------------
# per-design analysis
# ---------------------------------------------------------------------------

def analyze(tag, power_path, header_path, n_shares, report):
    cycles, hd = load_power(power_path)
    rows = load_header(header_path, n_shares)
    secrets = np.array([r[0] for r in rows], dtype=np.int64)
    shares = np.array([r[1] for r in rows], dtype=np.int64)   # (N, n_shares)
    first_cycles = np.array([r[2] for r in rows], dtype=np.int64)
    n = len(rows)

    spacing = np.diff(first_cycles)
    report.append(f"\n# Design {tag}\n")
    report.append(f"- cycles: {len(hd)}, triples: {n}\n")
    report.append(f"- first_cycle spacing: unique {sorted(set(spacing.tolist()))}\n")
    report.append(f"- HD range: [{hd.min()}, {hd.max()}]\n")
    report.append(f"- distinct secrets: {len(np.unique(secrets))}/256, "
                  f"fixed group (S=0x00) size: {int((secrets == 0).sum())}\n")

    M = stage_matrix(hd, first_cycles, n_offsets=16)

    # ---------------- Q1: degenerate-stage diagnostics ----------------
    report.append("\n## Q1. Per-stage HD distribution (degenerate t-test diagnosis)\n\n")
    report.append("| stage | nunique | var | min | max | t_cond | t_fixed | class |\n")
    report.append("|---|---|---|---|---|---|---|---|\n")
    genuine = []
    for off in range(16):
        col = M[:, off]
        nun = len(np.unique(col))
        tc = welch_t(col[secrets < 0x80], col[secrets >= 0x80])
        tf = welch_t(col[secrets == 0x00], col[secrets != 0x00])
        if nun == 1:
            cls = "CONSTANT"
        elif abs(abs(tc) - 1.0) < 1e-9 or abs(abs(tf) - 1.0) < 1e-9:
            cls = "SINGLE-OUTLIER (|t|=1 artifact)"
        else:
            cls = "GENUINE"
            genuine.append(off)
        report.append(f"| {off} | {nun} | {col.var():.4f} | {col.min():.0f} "
                      f"| {col.max():.0f} | {tc:+.4f} | {tf:+.4f} | {cls} |\n")
    report.append(f"\nStages with genuine HD variance: {genuine}\n")

    # ---------------- Q2: higher-order TVLA ----------------
    report.append("\n## Q2. Higher-order TVLA (centered moments, Welch t)\n\n")
    report.append("| stage | order | t_cond | t_fixed |\n")
    report.append("|---|---|---|---|\n")
    for off in range(16):
        col = M[:, off]
        if len(np.unique(col)) < 2:
            continue
        c = col - col.mean()
        for order in (1, 2, 3):
            z = col if order == 1 else c ** order
            tc = welch_t(z[secrets < 0x80], z[secrets >= 0x80])
            tf = welch_t(z[secrets == 0x00], z[secrets != 0x00])
            report.append(f"| {off} | {order} | {tc:+.4f} | {tf:+.4f} |\n")

    # ---------------- Q3: MI bias analysis ----------------
    report.append("\n## Q3. MI: plug-in vs Miller-Madow bias vs permutation null\n\n")
    report.append(f"(permutation null: {N_PERM} shuffles of S; "
                  "p95/p99 = null percentiles)\n\n")
    report.append("| stage | plug-in MI | MM bias | MM-corrected | null p95 | null p99 | null max |\n")
    report.append("|---|---|---|---|---|---|---|\n")
    mi_summary = {}
    for off in range(16):
        col = M[:, off]
        mi, bias, corr = mi_miller_madow(col, secrets)
        if len(np.unique(col)) < 2:
            report.append(f"| {off} | {mi:.4f} | {bias:.4f} | {corr:.4f} "
                          f"| - | - | - |\n")
            continue
        nulls = mi_perm_null(col, secrets)
        p95, p99, pmax = np.percentile(nulls, [95, 99]), None, None
        p95, p99 = np.percentile(nulls, 95), np.percentile(nulls, 99)
        pmax = nulls.max()
        mi_summary[off] = (mi, bias, corr, p95, p99, pmax)
        report.append(f"| {off} | {mi:.4f} | {bias:.4f} | {corr:.4f} "
                      f"| {p95:.4f} | {p99:.4f} | {pmax:.4f} |\n")

    # full-trace MI (all 16 stages flattened)
    hd_flat = M.flatten()
    sec_flat = np.tile(secrets, 16)
    mi_f, bias_f, corr_f = mi_miller_madow(hd_flat, sec_flat)
    nulls_f = mi_perm_null(hd_flat, sec_flat, n_perm=100)
    report.append(f"\nFull-trace MI: plug-in {mi_f:.4f}, MM bias {bias_f:.4f}, "
                  f"MM-corrected {corr_f:.4f}, null p99 "
                  f"{np.percentile(nulls_f, 99):.4f}, null max {nulls_f.max():.4f}\n")

    # per-bit MI at the output stage = stage with max y-variance; use all stages
    report.append("\nPer-bit MI at every stage with genuine variance "
                  "(plug-in / MM-corrected):\n\n")
    report.append("| stage | bit | plug-in | MM-corrected | null p99 |\n")
    report.append("|---|---|---|---|---|\n")
    for off in genuine:
        for b in range(8):
            sb = (secrets >> b) & 1
            mi, bias, corr = mi_miller_madow(M[:, off], sb)
            nulls = mi_perm_null(M[:, off], sb, n_perm=100)
            report.append(f"| {off} | {b} | {mi:.4f} | {corr:.4f} "
                          f"| {np.percentile(nulls, 99):.4f} |\n")

    # ---------------- Q4: decomposition of genuine stages ----------------
    report.append("\n## Q4. What drives the HD at genuine stages?\n\n")
    report.append("Least-squares R^2 of HD(stage) on Hamming weights of "
                  "secret / shares, and correlation of E[HD|S=s] with HW(s).\n\n")
    report.append("| stage | corr(HD, HW(S)) | corr(HD, HW(share0)) | "
                  "corr(HD, HW(share_last)) | corr(E[HD\\|S], HW(S)) |\n")
    report.append("|---|---|---|---|---|\n")
    for off in genuine:
        col = M[:, off]
        c_hwS = np.corrcoef(col, hw8(secrets))[0, 1]
        c_hw0 = np.corrcoef(col, hw8(shares[:, 0]))[0, 1]
        c_hwl = np.corrcoef(col, hw8(shares[:, -1]))[0, 1]
        # conditional mean curve vs HW(S)
        m_s = np.array([col[secrets == s].mean() if (secrets == s).any()
                        else np.nan for s in range(256)])
        valid = ~np.isnan(m_s)
        c_curve = np.corrcoef(m_s[valid], hw8(np.arange(256))[valid])[0, 1]
        report.append(f"| {off} | {c_hwS:+.4f} | {c_hw0:+.4f} | "
                      f"{c_hwl:+.4f} | {c_curve:+.4f} |\n")

    # ---------------- Q5: geometry ----------------
    report.append("\n## Q5. Geometry\n\n")
    report.append(f"- max HD observed = {hd.max()} (monitored wires in "
                  f"testbench: {'27' if tag == 'd1' else '35'})\n")
    report.append(f"- cycles/triple = {len(hd) / n:.2f}\n")

    console = {
        "tag": tag,
        "genuine": genuine,
        "mi": mi_summary,
        "full": (mi_f, bias_f, corr_f,
                 float(np.percentile(nulls_f, 99)), float(nulls_f.max())),
    }
    return console


def main():
    report = ["# Reanalysis Report (reviewer-driven)\n",
              "Traces: probe/results/d{1,2}/ (N=10,000 gate-level, "
              "Hamming-distance over monitored DFF wires)\n"]
    summaries = []
    for tag, pp, hp, ns in DESIGNS:
        print(f"=== analyzing {tag} ===")
        summaries.append(analyze(tag, pp, hp, ns, report))

    rpt_path = os.path.join(OUT, "reanalysis_report.md")
    with open(rpt_path, "w") as f:
        f.writelines(report)
    print(f"\nwrote {rpt_path}")

    print("\n" + "=" * 72)
    print("CONSOLE SUMMARY")
    print("=" * 72)
    for s in summaries:
        print(f"\n[{s['tag']}] genuine-variance stages: {s['genuine']}")
        for off, (mi, bias, corr, p95, p99, pmax) in s["mi"].items():
            flag = "ABOVE-NULL" if mi > pmax else "within-null"
            print(f"  stage {off:2d}: plug-in {mi:.4f} | MM-bias {bias:.4f} "
                  f"| MM-corr {corr:.4f} | null p99 {p99:.4f} "
                  f"max {pmax:.4f} -> {flag}")
        mi_f, bias_f, corr_f, p99f, maxf = s["full"]
        print(f"  full-trace: plug-in {mi_f:.4f} | MM-corr {corr_f:.4f} "
              f"| null p99 {p99f:.4f} max {maxf:.4f}")


if __name__ == "__main__":
    main()

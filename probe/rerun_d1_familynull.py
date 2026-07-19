#!/usr/bin/env python3
"""
rerun_d1_familynull.py
======================
Family-wise (max-statistic) permutation nulls for the N=10,000 d=1 rerun.

The paper compares the MAX plug-in MI over 34 wires x 23 offsets (and over
2-wire pairs) against a null.  A per-test null p99 is invalid for a max over
782 / ~12k tests, so we compute the permutation distribution of the MAX
statistic itself (300 shuffles, RNG seed 20260719).

Also recomputes the observed pair max with the structural share-recombination
exclusion done correctly: pairs (y0_out[i], y1_out[i]) excluded at ALL
output-hold offsets 18..22 (the y registers hold from offset 18 until the
next triple), not just offset 18.

Fast path: bincount-based plug-in MI (identical counts to
reanalysis.mi_plugin, verified against it on the observed maxima).
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reanalysis as R  # noqa: E402  (RNG seeded 20260719)

BASE = os.path.join(HERE, "results", "reanalysis")
N_OFF = 23
OUT_STAGE = 18
N_PERM = 300
N_BITS = 34
STRUCT_PAIRS = {(17 + i, 25 + i) for i in range(8)}
STRUCT_OFFS = set(range(OUT_STAGE, N_OFF))  # 18..22 output-hold window


def mi_from_counts(cnt, N):
    p = cnt / N
    px = p.sum(axis=1, keepdims=True)
    py = p.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = p * np.log2(p / (px @ py))
    t[~np.isfinite(t)] = 0.0
    return float(t.sum())


def mi_bin(code, sec, K):
    """plug-in MI between integer code (0..K-1) and secret (0..255)."""
    cnt = np.bincount(code * 256 + sec, minlength=K * 256)
    return mi_from_counts(cnt.reshape(K, 256).astype(np.float64), len(sec))


def main():
    rows = R.load_header(os.path.join(BASE, "d1_bitheader.txt"), 2)
    sec = np.array([r[0] for r in rows], dtype=np.int64)
    fc = np.array([r[2] for r in rows], dtype=np.int64)
    bt = np.loadtxt(os.path.join(BASE, "d1_bittrace.txt"), dtype=str)
    bit = np.array([[int(c) for c in line] for line in bt], dtype=np.int8)
    n = len(sec)

    # aligned wire arrays per offset: A[off] -> (n, 34) int8
    A = np.empty((N_OFF, n, N_BITS), dtype=np.int8)
    for off in range(N_OFF):
        A[off] = bit[np.minimum(fc + off, len(bit) - 1)]

    # ---------------- single-wire observed + family null ---------------
    obs_w = np.zeros((N_OFF, N_BITS))
    for off in range(N_OFF):
        for w in range(N_BITS):
            obs_w[off, w] = mi_bin(A[off][:, w].astype(np.int64), sec, 2)
    wo, ww = np.unravel_index(np.argmax(obs_w), obs_w.shape)
    print(f"single-wire observed max {obs_w[wo, ww]:.6f} "
          f"(wire {ww} @ off {wo})")
    # cross-check with reanalysis.mi_plugin
    mi_chk, _, _ = R.mi_plugin(A[wo][:, ww], sec)
    print(f"  cross-check via mi_plugin: {mi_chk:.6f}")

    null_max_w = np.empty(N_PERM)
    for k in range(N_PERM):
        sp = R.RNG.permutation(sec)
        m = 0.0
        for off in range(N_OFF):
            for w in range(N_BITS):
                v = mi_bin(A[off][:, w].astype(np.int64), sp, 2)
                if v > m:
                    m = v
        null_max_w[k] = m
        if (k + 1) % 100 == 0:
            print(f"  wire null {k + 1}/{N_PERM} ...")
    p99w = float(np.percentile(null_max_w, 99))
    pval_w = float((null_max_w >= obs_w[wo, ww]).mean())
    print(f"  family null max-statistic: p99 {p99w:.6f}, "
          f"max {null_max_w.max():.6f}; observed {obs_w[wo, ww]:.6f} "
          f"-> empirical p {pval_w:.4f}")

    # ---------------- pair codes ---------------------------------------
    pairs = [(i, j) for i in range(N_BITS) for j in range(i + 1, N_BITS)]
    pair_is_struct = np.array([(i, j) in STRUCT_PAIRS for i, j in pairs])
    # C[off] -> (n, 561) int8 joint code
    C = np.empty((N_OFF, n, len(pairs)), dtype=np.int8)
    for off in range(N_OFF):
        a = A[off].astype(np.int16)
        for k, (i, j) in enumerate(pairs):
            C[off, :, k] = (a[:, i] * 2 + a[:, j]).astype(np.int8)

    keep = np.ones((N_OFF, len(pairs)), dtype=bool)
    for off in STRUCT_OFFS:
        keep[off, pair_is_struct] = False

    obs_p = np.full((N_OFF, len(pairs)), -1.0)
    for off in range(N_OFF):
        for k in range(len(pairs)):
            obs_p[off, k] = mi_bin(C[off][:, k].astype(np.int64), sec, 4)
    # global max and non-structural max
    go, gk = np.unravel_index(np.argmax(obs_p), obs_p.shape)
    print(f"\npair observed GLOBAL max {obs_p[go, gk]:.6f} "
          f"(pair {pairs[gk]} @ off {go})")
    masked = np.where(keep, obs_p, -1.0)
    no, nk = np.unravel_index(np.argmax(masked), masked.shape)
    print(f"pair observed NON-STRUCT max {obs_p[no, nk]:.6f} "
          f"(pair {pairs[nk]} @ off {no})")
    mi_chk, _, _ = R.mi_plugin(C[no][:, nk], sec)
    print(f"  cross-check via mi_plugin: {mi_chk:.6f}")

    null_max_p = np.empty(N_PERM)
    for k in range(N_PERM):
        sp = R.RNG.permutation(sec)
        m = 0.0
        for off in range(N_OFF):
            ks = np.nonzero(keep[off])[0]
            for kk in ks:
                v = mi_bin(C[off][:, kk].astype(np.int64), sp, 4)
                if v > m:
                    m = v
        null_max_p[k] = m
        if (k + 1) % 50 == 0:
            print(f"  pair null {k + 1}/{N_PERM} ...")
    p99p = float(np.percentile(null_max_p, 99))
    pval_p = float((null_max_p >= obs_p[no, nk]).mean())
    print(f"  family null max-statistic (non-struct): p99 {p99p:.6f}, "
          f"max {null_max_p.max():.6f}; observed {obs_p[no, nk]:.6f} "
          f"-> empirical p {pval_p:.4f}")

    out = {
        "wire_obs_max": float(obs_w[wo, ww]), "wire_off": int(wo),
        "wire_idx": int(ww),
        "wire_family_p99": p99w, "wire_family_max": float(null_max_w.max()),
        "wire_family_pval": pval_w,
        "pair_global": {"pair": pairs[gk], "off": int(go),
                        "mi": float(obs_p[go, gk])},
        "pair_nostruct": {"pair": pairs[nk], "off": int(no),
                          "mi": float(obs_p[no, nk])},
        "pair_family_p99": p99p, "pair_family_max": float(null_max_p.max()),
        "pair_family_pval": pval_p,
    }
    import json
    with open(os.path.join(BASE, "d1_fixed", "family_nulls.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote family_nulls.json")


if __name__ == "__main__":
    main()

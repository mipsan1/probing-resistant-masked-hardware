#!/usr/bin/env python3
"""
rerun_d1_analysis.py
====================
N=10,000 re-run analysis for the NEW first-order masked AES S-box
(17-cycle latency, valid_pipe[16:0], r0..r6) on the gate-level netlist
syn/masked_sbox_first_order_sim_netlist.v (818 DFFs).

Inputs (fresh, chunked gate-level runs merged + verified):
  probe/results/reanalysis/d1_bittrace.txt    230,002 rows x 34 bits
  probe/results/reanalysis/d1_bitheader.txt   secret s0 s1 fc   (seed CAFEBABE)
  probe/results/reanalysis/d1_power_fixed.txt cycle hd          (seed CAFEFACE)
  probe/results/reanalysis/d1_header_fixed.txt secret s0 s1 fc

Geometry (verified): 23 cycles/triple, fc(t) = 2 + 23 t, output stage 18.
Monitored wires: 34.  Pipeline offsets: 23 (0..22).

Estimator (identical to reanalysis.py / regen_results.py):
  plug-in MI (no smoothing), Miller-Madow correction,
  permutation null p99 (300 shuffles, RNG seed 20260719).

Outputs:
  probe/results/reanalysis/d1_fixed/{tvla_per_cycle, tvla_higher_order,
      mi_power_per_stage, mi_power_per_bit, mi_wire, mi_pair}.csv
  probe/results/reanalysis/d1_fixed/summary_d1_rerun.json
  probe/results/d1/{same CSVs}
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reanalysis as R  # noqa: E402  (RNG seeded 20260719)

BASE = os.path.join(HERE, "results", "reanalysis")
OUT_FIXED = os.path.join(BASE, "d1_fixed")
OUT_D1 = os.path.join(HERE, "results", "d1")
os.makedirs(OUT_FIXED, exist_ok=True)
os.makedirs(OUT_D1, exist_ok=True)

N_OFF = 23          # pipeline offsets 0..22 (23 cycles/triple spacing)
OUT_STAGE = 18      # verified: y0^y1 == SBOX(S) and valid_out high here
N_PERM = 300

NAMES = ([f"valid_pipe[{i}]" for i in range(17)]
         + [f"y0_out[{i}]" for i in range(8)]
         + [f"y1_out[{i}]" for i in range(8)]
         + ["valid_out"])
N_BITS = len(NAMES)  # 34

# structural share-recombination pairs at the output stage:
# (y0_out[i], y1_out[i]) at offset OUT_STAGE carry ~1 bit by construction
STRUCT_PAIRS = {(17 + i, 25 + i) for i in range(8)}


def load_bit():
    rows = R.load_header(os.path.join(BASE, "d1_bitheader.txt"), 2)
    secrets = np.array([r[0] for r in rows], dtype=np.int64)
    fc = np.array([r[2] for r in rows], dtype=np.int64)
    bt = np.loadtxt(os.path.join(BASE, "d1_bittrace.txt"), dtype=str)
    bit = np.array([[int(c) for c in line] for line in bt], dtype=np.int8)
    return bit, secrets, fc


def load_pow():
    cycles, hd = R.load_power(os.path.join(BASE, "d1_power_fixed.txt"))
    rows = R.load_header(os.path.join(BASE, "d1_header_fixed.txt"), 2)
    secrets = np.array([r[0] for r in rows], dtype=np.int64)
    fc = np.array([r[2] for r in rows], dtype=np.int64)
    return hd, secrets, fc


def aligned(bit, fc, off):
    idx = np.minimum(fc + off, len(bit) - 1)
    return bit[idx]


def main():
    bit, sec_b, fc_b = load_bit()
    hd, sec_p, fc_p = load_pow()
    n = len(sec_b)
    assert len(sec_p) == n == 10000
    assert bit.shape == (230002, 34), bit.shape
    assert (fc_b == 2 + 23 * np.arange(n)).all()
    assert (fc_p == 2 + 23 * np.arange(n)).all()
    print(f"N={n} triples; bit trace {bit.shape}; "
          f"power rows {len(hd)}; HD range [{hd.min()},{hd.max()}]")
    print(f"distinct secrets: probe {len(np.unique(sec_b))}/256, "
          f"power {len(np.unique(sec_p))}/256")

    S = {}  # summary dict

    # ------------------------------------------------------------------
    # A1. single-wire MI, 34 wires x 23 offsets
    # ------------------------------------------------------------------
    print("\n[A1] single-wire MI ...")
    wire_rows = []
    for w in range(N_BITS):
        per_off = np.zeros(N_OFF)
        for off in range(N_OFF):
            al = aligned(bit, fc_b, off)
            per_off[off], _, _ = R.mi_plugin(al[:, w], sec_b)
        worst = int(np.argmax(per_off))
        al = aligned(bit, fc_b, worst)
        mi, bias, corr = R.mi_miller_madow(al[:, w], sec_b)
        nulls = R.mi_perm_null(al[:, w], sec_b, n_perm=N_PERM)
        wire_rows.append((w, NAMES[w], float(per_off[worst]), worst,
                          float(corr), float(np.percentile(nulls, 99))))
    max_wire = max(wire_rows, key=lambda r: r[2])
    S["wire_max"] = dict(name=max_wire[1], off=max_wire[3],
                         plugin=max_wire[2], mm=max_wire[4], p99=max_wire[5])
    S["wire_max_mm"] = max(r[4] for r in wire_rows)
    S["wire_null_p99_max"] = max(r[5] for r in wire_rows)
    print(f"  max: {max_wire[1]} @ off {max_wire[3]}: plug-in "
          f"{max_wire[2]:.6f}, MM {max_wire[4]:.6f}, null p99 {max_wire[5]:.6f}")
    print(f"  max MM-corr {S['wire_max_mm']:.6f}; max null p99 "
          f"{S['wire_null_p99_max']:.6f}")

    # ------------------------------------------------------------------
    # A2. 2-wire joint MI, all 561 pairs x 23 offsets
    # ------------------------------------------------------------------
    print("\n[A2] 2-wire joint MI (all pairs x offsets) ...")
    best = (0.0, -1, -1, -1)          # global max
    best_ns = (0.0, -1, -1, -1)       # max excluding structural pairs@18
    pair_top = []                     # for CSV: top-20 global
    for i in range(N_BITS):
        for j in range(i + 1, N_BITS):
            for off in range(N_OFF):
                al = aligned(bit, fc_b, off)
                joint = al[:, i] * 2 + al[:, j]
                mi, _, _ = R.mi_plugin(joint, sec_b)
                if mi > best[0]:
                    best = (mi, i, j, off)
                if not (off == OUT_STAGE and (i, j) in STRUCT_PAIRS):
                    if mi > best_ns[0]:
                        best_ns = (mi, i, j, off)
                pair_top.append((mi, i, j, off))
    pair_top.sort(key=lambda x: -x[0])

    def pair_stats(mi, i, j, off):
        al = aligned(bit, fc_b, off)
        joint = al[:, i] * 2 + al[:, j]
        mi2, bias, corr = R.mi_miller_madow(joint, sec_b)
        nulls = R.mi_perm_null(joint, sec_b, n_perm=N_PERM)
        return float(corr), float(np.percentile(nulls, 99))

    mi, i, j, off = best
    corr, p99 = pair_stats(mi, i, j, off)
    S["pair_global"] = dict(i=NAMES[i], j=NAMES[j], off=off, plugin=mi,
                            mm=corr, p99=p99)
    print(f"  global max: {NAMES[i]} x {NAMES[j]} @ {off}: plug-in {mi:.6f}, "
          f"MM {corr:.6f}, null p99 {p99:.6f}")
    mi, i, j, off = best_ns
    corr, p99 = pair_stats(mi, i, j, off)
    S["pair_nostruct"] = dict(i=NAMES[i], j=NAMES[j], off=off, plugin=mi,
                              mm=corr, p99=p99)
    print(f"  max excl. structural pairs@18: {NAMES[i]} x {NAMES[j]} @ {off}: "
          f"plug-in {mi:.6f}, MM {corr:.6f}, null p99 {p99:.6f}")

    # ------------------------------------------------------------------
    # B1. TVLA per stage (power trace)
    # ------------------------------------------------------------------
    print("\n[B1] TVLA ...")
    M = R.stage_matrix(hd, fc_p, n_offsets=N_OFF)
    tvla_rows, ho_rows, genuine = [], [], []
    for off in range(N_OFF):
        col = M[:, off]
        tc = R.welch_t(col[sec_p < 0x80], col[sec_p >= 0x80])
        tf = R.welch_t(col[sec_p == 0x00], col[sec_p != 0x00])
        tvla_rows.append((off, tc, tf))
        if len(np.unique(col)) >= 3:
            genuine.append(off)
            c = col - col.mean()
            for order in (1, 2, 3):
                z = col if order == 1 else c ** order
                ho_rows.append((off, order,
                                R.welch_t(z[sec_p < 0x80], z[sec_p >= 0x80]),
                                R.welch_t(z[sec_p == 0x00], z[sec_p != 0x00])))
    g = set(genuine)
    mc = max(abs(r[1]) for r in tvla_rows if r[0] in g)
    mf = max(abs(r[2]) for r in tvla_rows if r[0] in g)
    mc_stage = max((r for r in tvla_rows if r[0] in g), key=lambda r: abs(r[1]))
    mf_stage = max((r for r in tvla_rows if r[0] in g), key=lambda r: abs(r[2]))
    mho2 = max(max(abs(r[2]), abs(r[3])) for r in ho_rows if r[1] == 2)
    mho3 = max(max(abs(r[2]), abs(r[3])) for r in ho_rows if r[1] == 3)
    mho = max(max(abs(r[2]), abs(r[3])) for r in ho_rows)
    S["tvla"] = dict(genuine_stages=genuine, max_cond=mc, max_fixed=mf,
                     cond_stage=[mc_stage[0], mc_stage[1]],
                     fixed_stage=[mf_stage[0], mf_stage[2]],
                     max_ho2=mho2, max_ho3=mho3, max_ho_all=mho)
    print(f"  genuine stages {genuine}")
    print(f"  cond max|t| {mc:.4f} (stage {mc_stage[0]}, t={mc_stage[1]:+.4f}); "
          f"fixed max|t| {mf:.4f} (stage {mf_stage[0]}, t={mf_stage[2]:+.4f})")
    print(f"  higher-order max|t|: 2nd {mho2:.4f}, 3rd {mho3:.4f}, "
          f"all {mho:.4f}")

    # ------------------------------------------------------------------
    # B2. per-stage I(HD;S) + full-trace + per-bit + corr(HD,HW(S))
    # ------------------------------------------------------------------
    print("\n[B2] MI on HD power trace ...")
    mi_rows = []
    for off in range(N_OFF):
        col = M[:, off]
        mi, bias, corr = R.mi_miller_madow(col, sec_p)
        if len(np.unique(col)) >= 3:
            nulls = R.mi_perm_null(col, sec_p, n_perm=N_PERM)
            p99 = float(np.percentile(nulls, 99))
        else:
            p99 = 0.0
        mi_rows.append((off, float(mi), float(corr), p99))
    top_stage = max(mi_rows, key=lambda r: r[1])
    S["mi_stage_max"] = dict(stage=top_stage[0], plugin=top_stage[1],
                             mm=top_stage[2], p99=top_stage[3])
    print(f"  max plug-in stage {top_stage[0]}: {top_stage[1]:.6f} bits, "
          f"MM {top_stage[2]:.6f}, null p99 {top_stage[3]:.6f}")

    col = M[:, top_stage[0]]
    r_hw = float(np.corrcoef(col, R.hw8(sec_p))[0, 1])
    S["mi_stage_max_corr_hw"] = r_hw
    print(f"  corr(HD(stage {top_stage[0]}), HW(S)) = {r_hw:+.4f}")

    hd_flat = M.flatten()
    sec_flat = np.tile(sec_p, N_OFF)
    mi_f, bias_f, corr_f = R.mi_miller_madow(hd_flat, sec_flat)
    S["mi_full"] = dict(plugin=float(mi_f), mm=float(corr_f))
    print(f"  full-trace MI: plug-in {mi_f:.6f}, MM {corr_f:.6f}")

    bit_rows = []
    out_col = M[:, OUT_STAGE]
    for b in range(8):
        sb = (sec_p >> b) & 1
        mi, bias, corr = R.mi_miller_madow(out_col, sb)
        nulls = R.mi_perm_null(out_col, sb, n_perm=N_PERM)
        bit_rows.append((b, float(mi), float(corr),
                         float(np.percentile(nulls, 99))))
    S["mi_bit_max"] = max(bit_rows, key=lambda r: r[1])
    print(f"  per-bit MI @ stage {OUT_STAGE}: max {S['mi_bit_max'][1]:.6f} "
          f"(bit {S['mi_bit_max'][0]}), MM {S['mi_bit_max'][2]:.6f}, "
          f"null p99 {S['mi_bit_max'][3]:.6f}")
    print("  per-bit: " + " ".join(f"{r[1]:.4f}" for r in bit_rows))

    # ------------------------------------------------------------------
    # write CSVs (regen_results schema, both output dirs)
    # ------------------------------------------------------------------
    for outdir in (OUT_FIXED, OUT_D1):
        with open(os.path.join(outdir, "tvla_per_cycle.csv"), "w") as f:
            f.write("stage_offset,t_conditional,t_fixed_vs_random\n")
            for off, tc, tf in tvla_rows:
                f.write(f"{off},{tc:.6f},{tf:.6f}\n")
        with open(os.path.join(outdir, "tvla_higher_order.csv"), "w") as f:
            f.write("stage_offset,moment,t_conditional,t_fixed_vs_random\n")
            for off, o, tc, tf in ho_rows:
                f.write(f"{off},{o},{tc:.6f},{tf:.6f}\n")
        with open(os.path.join(outdir, "mi_power_per_stage.csv"), "w") as f:
            f.write("stage_offset,mi_plugin,mi_mm_corrected,null_p99\n")
            for off, mi, corr, p99 in mi_rows:
                f.write(f"{off},{mi:.6f},{corr:.6f},{p99:.6f}\n")
            f.write(f"-1,{mi_f:.6f},{corr_f:.6f},0.0\n")
        with open(os.path.join(outdir, "mi_power_per_bit.csv"), "w") as f:
            f.write("bit_index,mi_plugin,mi_mm_corrected,null_p99\n")
            for b, mi, corr, p99 in bit_rows:
                f.write(f"{b},{mi:.6f},{corr:.6f},{p99:.6f}\n")
        with open(os.path.join(outdir, "mi_wire.csv"), "w") as f:
            f.write("wire_idx,wire_name,max_mi_plugin,worst_offset,"
                    "mi_mm_corrected,null_p99\n")
            for w, nm, mi, wo, corr, p99 in wire_rows:
                f.write(f"{w},{nm},{mi:.6f},{wo},{corr:.6f},{p99:.6f}\n")
        with open(os.path.join(outdir, "mi_pair.csv"), "w") as f:
            f.write("wire_i,wire_j,wire_i_name,wire_j_name,mi_joint_plugin,"
                    "mi_mm_corrected,null_p99_top,offset\n")
            for k, (mi, i, j, off) in enumerate(pair_top[:20]):
                corr, p99 = pair_stats(mi, i, j, off) if k == 0 else (0.0, 0.0)
                f.write(f"{i},{j},{NAMES[i]},{NAMES[j]},{mi:.6f},"
                        f"{corr:.6f},{p99:.6f},{off}\n")

    with open(os.path.join(OUT_FIXED, "summary_d1_rerun.json"), "w") as f:
        json.dump(S, f, indent=2, default=float)
    print(f"\nwrote CSVs -> {OUT_FIXED} and {OUT_D1}")
    print(json.dumps(S, indent=2, default=float))


if __name__ == "__main__":
    main()

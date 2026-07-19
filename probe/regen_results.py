#!/usr/bin/env python3
"""
regen_results.py
================
Regenerate all paper-facing result CSVs from the *corrected* HD power
traces and the regenerated DFF bit traces, with bias-aware statistics:

  probe/results/reanalysis/{d1,d2}_fixed/
    tvla_per_cycle.csv      stage, t_cond, t_fixed          ( Welch, raw )
    tvla_higher_order.csv   stage, order, t_cond, t_fixed   ( moments 1-3 )
    mi_power_per_stage.csv  stage, mi_plugin, mi_mm, null_p99 (+ full row -1)
    mi_power_per_bit.csv    bit, mi_plugin, mi_mm, null_p99 ( output stage )
    mi_wire.csv             wire, name, max_mi, worst_off, mi_mm, null_p99
    mi_pair.csv             wi, wj, names, mi_joint, mi_mm, null_p99 (top 20)
    summary.json            headline numbers for the manuscript tables
"""

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reanalysis as R  # noqa: E402  (load_power, load_header, ...)

OUT_BASE = os.path.join(HERE, "results", "reanalysis")
RNG = np.random.default_rng(20260719)

WIRE_NAMES = {
    2: [f"valid_pipe[{i}]" for i in range(10)]
       + [f"y0_out[{i}]" for i in range(8)]
       + [f"y1_out[{i}]" for i in range(8)] + ["valid_out"],
    3: [f"valid_pipe[{i}]" for i in range(10)]
       + [f"y{s}_out[{i}]" for i in range(8) for s in range(3)]
       + ["valid_out"],
}
# fix ordering for d=2: valid_pipe, y0, y1, y2, valid_out
WIRE_NAMES[3] = ([f"valid_pipe[{i}]" for i in range(10)]
                 + [f"y0_out[{i}]" for i in range(8)]
                 + [f"y1_out[{i}]" for i in range(8)]
                 + [f"y2_out[{i}]" for i in range(8)] + ["valid_out"])

N_OFF = 15  # manuscript's 15-cycle window (offsets 0..14)


def tvla_tables(hd, fc, secrets):
    M = R.stage_matrix(hd, fc, n_offsets=N_OFF)
    rows, ho_rows = [], []
    for off in range(N_OFF):
        col = M[:, off]
        tc = R.welch_t(col[secrets < 0x80], col[secrets >= 0x80])
        tf = R.welch_t(col[secrets == 0x00], col[secrets != 0x00])
        rows.append((off, tc, tf))
        if len(np.unique(col)) >= 3:  # genuine variance only
            c = col - col.mean()
            for order in (1, 2, 3):
                z = col if order == 1 else c ** order
                ho_rows.append((off, order,
                                R.welch_t(z[secrets < 0x80], z[secrets >= 0x80]),
                                R.welch_t(z[secrets == 0x00], z[secrets != 0x00])))
    genuine = [off for off in range(N_OFF) if len(np.unique(M[:, off])) >= 3]
    max_cond = max(abs(r[1]) for r in rows if r[0] in genuine) if genuine else 0.0
    max_fixed = max(abs(r[2]) for r in rows if r[0] in genuine) if genuine else 0.0
    max_ho = max((max(abs(r[2]), abs(r[3])) for r in ho_rows), default=0.0)
    return rows, ho_rows, genuine, max_cond, max_fixed, max_ho


def mi_power_tables(hd, fc, secrets):
    M = R.stage_matrix(hd, fc, n_offsets=N_OFF)
    rows = []
    for off in range(N_OFF):
        col = M[:, off]
        mi, bias, corr = R.mi_miller_madow(col, secrets)
        if len(np.unique(col)) >= 3:
            nulls = R.mi_perm_null(col, secrets, n_perm=300)
            p99 = float(np.percentile(nulls, 99))
        else:
            p99 = 0.0
        rows.append((off, mi, corr, p99))
    hd_flat = M.flatten()
    sec_flat = np.tile(secrets, N_OFF)
    mi_f, bias_f, corr_f = R.mi_miller_madow(hd_flat, sec_flat)
    return rows, (mi_f, corr_f)


def mi_bit_table(M_out, secrets):
    rows = []
    for b in range(8):
        sb = (secrets >> b) & 1
        mi, bias, corr = R.mi_miller_madow(M_out, sb)
        rows.append((b, mi, corr, 0.0))
    return rows


def mi_wire_table(bit_trace, secrets, fc, names):
    rows = []
    n_bits = len(names)
    n_triples = len(secrets)
    # max over offsets per wire (plug-in), then MM + null at worst offset.
    # Alignment uses the actual first_cycle of each triple (spacing mixes
    # 15/16 cycles); a fixed stride drifts and misaligns late triples.
    for w in range(n_bits):
        per_off = []
        for off in range(N_OFF):
            idx = np.minimum(fc + off, len(bit_trace) - 1)
            wire = bit_trace[idx, w]
            mi, _, _ = R.mi_plugin(wire, secrets)
            per_off.append(mi)
        worst = int(np.argmax(per_off))
        idx = np.minimum(fc + worst, len(bit_trace) - 1)
        wire = bit_trace[idx, w]
        mi, bias, corr = R.mi_miller_madow(wire, secrets)
        nulls = R.mi_perm_null(wire, secrets, n_perm=300)
        rows.append((w, names[w], float(per_off[worst]), worst,
                     float(corr), float(np.percentile(nulls, 99))))
    return rows


def mi_pair_table(bit_trace, secrets, fc, names, wire_rows):
    n_bits = len(names)
    top10 = sorted(wire_rows, key=lambda r: -r[2])[:10]
    off = 10
    idx = np.minimum(fc + off, len(bit_trace) - 1)
    aligned = bit_trace[idx]
    pairs = []
    for wr in top10:
        i = wr[0]
        for j in range(n_bits):
            if i == j:
                continue
            joint = aligned[:, i] * 2 + aligned[:, j]
            mi, bias, corr = R.mi_miller_madow(joint, secrets)
            pairs.append((i, j, float(mi), float(corr)))
    pairs.sort(key=lambda x: -x[2])
    top = pairs[:20]
    i, j, mi, corr = top[0]
    joint = aligned[:, i] * 2 + aligned[:, j]
    nulls = R.mi_perm_null(joint, secrets, n_perm=300)
    null_p99 = float(np.percentile(nulls, 99))
    return [(i, j, names[i], names[j], mi, corr, null_p99 if k == 0 else 0.0)
            for k, (i, j, mi, corr) in enumerate(top)]


def write_csvs(outdir, tag, tvla_rows, ho_rows, mi_rows, mi_full, bit_rows):
    os.makedirs(outdir, exist_ok=True)
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
        f.write(f"-1,{mi_full[0]:.6f},{mi_full[1]:.6f},0.0\n")
    with open(os.path.join(outdir, "mi_power_per_bit.csv"), "w") as f:
        f.write("bit_index,mi_plugin,mi_mm_corrected,null_p99\n")
        for b, mi, corr, p99 in bit_rows:
            f.write(f"{b},{mi:.6f},{corr:.6f},{p99:.6f}\n")


def process(tag, power, header, bittrace, bitheader, n_shares):
    print(f"=== {tag} ===")
    cycles, hd = R.load_power(power)
    rows = R.load_header(header, n_shares)
    secrets = np.array([r[0] for r in rows], dtype=np.int64)
    fc = np.array([r[2] for r in rows], dtype=np.int64)
    n = len(rows)

    tvla_rows, ho_rows, genuine, mc, mf, mho = tvla_tables(hd, fc, secrets)
    print(f"  genuine stages: {genuine}; max|t| cond {mc:.4f} fixed {mf:.4f} "
          f"higher-order {mho:.4f}")

    mi_rows, mi_full = mi_power_tables(hd, fc, secrets)
    print(f"  full-trace MI plug-in {mi_full[0]:.4f} MM-corr {mi_full[1]:.4f}")

    M12 = R.stage_matrix(hd, fc, n_offsets=N_OFF)[:, 12]
    bit_rows = mi_bit_table(M12, secrets)

    outdir = os.path.join(OUT_BASE, f"{tag}_fixed")
    write_csvs(outdir, tag, tvla_rows, ho_rows, mi_rows, mi_full, bit_rows)

    # --- bit-trace probing ---
    names = WIRE_NAMES[n_shares]
    bt = np.loadtxt(bittrace, dtype=str)
    bit_arr = np.array([[int(c) for c in line] for line in bt], dtype=np.int8)
    wire_rows = mi_wire_table(bit_arr, secrets, fc, names)
    pair_rows = mi_pair_table(bit_arr, secrets, fc, names, wire_rows)
    with open(os.path.join(outdir, "mi_wire.csv"), "w") as f:
        f.write("wire_idx,wire_name,max_mi_plugin,worst_offset,"
                "mi_mm_corrected,null_p99\n")
        for w, nm, mi, wo, corr, p99 in wire_rows:
            f.write(f"{w},{nm},{mi:.6f},{wo},{corr:.6f},{p99:.6f}\n")
    with open(os.path.join(outdir, "mi_pair.csv"), "w") as f:
        f.write("wire_i,wire_j,wire_i_name,wire_j_name,mi_joint_plugin,"
                "mi_mm_corrected,null_p99_top\n")
        for i, j, ni, nj, mi, corr, p99 in pair_rows:
            f.write(f"{i},{j},{ni},{nj},{mi:.6f},{corr:.6f},{p99:.6f}\n")

    max_wire = max(wire_rows, key=lambda r: r[2])
    max_wire_mm = max(r[4] for r in wire_rows)
    max_wire_null = max(r[5] for r in wire_rows)
    top_pair = pair_rows[0]
    summary = {
        "tag": tag,
        "genuine_stages": genuine,
        "tvla_max_cond_genuine": round(mc, 4),
        "tvla_max_fixed_genuine": round(mf, 4),
        "tvla_max_higher_order": round(mho, 4),
        "mi_stage12_plugin": [r for r in mi_rows if r[0] == 12][0][1],
        "mi_stage12_mm": [r for r in mi_rows if r[0] == 12][0][2],
        "mi_full_plugin": round(mi_full[0], 4),
        "mi_full_mm": round(mi_full[1], 4),
        "mi_wire_max_plugin": round(max_wire[2], 4),
        "mi_wire_max_mm": round(max_wire_mm, 4),
        "mi_wire_null_p99_max": round(max_wire_null, 4),
        "mi_pair_top_plugin": round(top_pair[4], 4),
        "mi_pair_top_mm": round(top_pair[5], 4),
        "mi_pair_null_p99": round(top_pair[6], 4),
    }
    print("  " + json.dumps(summary, indent=None))
    return summary


def main():
    base = os.path.join(HERE, "results", "reanalysis")
    s1 = process("d1",
                 os.path.join(base, "d1_power_fixed.txt"),
                 os.path.join(base, "d1_header_fixed.txt"),
                 os.path.join(base, "d1_bittrace.txt"),
                 os.path.join(base, "d1_bitheader.txt"), 2)
    s2 = process("d2",
                 os.path.join(base, "d2_power_fixed.txt"),
                 os.path.join(base, "d2_header_fixed.txt"),
                 os.path.join(base, "d2_bittrace.txt"),
                 os.path.join(base, "d2_bitheader.txt"), 3)
    with open(os.path.join(base, "summary_fixed.json"), "w") as f:
        json.dump([s1, s2], f, indent=2)
    print(f"\nwrote {os.path.join(base, 'summary_fixed.json')}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
positive_control.py
===================
Positive-control analysis for the side-channel verification pipeline.

The DUT is rtl/unmasked_sbox.v — a deliberately UNPROTECTED AES S-box
with the same outer pipeline structure (10-stage valid pipe, registered
output) as the masked designs.  It was stimulated with the identical
testbench methodology (rtl/tb_power_sim_unmasked.v mirrors
rtl/tb_power_sim.v: same LFSR seed, same secret sequence, same HD
metric over the monitored DFFs, same fc-based alignment).

If the TVLA / MI / probing apparatus cannot flag THIS design as leaky,
it cannot claim detection capability for the masked designs either.

Inputs (copied from the simulator):
  probe/results/reanalysis/unmasked/uc_power.txt   (cycle, hd)
  probe/results/reanalysis/unmasked/uc_header.txt  (secret s0 s1 fc)
  probe/results/reanalysis/unmasked/uc_trace.txt   (19-bit rows)

Outputs (same CSV/JSON schema as the masked re-analysis):
  probe/results/reanalysis/unmasked/{tvla_per_cycle, tvla_higher_order,
      mi_power_per_stage, mi_power_per_bit, mi_wire, mi_pair}.csv
  probe/results/reanalysis/unmasked/summary_unmasked.json
"""

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reanalysis as R          # noqa: E402
import regen_results as G       # noqa: E402  (same tables as masked runs)

OUT = os.path.join(HERE, "results", "reanalysis", "unmasked")
N_OFF = 15

WIRES = ([f"valid_pipe[{i}]" for i in range(10)]
         + [f"y_out[{i}]" for i in range(8)]
         + ["valid_out"])

# Canonical Rijndael S-box (reference for validating the hand-typed
# Verilog LUT against every triple observed in the trace).
REF_SBOX = bytes([
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67,
    0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2,
    0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5,
    0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80,
    0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6,
    0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe,
    0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02,
    0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda,
    0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e,
    0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8,
    0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac,
    0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4,
    0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74,
    0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57,
    0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87,
    0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d,
    0x0f, 0xb0, 0x54, 0xbb, 0x16,
])
assert sorted(REF_SBOX) == list(range(256)), "reference S-box is not a permutation"


def lut_check(bit_arr, secrets, fc):
    """Verify y_out == REF_SBOX[secret] for every triple; auto-detect the
    output offset (the one with a perfect match). Returns (offset, n_bad,
    coverage)."""
    n = len(secrets)
    best = None
    for off in range(9, N_OFF + 1):
        idx = np.minimum(fc + off, len(bit_arr) - 1)
        y = bit_arr[idx][:, 10:18]                     # y_out[0..7]
        yval = np.zeros(n, dtype=np.int64)
        for b in range(8):
            yval |= y[:, b].astype(np.int64) << b
        ref = np.array([REF_SBOX[s] for s in secrets], dtype=np.int64)
        n_bad = int((yval != ref).sum())
        if best is None or n_bad < best[1]:
            best = (off, n_bad)
        if n_bad == 0:
            break
    coverage = len(np.unique(secrets))
    return best[0], best[1], coverage


def main():
    power = os.path.join(OUT, "uc_power.txt")
    header = os.path.join(OUT, "uc_header.txt")
    trace = os.path.join(OUT, "uc_trace.txt")

    cycles, hd = R.load_power(power)
    rows = R.load_header(header, 2)
    secrets = np.array([r[0] for r in rows], dtype=np.int64)
    fc = np.array([r[2] for r in rows], dtype=np.int64)
    n = len(rows)
    print(f"cycles {len(hd)}, triples {n}, HD range "
          f"[{hd.min()}, {hd.max()}] (19 monitored wires)")

    bt = np.loadtxt(trace, dtype=str)
    bit_arr = np.array([[int(c) for c in line] for line in bt],
                       dtype=np.int8)
    assert bit_arr.shape[1] == 19, bit_arr.shape

    # ---------------- LUT / DUT functional validation ----------------
    lut_off, lut_bad, cov = lut_check(bit_arr, secrets, fc)
    print(f"LUT check: output offset fc+{lut_off}, mismatches "
          f"{lut_bad}/{n}, distinct secrets covered {cov}/256")
    if lut_bad != 0:
        print("FATAL: unmasked S-box LUT mismatch — fix rtl/unmasked_sbox.v")
        sys.exit(1)

    # ---------------- TVLA (identical functions as masked) -----------
    tvla_rows, ho_rows, genuine, mc, mf, mho = G.tvla_tables(hd, fc, secrets)
    print(f"genuine stages {genuine}; max|t| cond {mc:.2f} fixed {mf:.2f} "
          f"higher-order {mho:.2f}")

    # ---------------- MI on HD power trace ---------------------------
    mi_rows, mi_full = G.mi_power_tables(hd, fc, secrets)
    M_out = R.stage_matrix(hd, fc, n_offsets=N_OFF)[:, min(lut_off, N_OFF - 1)]
    bit_rows = G.mi_bit_table(M_out, secrets)

    # ---------------- per-wire / pair probing MI ---------------------
    wire_rows = G.mi_wire_table(bit_arr, secrets, fc, WIRES)
    pair_rows = G.mi_pair_table(bit_arr, secrets, fc, WIRES, wire_rows)

    # ---------------- write CSVs (same schema as masked) -------------
    G.write_csvs(OUT, "uc", tvla_rows, ho_rows, mi_rows, mi_full, bit_rows)
    with open(os.path.join(OUT, "mi_wire.csv"), "w") as f:
        f.write("wire_idx,wire_name,max_mi_plugin,worst_offset,"
                "mi_mm_corrected,null_p99\n")
        for w, nm, mi, wo, corr, p99 in wire_rows:
            f.write(f"{w},{nm},{mi:.6f},{wo},{corr:.6f},{p99:.6f}\n")
    with open(os.path.join(OUT, "mi_pair.csv"), "w") as f:
        f.write("wire_i,wire_j,wire_i_name,wire_j_name,mi_joint_plugin,"
                "mi_mm_corrected,null_p99_top\n")
        for i, j, ni, nj, mi, corr, p99 in pair_rows:
            f.write(f"{i},{j},{ni},{nj},{mi:.6f},{corr:.6f},{p99:.6f}\n")

    max_wire = max(wire_rows, key=lambda r: r[2])
    max_wire_mm = max(r[4] for r in wire_rows)
    max_wire_null = max(r[5] for r in wire_rows)
    top_pair = pair_rows[0]
    stage_mi = {r[0]: r for r in mi_rows}
    out_stage = min(lut_off, N_OFF - 1)
    summary = {
        "tag": "unmasked_posctrl",
        "n_triples": n,
        "lut_output_offset": lut_off,
        "lut_mismatches": lut_bad,
        "secret_coverage_256": cov,
        "genuine_stages": genuine,
        "tvla_max_cond_genuine": round(mc, 4),
        "tvla_max_fixed_genuine": round(mf, 4),
        "tvla_max_higher_order": round(mho, 4),
        "mi_output_stage": out_stage,
        "mi_stage_output_plugin": stage_mi[out_stage][1],
        "mi_stage_output_mm": stage_mi[out_stage][2],
        "mi_full_plugin": round(mi_full[0], 4),
        "mi_full_mm": round(mi_full[1], 4),
        "mi_wire_max_plugin": round(max_wire[2], 4),
        "mi_wire_max_mm": round(max_wire_mm, 4),
        "mi_wire_null_p99_max": round(max_wire_null, 4),
        "mi_pair_top_plugin": round(top_pair[4], 4),
        "mi_pair_top_mm": round(top_pair[5], 4),
        "mi_pair_null_p99": round(top_pair[6], 4),
    }
    with open(os.path.join(OUT, "summary_unmasked.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 72)
    print("POSITIVE CONTROL SUMMARY (unmasked AES S-box, N =", n, ")")
    print("=" * 72)
    print(json.dumps(summary, indent=2))

    # Per-instrument verdict.  Note: first-order TVLA on the HD trace is
    # EXPECTED to be weak even on an unmasked design: the only monitored
    # data transition is y_out old->new, and E[HW(x ^ Y)] = 4 exactly for
    # uniform Y, so the conditional HD mean is secret-independent by
    # construction; only higher moments carry the signal.
    stage_null_p99 = stage_mi[out_stage][3]
    verdict = {
        "probing_wire_mi_fires": bool(max_wire_mm > max_wire_null),
        "stage_mi_fires": bool(stage_mi[out_stage][2] > stage_null_p99),
        "tvla_first_order_fires": bool(mc > 4.5 or mf > 4.5),
        "tvla_higher_order_fires": bool(mho > 4.5),
    }
    verdict["overall_fires"] = bool(
        verdict["probing_wire_mi_fires"] and verdict["stage_mi_fires"]
        and verdict["tvla_higher_order_fires"])
    summary["detection"] = verdict
    with open(os.path.join(OUT, "summary_unmasked.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\nDETECTION VERDICT")
    for k, v in verdict.items():
        print(f"  {k}: {'FIRES' if v else 'does not fire'}")
    print("\nPOSITIVE CONTROL:", "PASSES (apparatus detects the unmasked "
          "design)" if verdict["overall_fires"] else "FAILS — BAD")
    print(f"wrote {os.path.join(OUT, 'summary_unmasked.json')}")


if __name__ == "__main__":
    main()

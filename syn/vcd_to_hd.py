#!/usr/bin/env python3
"""
vcd_to_hd.py
============
Read a VCD file (output of iverilog's $dumpvars) and convert the
y0_out, y1_out signals into an HD (Hamming Distance) model power
trace, one integer per cycle.

HD model: the power of a register is proportional to the number of
bits that toggle between consecutive samples.  We treat the 256-bit
vector y = y0_out || y1_out as the register.

Output: one integer per cycle, in time order.
"""
import argparse
import sys

try:
    import vcdvcd
except ImportError:
    sys.exit("vcdvcd is required.  Install with: pip install vcdvcd")


def parse_value(v: str, bits: int) -> int:
    """Convert a vcdvcd value string to an int.

    Format: "1", "0", "x", "z" (1-bit); "xNNNN" or "bNNNN" (multi-bit).
    """
    if v in ("0", "1"):
        return int(v)
    if v in ("x", "z", "X", "Z"):
        return 0
    if v.startswith("x") or v.startswith("X") or v.startswith("z"):
        # unknown — return 0
        return 0
    if v.startswith("b"):
        return int(v[1:], 2)
    # bare binary
    return int(v, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vcd", help="input VCD file")
    ap.add_argument("trace", help="output HD trace file (one int/line)")
    ap.add_argument("--ref-y0", default="tb_vcd_dump.u_dut.y0_out[127:0]",
                    help="VCD reference of y0 share")
    ap.add_argument("--ref-y1", default="tb_vcd_dump.u_dut.y1_out[127:0]",
                    help="VCD reference of y1 share")
    ap.add_argument("--bits", type=int, default=128,
                    help="width of each share (default: 128)")
    args = ap.parse_args()

    print(f"Reading {args.vcd} ...")
    vcd = vcdvcd.VCDVCD(args.vcd)

    # Each .tv is a list of (time, value_string)
    y0_tv = vcd[args.ref_y0].tv
    y1_tv = vcd[args.ref_y1].tv
    print(f"  y0 samples: {len(y0_tv)}")
    print(f"  y1 samples: {len(y1_tv)}")

    # Merge y0/y1 timelines.  Each change in either signal gives a new
    # sample point.  At each sample, both y0 and y1 have their most
    # recent value.
    n = max(len(y0_tv), len(y1_tv))
    i0 = i1 = 0
    last_y0 = "0" * args.bits
    last_y1 = "0" * args.bits
    times = []
    y0_vals = []
    y1_vals = []
    # Simulate by walking all events in time order
    events = sorted(set([t for t, _ in y0_tv] + [t for t, _ in y1_tv]))
    for t in events:
        # Advance y0 to time t
        while i0 < len(y0_tv) and y0_tv[i0][0] <= t:
            last_y0 = y0_tv[i0][1]
            i0 += 1
        # Advance y1 to time t
        while i1 < len(y1_tv) and y1_tv[i1][0] <= t:
            last_y1 = y1_tv[i1][1]
            i1 += 1
        times.append(t)
        y0_vals.append(parse_value(last_y0, args.bits))
        y1_vals.append(parse_value(last_y1, args.bits))

    # Compute HD per sample
    with open(args.trace, "w") as f:
        prev = 0
        for t, y0, y1 in zip(times, y0_vals, y1_vals):
            cur = (y0 << args.bits) | y1
            hd = bin(cur ^ prev).count("1")
            f.write(f"{hd}\n")
            prev = cur
    print(f"Wrote {len(times)} HD samples to {args.trace}")


if __name__ == "__main__":
    main()

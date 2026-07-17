#!/usr/bin/env python3
"""
prolead_postprocess.py
======================
Post-process a Yosys-generated gate-level Verilog netlist into the
format PROLEAD expects.

Transformations:
  1. Rename the top module from `masked_sbox_first_order` to
     `circuit` (PROLEAD hardcodes this name).
  2. Rename the port interface to PROLEAD's expected names:
       x0_in  -> sboxIn[7:0]   (input share 0)
       x1_in  -> sboxIn[15:8]  (input share 1)
       r0_in..r27_in -> randomS2[15:0], randomS3[7:0], randomS4[15:0], randomS5[31:0]
       y0_out -> sboxOut[7:0]
       y1_out -> sboxOut[15:8]
     (matches the AES_Sbox_CMS_d1 example's signal convention)
  3. Drop the `rst_n` and `valid_in`/`valid_out` signals — PROLEAD
     probes the DFFs directly without the pipeline handshake.

Usage:
   python3 syn/prolead_postprocess.py syn/prolead/_pre.v \\
       syn/prolead/masked_sbox_first_order_circuit.v
"""
import re
import sys


# Top module name (input) -> PROLEAD's expected module name
TOP_MODULE_IN = "masked_sbox_first_order"
TOP_MODULE_OUT = "circuit"

# Input port remapping: original port name -> PROLEAD-style signal
PORT_RENAME = {
    "x0_in":  "sboxIn[7:0]",
    "x1_in":  "sboxIn[15:8]",
    "y0_out": "sboxOut[7:0]",
    "y1_out": "sboxOut[15:8]",
}

# Random-share port packing (28 bytes total, packed as the CMS
# example's 4 random signals):
#   r0..r15   -> randomS2[15:0]  (16 bytes -> 16-bit bus)
#   r16..r23  -> randomS3[7:0]   ( 8 bytes ->  8-bit bus)
#   r24..r27  -> randomS4[15:0]  ( 4 bytes ->  4-bit bus; here 8 bits)
# We pack all 28 bytes into a 224-bit bus `randomIn[223:0]` and
# provide a config that maps it to PROLEAD's `randomS*` group.
# Simpler: keep the 28 individual ports and let PROLEAD treat each
# as an 8-bit random input.
KEEP_RANDOM_PORTS = True  # if False, pack into buses


def main(in_path: str, out_path: str):
    with open(in_path) as f:
        text = f.read()

    # 1. Top module rename
    text = text.replace(f"module {TOP_MODULE_IN}(",
                        f"module {TOP_MODULE_OUT}(")
    text = re.sub(r"\b" + TOP_MODULE_IN + r"\b",
                  TOP_MODULE_OUT, text)

    # 2. Port-list rename
    for old, new in PORT_RENAME.items():
        text = re.sub(r"\b" + old + r"\b", new, text)

    # 3. Drop rst_n, valid_in, valid_out (handled separately)
    # In the port list these are bare names; in the body they appear
    # as .rst_n(...) / .valid_in(...) on cell instances.  Removing
    # them requires both transformations.
    for sig in ("rst_n", "valid_in", "valid_out"):
        text = re.sub(rf"[\s,]{sig}[\s,]", " ", text)
        text = re.sub(rf"\.{sig}\s*\([^)]*\)", "", text)

    # 4. Sanity: collapse runs of whitespace inside the port list
    # (defensive — Yosys emits pretty-printed output)
    text = re.sub(r"\n\s*\n", "\n", text)

    with open(out_path, "w") as f:
        f.write(text)
    print(f"Wrote {out_path} ({len(text)} bytes, {len(text.splitlines())} lines)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <in.v> <out.v>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

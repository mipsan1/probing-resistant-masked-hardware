#!/usr/bin/env bash
# Gate-level functional sim: synthesize the flattened netlist (no abc
# mapping; generic $_DFFE_PN0P_/$_DFF_PN0_ primitives), recompile the
# testbench against it and run.
#
# Netlists written by yosys syn/synth_round1_flat.ys:
#   syn/masked_aes_round1_flat_syn.v  -- fully flattened single module
#     (~48 MB; used for yosys `stat` reporting and structural flows;
#     exceeds iverilog's capacity in the 300 s sandbox process window)
#   syn/masked_aes_round1_hier_syn.v  -- the SAME design one pass
#     before `flatten` (S-boxes stay instances; ~2.7 MB).  `flatten`
#     is purely structural, so cycle behavior is identical; this is
#     the file the gate-level functional sim below runs against.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Vector generation (DUT contract: gold = MC(SR(SB(pt))) XOR rk)
python3 sim/gen_round1_vectors.py

# 2. Synthesize the gate-level netlists (skip with FAST=1)
if [ "${FAST:-0}" != "1" ]; then
    yosys syn/synth_round1_flat.ys
fi

# 3. Compile testbench + gate-level netlist (hierarchy-preserving form
#    of the flattened design; yosys write_verilog emits generic cells
#    as assign/always RTL-style processes, so no simlib.v is needed).
cd rtl
iverilog -g2012 -I . -o /tmp/round1_tb_gl.vvp \
    tb_masked_aes_round1.v \
    ../syn/masked_aes_round1_hier_syn.v
cd ..
vvp /tmp/round1_tb_gl.vvp

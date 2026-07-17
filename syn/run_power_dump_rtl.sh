#!/usr/bin/env bash
# RTL-level power trace dump (fast).  Uses the RTL netlist
# (rtl/masked_aes_round1.v) instead of the gate-level netlist
# (syn/masked_aes_round1_syn.v), so 10K traces complete in seconds
# rather than the 10+ minutes that the gate-level sim would take.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Generate 10K triples
python3 syn/gen_power_dump.py

# 2. Compile + run (RTL, not gate-level)
cd rtl
iverilog -g2012 -I . -o /tmp/tb_power_rtl.vvp \
    tb_power_dump.v \
    masked_sbox_first_order.v \
    masked_sbox_pkg.v \
    masked_aes_round1.v
cd ..
vvp /tmp/tb_power_rtl.vvp

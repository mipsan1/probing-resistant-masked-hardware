#!/usr/bin/env bash
# Generate power-dump vectors and run iverilog sim.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Generate 10K triples
python3 syn/gen_power_dump.py

# 2. Compile + run
cd rtl
iverilog -g2012 -I . -o /tmp/tb_power.vvp \
    tb_power_dump.v \
    ../syn/masked_aes_round1_syn.v
cd ..
vvp /tmp/tb_power.vvp

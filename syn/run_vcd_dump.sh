#!/usr/bin/env bash
# Run the VCD power-trace testbench (RTL netlist) for the masked AES
# round 1.  Produces sim/power.vcd which is then post-processed by
# syn/vcd_to_hd.py into an HD-model power trace.
#
# NOTE: iverilog's single-threaded simulator becomes the bottleneck
# for trace counts above ~10 vectors × 14 cycles.  For larger traces
# (≥1K vectors), use a faster simulator such as Verilator or
# commercial VCS / Modelsim; only the VCD file format is identical.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Generate vectors
python3 syn/gen_power_dump.py

# 2. Compile + run (RTL, not gate-level; gate-level is too slow)
cd rtl
iverilog -g2012 -I . -o /tmp/tb_vcd.vvp \
    tb_vcd_dump.v \
    masked_sbox_first_order.v \
    masked_sbox_pkg.v \
    masked_aes_round1.v
cd ..
N=${N_VECTORS:-100}
vvp /tmp/tb_vcd.vvp +N=$N 2>&1 | grep -v "Not enough words"

# 3. VCD -> HD trace
source .venv/bin/activate 2>/dev/null || true
python3 syn/vcd_to_hd.py sim/power.vcd sim/power_trace.txt

# 4. TVLA (optional, requires numpy)
python3 probe/tvla.py sim/power_trace.txt sim/power_secret.txt \
    --output sim/tvla_results.txt 2>&1 || echo "TVLA skipped (numpy missing)"

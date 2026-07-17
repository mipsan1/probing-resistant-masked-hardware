#!/usr/bin/env bash
# Gate-level VCD power-trace pipeline.
#
# Synthesizes the masked AES round-1 design (d=1 and d=2) into
# iverilog-friendly netlists, runs the gate-level testbench, then
# applies TVLA on the resulting Hamming-distance power trace.
#
# Outputs:
#   sim/power_gl_trace.txt         (cycle, hd) for d=1
#   sim/power_gl_header.txt        (secret, first_cycle) for d=1
#   sim/power_gl_d2_trace.txt      (cycle, hd) for d=2
#   sim/power_gl_d2_header.txt     (secret, first_cycle) for d=2
#   sim/tvla_gl/tvla_report.md     TVLA results for d=1
#   sim/tvla_gl_d2/tvla_report.md  TVLA results for d=2
#
# Usage:
#   bash syn/run_vcd_dump_gl.sh
#   N=1000 bash syn/run_vcd_dump_gl.sh
set -euo pipefail
cd "$(dirname "$0")/.."

N=${N_VECTORS:-100}

# 1. d=1 gate-level netlist (abc -fast + setundef -zero)
yosys -q syn/synth_round1_gl.ys

# 2. d=1 testbench
cd rtl
iverilog -g2012 -I . -o /tmp/tb_vcd_gl.vvp \
    tb_vcd_dump_gl.v \
    /Users/ckim/Downloads/IEEE-Transactions-TIFS/syn/masked_aes_round1_gl_syn.v
cd ..
vvp /tmp/tb_vcd_gl.vvp +N=$N 2>&1 | grep -v "Not enough words" | tail -2

# 3. TVLA on d=1
python3 probe/tvla.py sim/power_gl_trace.txt sim/power_gl_header.txt \
    sim/tvla_gl 1 2>&1 | tail -8

# 4. d=2 gate-level netlist
yosys -q syn/synth_round1_d2_gl.ys

# 5. d=2 mask file (1008 bytes/vector)
if [ ! -f sim/power_d2_masks.txt ]; then
    python3 - <<'PYEOF'
import os, random
random.seed(20260717)
N = 100
masks = [f'{random.randint(0,255):02x}'
         for _ in range(N*1008)]
with open('sim/power_d2_masks.txt', 'w') as f:
    f.write('\n'.join(masks) + '\n')
print(f"Wrote sim/power_d2_masks.txt ({N*1008} entries)")
PYEOF
fi

# 6. d=2 testbench
cd rtl
iverilog -g2012 -I . -o /tmp/tb_vcd_gl_d2.vvp \
    tb_vcd_dump_gl_d2.v \
    /Users/ckim/Downloads/IEEE-Transactions-TIFS/syn/masked_aes_round1_d2_gl_syn.v
cd ..
vvp /tmp/tb_vcd_gl_d2.vvp +N=$N 2>&1 | grep -v "Too many words" | tail -2

# 7. TVLA on d=2
python3 probe/tvla.py sim/power_gl_d2_trace.txt sim/power_gl_d2_header.txt \
    sim/tvla_gl_d2 2 2>&1 | tail -8

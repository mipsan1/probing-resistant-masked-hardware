#!/usr/bin/env bash
# Gate-level functional sim: synthesize netlist, recompile + run testbench.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Vector generation (same as run_round1_sim.sh)
python3 - <<'PYEOF'
import os, sys, random
sys.path.insert(0, ".")
from reference.masked_aes import masked_aes_round1
random.seed(20260717)
N = 100
os.makedirs("sim", exist_ok=True)
pt_lines, key_lines, gold_lines = [], [], []
for i in range(N):
    pt = random.randbytes(16)
    k  = random.randbytes(16)
    g  = masked_aes_round1(pt, k)
    pt_lines.append(f"{int.from_bytes(pt, 'big'):032x}")
    key_lines.append(f"{int.from_bytes(k,  'big'):032x}")
    gold_lines.append(f"{int.from_bytes(g, 'big'):032x}")
    mask_lines = [f"{random.randint(0, 255):02x}" for _ in range(448)]
    with open(f"sim/round1_mask_{i}.txt", "w") as f:
        f.write("\n".join(mask_lines) + "\n")
with open("sim/round1_pt.txt",   "w") as f: f.write("\n".join(pt_lines)   + "\n")
with open("sim/round1_keys.txt", "w") as f: f.write("\n".join(key_lines)  + "\n")
with open("sim/round1_gold.txt", "w") as f: f.write("\n".join(gold_lines) + "\n")
print(f"Generated {N} vectors in sim/")
PYEOF

# 2. Compile testbench + gate-level netlist (which already inlines
#    masked_sbox_first_order as $_AND_/$_XOR_ primitives).
cd rtl
iverilog -g2012 -I . -o /tmp/tb_round1_gl.vvp \
    tb_masked_aes_round1.v \
    ../syn/masked_aes_round1_syn.v
cd ..
vvp /tmp/tb_round1_gl.vvp

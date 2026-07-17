#!/usr/bin/env bash
# Single-vector debug
set -euo pipefail
cd "$(dirname "$0")/.."

python3 - <<'PYEOF'
import os, sys, random
sys.path.insert(0, ".")
from reference.masked_aes import masked_aes_round1
random.seed(20260717)
os.makedirs("sim", exist_ok=True)
i = 0
pt = bytes(16)
k  = bytes(16)
g  = masked_aes_round1(pt, k)
print(f"pt={pt.hex()} key={k.hex()} golden={g.hex()}")
with open("sim/round1_pt.txt",   "w") as f: f.write(f"{int.from_bytes(pt, 'big'):032x}\n")
with open("sim/round1_keys.txt", "w") as f: f.write(f"{int.from_bytes(k, 'big'):032x}\n")
with open("sim/round1_gold.txt", "w") as f: f.write(f"{int.from_bytes(g, 'big'):032x}\n")
mask_lines = [f"{random.randint(0, 255):02x}" for _ in range(448)]
with open("sim/round1_mask_0.txt", "w") as f:
    f.write("\n".join(mask_lines) + "\n")
PYEOF

cd rtl
iverilog -g2012 -I . -o /tmp/tb_round1.vvp \
    tb_masked_aes_round1.v masked_aes_round1.v \
    masked_sbox_first_order.v masked_sbox_pkg.v
cd ..
vvp /tmp/tb_round1.vvp 2>&1 | head -10

#!/usr/bin/env bash
# Generate round-1 test vectors and run iverilog simulation.
# Vectors implement the DUT contract (gold = MC(SR(SB(pt))) XOR rk,
# external round key, no key schedule) — see sim/gen_round1_vectors.py.
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Generate vectors (deterministic, seed 20260717)
python3 sim/gen_round1_vectors.py

# 2. Compile + run (-I rtl/ so `include "masked_sbox_pkg.v" works)
cd rtl
iverilog -g2012 -I . -o /tmp/tb_round1.vvp \
    tb_masked_aes_round1.v masked_aes_round1.v \
    masked_sbox_first_order.v masked_sbox_pkg.v
cd ..
vvp /tmp/tb_round1.vvp

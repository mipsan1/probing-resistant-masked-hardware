"""
gen_power_dump.py
=================
Generate 10,000 (plaintext, key, mask) triples for the full-chip
power-dump testbench.

Output files (read by iverilog $readmemh):
  sim/power_secret.txt  - 32-hex secret (plaintext || key), 10K lines
  sim/power_s0.txt      - 32-hex share-0 of plaintext
  sim/power_s1.txt      - 32-hex share-1 of plaintext
  sim/power_rk0.txt     - 32-hex share-0 of round key (= key_share_0)
  sim/power_rk1.txt     - 32-hex share-1 of round key (= key_share_1)
  sim/power_masks.txt   - 448 mask bytes per vector, 16K lines

The "secret" for TVLA is the low byte of the plaintext (1 of 256
values), uniformly distributed.
"""

import os
import random


def main(n_vectors: int = 10000, seed: int = 20260717):
    random.seed(seed)
    out = "sim"
    os.makedirs(out, exist_ok=True)

    with (
        open(f"{out}/power_secret.txt", "w") as f_sec,
        open(f"{out}/power_s0.txt", "w") as f_s0,
        open(f"{out}/power_s1.txt", "w") as f_s1,
        open(f"{out}/power_rk0.txt", "w") as f_rk0,
        open(f"{out}/power_rk1.txt", "w") as f_rk1,
        open(f"{out}/power_masks.txt", "w") as f_msk,
    ):
        for i in range(n_vectors):
            pt = random.randbytes(16)
            key = random.randbytes(16)
            s0 = random.randbytes(16)
            s1 = bytes(a ^ b for a, b in zip(pt, s0))
            rk0 = random.randbytes(16)
            rk1 = bytes(a ^ b for a, b in zip(key, rk0))
            masks = [random.randint(0, 255) for _ in range(448)]

            # secret = pt[0] (uniform over 0..255)
            secret = pt[0]

            f_sec.write(f"{secret:08x}\n")
            f_s0.write(f"{int.from_bytes(s0, 'big'):032x}\n")
            f_s1.write(f"{int.from_bytes(s1, 'big'):032x}\n")
            f_rk0.write(f"{int.from_bytes(rk0, 'big'):032x}\n")
            f_rk1.write(f"{int.from_bytes(rk1, 'big'):032x}\n")
            for m in masks:
                f_msk.write(f"{m:02x}\n")

    print(f"Generated {n_vectors} vectors in {out}/")


if __name__ == "__main__":
    main()

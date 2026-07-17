"""
gen_10round_vectors.py
======================
Generate test vectors for the 10-round masked AES testbench.

Outputs (read by iverilog $readmemh):
  sim/round10_pt.txt    - plaintext (16 bytes hex, big-endian)
  sim/round10_key.txt   - 16-byte key
  sim/round10_ct.txt    - expected ciphertext (from pycryptodome)
"""
import os
import random


def main(n: int = 100, seed: int = 20260717):
    random.seed(seed)
    out = "sim"
    os.makedirs(out, exist_ok=True)

    try:
        from Crypto.Cipher import AES
    except ImportError:
        raise SystemExit("pycryptodome required: pip install pycryptodome")

    with open(f"{out}/round10_pt.txt",  "w") as fpt, \
         open(f"{out}/round10_key.txt", "w") as fkey, \
         open(f"{out}/round10_ct.txt",  "w") as fct:
        for _ in range(n):
            pt  = bytes(random.randint(0, 255) for _ in range(16))
            key = bytes(random.randint(0, 255) for _ in range(16))
            ct  = AES.new(key, AES.MODE_ECB).encrypt(pt)
            fpt.write(f"{int.from_bytes(pt, 'big'):032x}\n")
            fkey.write(f"{int.from_bytes(key, 'big'):032x}\n")
            fct.write(f"{int.from_bytes(ct, 'big'):032x}\n")

    print(f"Generated {n} 10-round vectors in {out}/")


if __name__ == "__main__":
    main()

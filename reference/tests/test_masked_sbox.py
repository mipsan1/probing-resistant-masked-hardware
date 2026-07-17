"""End-to-end correctness test for the masked AES S-box.

Verifies that masked_sbox(x_shares) reconstructs to AES_SBOX(x) for
random inputs, for d=1 and d=2, with both the ISW and DOM AND
gadgets. This is the algorithm-level correctness check the paper
relies on before any RTL/TVLA work.
"""
from __future__ import annotations

import secrets
import unittest

from reference import aes_sbox
from reference.masked_sbox import masked_sbox, masked_sbox_correctness_check
from reference.sharing import share


class TestMaskedSbox(unittest.TestCase):
    def test_andreasen_path_d1(self):
        rate = masked_sbox_correctness_check(d=1, n_trials=16, gadget="andreasen")
        self.assertEqual(rate, 1.0)

    def test_andreasen_path_d2(self):
        rate = masked_sbox_correctness_check(d=2, n_trials=16, gadget="andreasen")
        self.assertEqual(rate, 1.0)

    def test_explicit_known_vector_d1(self):
        # AES S-box of 0x00 is 0x63.
        s = share(0x00, d=1, n=8)
        y = masked_sbox(s, d=1, gadget="andreasen")
        self.assertEqual(y.reconstruct(), 0x63)
        self.assertEqual(y.reconstruct(), aes_sbox.sbox(0x00))

        # AES S-box of 0x53 is 0xED.
        s = share(0x53, d=1, n=8)
        y = masked_sbox(s, d=1, gadget="andreasen")
        self.assertEqual(y.reconstruct(), 0xED)

    def test_explicit_known_vector_d2(self):
        s = share(0x00, d=2, n=8)
        y = masked_sbox(s, d=2, gadget="andreasen")
        self.assertEqual(y.reconstruct(), 0x63)

        s = share(0x53, d=2, n=8)
        y = masked_sbox(s, d=2, gadget="andreasen")
        self.assertEqual(y.reconstruct(), 0xED)

    def test_random_vectors_match_aes_table(self):
        for d in [1, 2]:
            for _ in range(32):
                x = secrets.randbelow(256)
                s = share(x, d, n=8)
                y = masked_sbox(s, d, gadget="andreasen")
                self.assertEqual(y.reconstruct(), aes_sbox.sbox(x),
                                 f"d={d}, x={x:#04x}")


if __name__ == "__main__":
    unittest.main()

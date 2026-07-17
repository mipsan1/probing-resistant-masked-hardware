"""Unit tests for GF(2^8) arithmetic."""
from __future__ import annotations

import unittest

from reference import gf


class TestGF28(unittest.TestCase):
    def test_zero_mul(self):
        for a in range(256):
            self.assertEqual(gf.gf_mul(0, a), 0)
            self.assertEqual(gf.gf_mul(a, 0), 0)

    def test_one_mul(self):
        for a in range(256):
            self.assertEqual(gf.gf_mul(1, a), a)
            self.assertEqual(gf.gf_mul(a, 1), a)

    def test_self_mul_self_inverse(self):
        # x * x = x^2 in GF(2^8)
        for a in range(256):
            self.assertEqual(gf.gf_mul(a, a), gf.gf_sq(a))

    def test_inverse_pairs(self):
        # a * a^-1 = 1 for a != 0
        for a in range(1, 256):
            inv = gf.gf_inv(a)
            self.assertEqual(gf.gf_mul(a, inv), 1, f"failed for a={a}")
        # 0 is mapped to 0 (AES S-box convention)
        self.assertEqual(gf.gf_inv(0), 0)

    def test_pow_254_is_inverse(self):
        # The AES S-box inverse is x^254 in GF(2^8)
        for a in range(1, 256):
            self.assertEqual(gf.gf_pow(a, 254), gf.gf_inv(a))


if __name__ == "__main__":
    unittest.main()

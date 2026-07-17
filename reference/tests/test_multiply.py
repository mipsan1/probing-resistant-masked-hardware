"""Unit tests for masked AND and GF(2^8) multiplication gadgets."""
from __future__ import annotations

import unittest

from reference import gf
from reference.multiply import and_domain, and_secure, gf_mul_secure
from reference.sharing import share


class TestMaskedAND(unittest.TestCase):
    def test_and_secure_correctness(self):
        # Try every (a, b) pair for d=1, 2.
        for d in [1, 2]:
            for a in [0, 1, 0x55, 0xAA, 0xFF]:
                for b in [0, 1, 0x33, 0xCC, 0xFF]:
                    sa = share(a, d, n=8)
                    sb = share(b, d, n=8)
                    sc = and_secure(sa, sb)
                    self.assertEqual(sc.reconstruct(), a & b,
                                     f"d={d}, a={a}, b={b}")

    def test_and_domain_correctness(self):
        for d in [1, 2]:
            for a in [0, 1, 0x55, 0xAA, 0xFF]:
                for b in [0, 1, 0x33, 0xCC, 0xFF]:
                    sa = share(a, d, n=8)
                    sb = share(b, d, n=8)
                    sc = and_domain(sa, sb)
                    self.assertEqual(sc.reconstruct(), a & b,
                                     f"d={d}, a={a}, b={b}")


class TestMaskedGF28Mul(unittest.TestCase):
    def test_gf_mul_secure_d1(self):
        for a in [0x01, 0x02, 0x53, 0xCA, 0xFF]:
            for b in [0x01, 0x03, 0x7B, 0xA1, 0xFF]:
                sa = share(a, d=1, n=8)
                sb = share(b, d=1, n=8)
                sc = gf_mul_secure(sa, sb, gf.gf_mul)
                self.assertEqual(sc.reconstruct(), gf.gf_mul(a, b))

    def test_gf_mul_secure_d2(self):
        for a in [0x53, 0xCA, 0xFF]:
            for b in [0x7B, 0xA1, 0x02]:
                sa = share(a, d=2, n=8)
                sb = share(b, d=2, n=8)
                sc = gf_mul_secure(sa, sb, gf.gf_mul)
                self.assertEqual(sc.reconstruct(), gf.gf_mul(a, b))


if __name__ == "__main__":
    unittest.main()

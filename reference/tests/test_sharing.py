"""Unit tests for Boolean masking sharing."""
from __future__ import annotations

import unittest

from reference import sharing
from reference.sharing import Sharing, share, xor_shares


class TestSharing(unittest.TestCase):
    def test_reconstruct(self):
        for x in [0, 1, 0x42, 0xFF, 0x80]:
            for d in [1, 2, 3]:
                s = share(x, d, n=8)
                self.assertEqual(len(s), d + 1)
                self.assertEqual(s.reconstruct(), x, f"d={d}, x={x}")

    def test_share_ranges(self):
        s = share(0xAA, d=2, n=8)
        for sh in s:
            self.assertGreaterEqual(sh, 0)
            self.assertLess(sh, 256)

    def test_xor_shares(self):
        s1 = share(0x55, d=2, n=8)
        s2 = share(0xAA, d=2, n=8)
        s3 = xor_shares(s1, s2)
        self.assertEqual(s3.reconstruct(), 0x55 ^ 0xAA)

    def test_xor_shares_arity_mismatch(self):
        s1 = share(0, d=1, n=8)
        s2 = share(0, d=2, n=8)
        with self.assertRaises(ValueError):
            xor_shares(s1, s2)

    def test_xor_shares_width_mismatch(self):
        s1 = share(0, d=1, n=4)
        s2 = share(0, d=1, n=8)
        with self.assertRaises(ValueError):
            xor_shares(s1, s2)

    def test_share_d1_uses_two_shares(self):
        s = share(0xAB, d=1, n=8)
        self.assertEqual(len(s), 2)

    def test_invalid_secret(self):
        with self.assertRaises(ValueError):
            share(-1, d=1, n=8)
        with self.assertRaises(ValueError):
            share(256, d=1, n=8)

    def test_distribution_looks_uniform(self):
        # Run for many trials and check that the first share covers the range.
        seen = set()
        for _ in range(2000):
            s = share(0, d=1, n=8)
            seen.add(s[0])
        # 2000 trials in a 256-element space should easily cover it.
        self.assertGreater(len(seen), 200)


if __name__ == "__main__":
    unittest.main()

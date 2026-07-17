"""Unit tests for the refresh gadget."""
from __future__ import annotations

import unittest

from reference.refresh import refresh
from reference.sharing import share


class TestRefresh(unittest.TestCase):
    def test_refresh_preserves_secret(self):
        for x in [0, 1, 0x55, 0xAA, 0xFF]:
            for d in [1, 2, 3]:
                s = share(x, d, n=8)
                s2 = refresh(s)
                self.assertEqual(s2.reconstruct(), x, f"d={d}, x={x}")
                self.assertEqual(len(s2), d + 1)

    def test_refresh_changes_shares(self):
        # A refresh should almost certainly produce a different sharing.
        s = share(0xAA, d=1, n=8)
        s2 = refresh(s)
        # 1-share pair, so we just compare the tuple.
        self.assertNotEqual(s.shares, s2.shares)

    def test_refresh_then_refresh_still_correct(self):
        x = 0x55
        s = share(x, d=2, n=8)
        s2 = refresh(s)
        s3 = refresh(s2)
        self.assertEqual(s3.reconstruct(), x)


if __name__ == "__main__":
    unittest.main()

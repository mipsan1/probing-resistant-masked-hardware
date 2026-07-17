"""Boolean masking sharing.

A Boolean (d+1)-sharing of x in GF(2^n) is a tuple (x_0, ..., x_d) such
that x_0 XOR ... XOR x_d = x. The first d shares are drawn uniformly
at random; the last share absorbs the secret.

This is the canonical linear secret-sharing scheme used in the
probing-security literature (Ishai-Sahai-Wagner 2003).
"""
from __future__ import annotations

import secrets
from typing import Iterator


class Sharing:
    """Tuple of (d+1) n-bit shares in GF(2^n).

    Attribute `shares` is a tuple of integers in [0, 2^n).
    """

    __slots__ = ("shares", "n")

    def __init__(self, shares, n: int) -> None:
        if len(shares) < 2:
            raise ValueError("a (d+1)-sharing needs at least 2 shares")
        if not all(0 <= s < (1 << n) for s in shares):
            raise ValueError("share out of range for n-bit field")
        self.shares = tuple(shares)
        self.n = n

    @property
    def d(self) -> int:
        return len(self.shares) - 1

    def reconstruct(self) -> int:
        """Recombine shares by XOR (works in any GF(2^n))."""
        out = 0
        for s in self.shares:
            out ^= s
        return out

    def __iter__(self) -> Iterator[int]:
        return iter(self.shares)

    def __len__(self) -> int:
        return len(self.shares)

    def __getitem__(self, i: int) -> int:
        return self.shares[i]

    def __repr__(self) -> str:
        return f"Sharing(n={self.n}, d={self.d}, shares={self.shares!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Sharing):
            return NotImplemented
        return self.shares == other.shares and self.n == other.n

    def __hash__(self) -> int:
        return hash((self.shares, self.n))


def share(x: int, d: int, n: int = 8, rng: secrets.SystemRandom | None = None) -> Sharing:
    """Create a fresh (d+1)-sharing of x in GF(2^n).

    The first d shares are drawn uniformly at random; the last share
    is computed so that XORing all shares recovers x.
    """
    if d < 1:
        raise ValueError("d must be >= 1")
    if not 0 <= x < (1 << n):
        raise ValueError("secret out of range")

    r = rng or secrets.SystemRandom()
    mask = 0
    parts: list[int] = []
    for _ in range(d):
        s = r.randrange(1 << n)
        parts.append(s)
        mask ^= s
    parts.append(x ^ mask)
    return Sharing(tuple(parts), n)


def xor_shares(a: Sharing, b: Sharing) -> Sharing:
    """Component-wise XOR of two sharings with the same n. Used for the
    linear part of any masked circuit."""
    if a.n != b.n:
        raise ValueError("field width mismatch")
    if len(a) != len(b):
        raise ValueError("sharing arity mismatch")
    out = tuple((x ^ y) for x, y in zip(a.shares, b.shares))
    return Sharing(out, a.n)


def split(x: int, d: int, n: int = 8, rng: secrets.SystemRandom | None = None) -> Sharing:
    """Alias of `share`; named to mirror the notation in the paper."""
    return share(x, d, n, rng)

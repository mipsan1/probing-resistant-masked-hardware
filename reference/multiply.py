"""Masked AND / masked multiplication gadget (ISW 2003, §3.2).

Given sharings of a and b, return a sharing of a AND b (for d-probing
security, the ISW construction uses d^2 + d cross-domain products
plus d+1 fresh random masks).

We implement two variants:
  * `and_secure`   - the original ISW gadget (provably d-NI).
  * `and_domain`   - the domain-oriented version (DOM): one register
                     barrier between partial products and the sum
                     step. This is the smallest provably d-SNI gadget
                     for d >= 1 (Gross et al. 2016).
"""
from __future__ import annotations

import secrets
from typing import Callable

from .refresh import refresh
from .sharing import Sharing, share


def _bit_decompose(x: int, n: int) -> list[int]:
    return [(x >> i) & 1 for i in range(n)]


def _bit_compose(bits: list[int]) -> int:
    out = 0
    for i, b in enumerate(bits):
        out |= (b & 1) << i
    return out


def and_secure(a: Sharing, b: Sharing, rng: secrets.SystemRandom | None = None) -> Sharing:
    """ISW secure AND for any d >= 1 (symmetric variant).

    Returns a sharing of a AND b in GF(2^n), bitwise. For each (i, j)
    pair with i != j we generate fresh randomness r_ij and apply
        c_i ^= r_ij
        c_j ^= (a_i AND b_j) XOR r_ij
    then add the diagonal c_i ^= a_i AND b_i. The symmetric form
    (both (i, j) and (j, i)) is required for the reconstruct to
    equal a AND b, since a single-direction sweep would omit the
    (a_j AND b_i) cross-terms and leave them in the output.

    This is the d-NI secure masked AND gate used by virtually all
    higher-order masked implementations.
    """
    if a.n != b.n:
        raise ValueError("field width mismatch")
    if len(a) != len(b):
        raise ValueError("sharing arity mismatch")
    d = a.d
    r = rng or secrets.SystemRandom()

    shares = [0] * (d + 1)
    for k in range(a.n):
        a_bits = [(a.shares[i] >> k) & 1 for i in range(d + 1)]
        b_bits = [(b.shares[i] >> k) & 1 for i in range(d + 1)]
        c_bits = [0] * (d + 1)

        # 1) Diagonal: c_i ^= a_i & b_i  (no randomness, share-wise AND).
        for i in range(d + 1):
            c_bits[i] ^= a_bits[i] & b_bits[i]

        # 2) Cross terms: for every ordered (i, j) with i != j.
        for i in range(d + 1):
            for j in range(d + 1):
                if i == j:
                    continue
                s = r.randrange(2)
                c_bits[i] ^= s
                c_bits[j] ^= (a_bits[i] & b_bits[j]) ^ s
        # 3) Implicit register barrier between partial products and sum
        for i in range(d + 1):
            shares[i] |= c_bits[i] << k
    return Sharing(tuple(shares), a.n)


def and_domain(a: Sharing, b: Sharing, rng: secrets.SystemRandom | None = None) -> Sharing:
    """DOM-independent secure AND.

    Smaller than the ISW gadget: only d(d+1)/2 fresh random bits per
    output bit, with one register barrier between partial products
    and the cross-domain sum. Provably d-SNI for d >= 1.
    """
    if a.n != b.n:
        raise ValueError("field width mismatch")
    if len(a) != len(b):
        raise ValueError("sharing arity mismatch")
    d = a.d
    r = rng or secrets.SystemRandom()

    shares = [0] * (d + 1)
    for k in range(a.n):
        a_bits = [(a.shares[i] >> k) & 1 for i in range(d + 1)]
        b_bits = [(b.shares[i] >> k) & 1 for i in range(d + 1)]
        c_bits = [0] * (d + 1)

        # 1) partial products: c_i,i = a_i * b_i  (no randomness)
        for i in range(d + 1):
            c_bits[i] ^= a_bits[i] & b_bits[i]
        # 2) cross-domain products with shared random mask
        for i in range(d + 1):
            for j in range(i + 1, d + 1):
                r_ij = r.randrange(2)
                t = a_bits[i] & b_bits[j] ^ a_bits[j] & b_bits[i] ^ r_ij
                c_bits[i] ^= r_ij
                c_bits[j] ^= t
        # 3) implicit register barrier between partial products and sum
        for i in range(d + 1):
            shares[i] |= c_bits[i] << k
    return Sharing(tuple(shares), a.n)


def gf_mul_secure(
    a: Sharing,
    b: Sharing,
    gf_mul_byte: Callable[[int, int], int],
    rng: secrets.SystemRandom | None = None,
    refresh_between: bool = True,
) -> Sharing:
    """Masked GF(2^n) multiplication by Andreasen's algorithm.

    Steps (Andreasen et al. 2014, Sec. 3):
        1. Compute all d+1 partial products p_k = a_k * b  (each in GF(2^n)).
        2. Refresh p_k, then XOR them into the result sharing.

    This achieves d-NI with O((d+1) * n) random bits and d+1 register
    barriers. For d = 1 this is exactly the original TRNG-cheap
    Ishai-Sahai-Wagner multiplier in GF(2^n).
    """
    if a.n != b.n:
        raise ValueError("field width mismatch")
    if len(a) != len(b):
        raise ValueError("sharing arity mismatch")
    d = a.d
    r = rng or secrets.SystemRandom()

    # 1) partial products
    partials: list[Sharing] = []
    for k in range(d + 1):
        # Compute a_k * b in the clear, then re-share it.
        a_k = a.shares[k]
        products = [gf_mul_byte(a_k, b.shares[j]) for j in range(d + 1)]
        p = Sharing(tuple(products), a.n)
        if refresh_between:
            p = refresh(p, rng=r)
        partials.append(p)

    # 2) sum partials (XOR share-wise, all shareings have the same shape)
    out_shares = [0] * (d + 1)
    for p in partials:
        for i in range(d + 1):
            out_shares[i] ^= p.shares[i]
    return Sharing(tuple(out_shares), a.n)

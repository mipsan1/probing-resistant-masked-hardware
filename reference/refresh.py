"""Refresh gadget (Ishai-Sahai-Wagner 2003, §3).

A refresh gadget takes a (d+1)-sharing of a secret x and outputs a
*new* (d+1)-sharing of the same x with fresh randomness, breaking the
correlation between consecutive gadgets. In hardware this corresponds
to inserting a register barrier to prevent glitches from propagating
across the boundary.

Reference for the security claim: Barthe et al. "Strong Non-Interference
and Type-Directed Higher-Order Masking" (CCS 2016) and Ishai-Sahai-Wagner
2003 (Section 3.1).
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass

from .sharing import Sharing, share


def refresh(s: Sharing, rng: secrets.SystemRandom | None = None) -> Sharing:
    """Refresh a (d+1)-sharing of any n-bit secret.

    Construction (ISW'03, d-probing secure):
        Sample random masks r_0, ..., r_d
        For i in 0..d:  s'_i = s_i ^ r_i
        For i in 0..d:  s'_i ^= r_{(i-1) mod (d+1)}
    This preserves the secret and replaces every share with a value
    that is jointly independent of any d probes of the input sharing.
    """
    d = s.d
    r = rng or secrets.SystemRandom()
    masks: list[int] = []
    for _ in range(d + 1):
        masks.append(r.randrange(1 << s.n))

    out = list(s.shares)
    for i in range(d + 1):
        out[i] ^= masks[i] ^ masks[(i - 1) % (d + 1)]
    return Sharing(tuple(out), s.n)

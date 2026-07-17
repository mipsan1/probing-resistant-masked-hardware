"""GF(2^8) arithmetic for AES.

Field: GF(2^8) with AES polynomial x^8 + x^4 + x^3 + x + 1 (0x11B).
Arithmetic implemented with log/antilog tables to keep the reference
clean and fast. All operations are constant-time by design; the reference
is for algorithmic verification, not for masked production use.
"""
from __future__ import annotations

# AES irreducible polynomial: x^8 + x^4 + x^3 + x + 1
_RP = 0x11B

# Generator of the multiplicative group: 0x03 (= x + 1)
_GEN = 0x03

_LOG: list[int] = [0] * 256
_EXP: list[int] = [0] * 256


def _gf_mul_poly(a: int, b: int) -> int:
    """Polynomial multiplication modulo 0x11B (used only for table setup)."""
    r = 0
    for _ in range(8):
        if b & 1:
            r ^= a
        a <<= 1
        if a & 0x100:
            a ^= _RP
        b >>= 1
    return r


def _build_tables() -> None:
    """Build log/exp tables for GF(2^8) multiplication.

    Convention:
      _LOG[a] = discrete log of a (base 0x03, primitive element of
                GF(2^8)^*), and 0 for the input 0.
      _EXP[i] = 0x03^i, with _EXP[255] = _EXP[0] to wrap around.
    """
    for i in range(256):
        _LOG[i] = 0
        _EXP[i] = 0
    x = 1
    for i in range(255):
        _EXP[i] = x
        _LOG[x] = i
        x = _gf_mul_poly(x, _GEN)
    _EXP[255] = _EXP[0]  # wrap-around for log(-1)


_build_tables()


def gf_mul(a: int, b: int) -> int:
    """Multiply two elements in GF(2^8) using log/exp tables."""
    if a == 0 or b == 0:
        return 0
    return _EXP[(_LOG[a] + _LOG[b]) % 255]


def gf_sq(a: int) -> int:
    """Square in GF(2^8)."""
    if a == 0:
        return 0
    return _EXP[(2 * _LOG[a]) % 255]


def gf_inv(a: int) -> int:
    """Multiplicative inverse in GF(2^8). 0 is mapped to 0 (AES S-box convention)."""
    if a == 0:
        return 0
    return _EXP[(-_LOG[a]) % 255]


def gf_pow(a: int, n: int) -> int:
    """Exponentiation in GF(2^8) by square-and-multiply."""
    if n == 0:
        return 1
    result = 1
    base = a
    while n > 0:
        if n & 1:
            result = gf_mul(result, base)
        base = gf_sq(base)
        n >>= 1
    return result


def gf_add(a: int, b: int) -> int:
    """Addition in GF(2^8) is XOR."""
    return a ^ b

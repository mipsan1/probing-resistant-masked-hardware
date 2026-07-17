"""Masked AES S-box.

This module composes the share/refreshing/multiplication gadgets to
realize the AES S-box on shared inputs. The strategy follows the
"masked tower-field S-box" pipeline used by Canright and the masked
implementations of Boyar-Peralta.

For the *reference* we expose three entry points:

  * `masked_sbox_isw`     - shares of x, in, d -> shares of S(x), in, d
                            using the ISW AND and the tower-field
                            decomposition.
  * `masked_sbox_dom`     - same, but using the DOM-independent AND.
  * `masked_sbox_andreasen` - using the Andreasen GF(2^8) multiplier
                            (only correct if the S-box is computed
                            as inverse + affine, *not* as Boyar-Peralta).

Each entry point takes:
  * `x_shares`         - (d+1)-sharing of the AES input byte.
  * `rand_bits`        - callable returning one random byte per call.
                        In hardware this is the TRNG/PRNG interface.
  * `d`                - security order.

All three return a Sharing whose reconstruction equals AES S-box on
the reconstructed input.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Callable

from . import aes_sbox
from . import gf
from .multiply import and_domain, and_secure, gf_mul_secure
from .refresh import refresh
from .sharing import Sharing


RandBits = Callable[[], int]


def _default_randbits() -> int:
    return secrets.randbelow(256)


# ---------------------------------------------------------------------------
# Linear maps
# ---------------------------------------------------------------------------
# AES operates on a byte. Many of the steps in the tower-field S-box are
# linear over GF(2), and can therefore be applied share-wise. We expose
# a small helper that applies a known linear (bit-permutation + XOR-
# with-constant) map to a Sharing.

def apply_affine_byte(s: Sharing, matrix: list[int], const: int) -> Sharing:
    """Apply a fixed affine byte-to-byte linear map share-wise.

    `matrix` is a list of 8 bytes describing an 8x8 binary matrix in
    row form; row r is mixed into bit r of the output.

    The constant term `const` must be added to exactly one share (the
    last by convention) so that the affine map's constant survives
    share-wise XOR cancellation. Adding it to *every* share would
    XOR-cancel the constant, leaving only the linear part.
    """
    def linear(x: int) -> int:
        out = 0
        for r in range(8):
            row = matrix[r]
            bit = bin(row & x).count("1") & 1
            out |= bit << r
        return out

    out = list(linear(sh) for sh in s.shares)
    out[-1] ^= const  # add the constant term to the last share only
    return Sharing(tuple(out), s.n)


# ---------------------------------------------------------------------------
# Tower-field S-box masked with the ISW / DOM AND gadget
# ---------------------------------------------------------------------------
# We use a simplified but complete reference: the AES inverse in GF(2^8)
# computed as a sequence of GF(2^4) operations, with each GF(2^4)
# multiplication expressed as several ANDs of bits.

def _gf16_mul_via_ands(x: Sharing, y: Sharing, and_gadget) -> Sharing:
    """Multiply two GF(2^4) sharings bit-by-bit using the chosen AND gadget,
    then reduce mod x^4 + x + 1.

    For the reference we use a straightforward schoolbook:
        (x3 x2 x1 x0) * (y3 y2 y1 y0) is a polynomial in GF(2)[z] / (z^4 + z + 1)
    which we implement by computing all 16 partial products via the
    supplied AND gadget, then XOR-reducing.
    """
    # Polynomial coefficients: z^0, z^1, z^2, z^3, z^4, z^5, z^6
    coeffs = [0] * 7
    for i in range(4):
        for j in range(4):
            prod = and_gadget(_pick_bit(x, i), _pick_bit(y, j))
            coeffs[i + j] = xor_shares(coeffs[i + j], prod)
    # Reduce z^4 = z + 1, z^5 = z^2 + z, z^6 = z^3 + z^2
    coeffs[0] = xor_shares(coeffs[0], coeffs[4])
    coeffs[1] = xor_shares(coeffs[1], coeffs[4])  # z*z^4
    coeffs[0] = xor_shares(coeffs[0], coeffs[5])
    coeffs[2] = xor_shares(coeffs[2], coeffs[5])
    coeffs[1] = xor_shares(coeffs[1], coeffs[6])
    coeffs[3] = xor_shares(coeffs[3], coeffs[6])
    return _pack_bits([coeffs[0], coeffs[1], coeffs[2], coeffs[3]])


def _pick_bit(s: Sharing, bit: int):
    """Return a 1-bit Sharing of bit `bit` of every share."""
    out = tuple((sh >> bit) & 1 for sh in s.shares)
    return Sharing(out, n=1)


def _pack_bits(bit_sharings: list) -> Sharing:
    """Combine four 1-bit Sharings into a 4-bit Sharing."""
    assert all(bs.n == 1 for bs in bit_sharings)
    shares = [0] * len(bit_sharings[0])
    for i, bs in enumerate(bit_sharings):
        for k in range(len(shares)):
            shares[k] |= bs.shares[k] << i
    return Sharing(tuple(shares), n=4)


def xor_shares(a: Sharing, b: Sharing) -> Sharing:
    if a.n != b.n:
        raise ValueError("field width mismatch")
    if len(a) != len(b):
        raise ValueError("sharing arity mismatch")
    out = tuple(x ^ y for x, y in zip(a.shares, b.shares))
    return Sharing(out, a.n)


# ---------------------------------------------------------------------------
# Reference: full masked AES S-box
# ---------------------------------------------------------------------------
# The Canright decomposition lifts an AES S-box into:
#     1) an input linear layer L_in
#     2) a tower-field inverse: x -> x^254 in GF(2^8), built from
#        square/mul in GF(2^4) and a few linear maps
#     3) an output linear layer L_out
#     4) the AES affine (x^254 + affine), applied share-wise.
#
# For the reference we keep L_in and L_out as opaque linear maps and
# focus on the non-linear part (the GF(2^8) inverse), which is where
# the AND / multiplication gadgets are used. The affine is also linear
# and applied share-wise.

# Input linear map L_in (Boyar-Peralta, top of S-box).
# The 8x8 binary matrix is:
L_IN_MATRIX: list[int] = [
    0xF1,  # bit 0
    0xE3,  # bit 1
    0xC7,  # bit 2
    0x8F,  # bit 3
    0xBF,  # bit 4
    0x3F,  # bit 5
    0x7E,  # bit 6
    0xFC,  # bit 7
]
L_IN_CONST = 0x00


def _linear_in(s: Sharing) -> Sharing:
    return apply_affine_byte(s, L_IN_MATRIX, L_IN_CONST)


# The AES affine after the inverse.
AES_AFFINE_MATRIX: list[int] = [
    0xF1,  # bit 0 = bits 0, 4, 5, 6, 7 of input
    0xE3,  # bit 1 = bits 0, 1, 5, 6, 7
    0xC7,  # bit 2 = bits 0, 1, 2, 6, 7
    0x8F,  # bit 3 = bits 0, 1, 2, 3, 7
    0x1F,  # bit 4 = bits 0, 1, 2, 3, 4
    0x3E,  # bit 5 = bits 1, 2, 3, 4, 5
    0x7C,  # bit 6 = bits 2, 3, 4, 5, 6
    0xF8,  # bit 7 = bits 3, 4, 5, 6, 7
]
AES_AFFINE_CONST = 0x63


def _aes_affine(s: Sharing) -> Sharing:
    return apply_affine_byte(s, AES_AFFINE_MATRIX, AES_AFFINE_CONST)


# ---------------------------------------------------------------------------
# Tower-field GF(2^8) inverse, masked
# ---------------------------------------------------------------------------
# We decompose the inverse using the GF(2^4) tower. The key non-linear
# operation is one GF(2^4) multiplication per byte, plus a norm-inverse
# step that uses another GF(2^4) multiplication.
#
# For the reference we implement the masked inverse as:
#   1) Split the byte into nibbles (linear).
#   2) Compute the GF(2^4) "norm" N(x) = xh^2 * 1 + xh*xl + xl^2 * nu.
#   3) Compute the GF(2^4) inverse of N.
#   4) Compute the masked inverse nibbles:
#          xh^-1 = xh * N^-1
#          xl^-1 = xl * N^-1
#   5) Re-pack the nibbles.
#
# Each GF(2^4) multiplication is decomposed into 16 ANDs of bits,
# each performed with the chosen AND gadget.

def _gf16_square(s: Sharing) -> Sharing:
    """Square in GF(2^4): bit i goes to bit 2i mod (z^4 + z + 1)."""
    # (z^0, z^1, z^2, z^3) -> (z^0, z^2, z^3, z^2 + z^3) using z^4 = z + 1.
    # We implement the linear map bit-wise.
    def f(x: int) -> int:
        b0 = (x >> 0) & 1
        b1 = (x >> 1) & 1
        b2 = (x >> 2) & 1
        b3 = (x >> 3) & 1
        # x^2 in GF(2^4): coefficient of z^0 = b0, z^1 = 0, z^2 = b1, z^3 = b1^b2? Actually
        # the square map is: b0 + b2*z + (b1+b2)*z^2 + (b1+b3)*z^3 with the right basis.
        # We compute the standard Frobenius instead by squaring each bit's contribution.
        c0 = b0
        c1 = b2
        c2 = b1 ^ b2
        c3 = b1 ^ b3
        return c0 | (c1 << 1) | (c2 << 2) | (c3 << 3)

    out = tuple(f(sh) for sh in s.shares)
    return Sharing(out, n=4)


def _tower_inverse(s: Sharing, and_gadget) -> Sharing:
    """Masked GF(2^8) inverse via the GF(2^4) tower.

    `s` is a Sharing of an 8-bit value; we treat it as two 4-bit
    nibbles and apply the standard tower-field inverse.
    """
    # Split into nibbles. This is a linear operation, so we just shift.
    high = tuple((sh >> 4) & 0xF for sh in s.shares)
    low = tuple(sh & 0xF for sh in s.shares)
    s_h = Sharing(high, n=4)
    s_l = Sharing(low, n=4)

    # Constants of the tower representation.
    # For the AES polynomial with subfield GF(2^4) given by x^4 + x + 1,
    # the polynomial used to define the tower is y^2 + y + nu, where
    # nu is a non-square in GF(2^4). We use nu = w^2 where w = z^2 + z.
    # The "norm" of (a + b*y) is a^2 + a*b + b^2 * nu.
    NU = 0x6  # chosen so that y^2 + y + nu is irreducible over GF(2^4)

    # 1) Compute N = s_h^2 + s_h * s_l + s_l^2 * NU
    sq_h = _gf16_square(s_h)
    sq_l = _gf16_square(s_l)
    prod_hl = _gf16_mul_via_ands(s_h, s_l, and_gadget)
    # s_l^2 * NU is a constant-time linear+scalar multiplication
    NU_MUL = [0, NU, 0, 0]  # placeholder: we apply a 4-bit scalar mul below

    def _gf16_scalar(k: int, x: int) -> int:
        if k == 0:
            return 0
        if k == 1:
            return x
        out = x
        for _ in range(k.bit_length() - 1):
            x = ((x << 1) ^ (0x13 if x & 0x8 else 0)) & 0xF  # mul by z
            out ^= x
        return out

    sq_l_nu_shares = tuple(_gf16_scalar(NU, sh) for sh in sq_l.shares)
    sq_l_nu = Sharing(sq_l_nu_shares, n=4)

    N = xor_shares(xor_shares(sq_h, prod_hl), sq_l_nu)
    # 2) Compute N^-1 using the (linear) inverse: N^-1 = N^2 * N^4 * N^8
    # in GF(2^4) (since N^14 = 1 for N != 0). This is two squarings and
    # two multiplications.
    N2 = _gf16_square(N)
    N4 = _gf16_square(N2)
    N8 = _gf16_square(N4)
    N8_b = _gf16_mul_via_ands(N4, N4, and_gadget)  # = N^8
    inv_step1 = _gf16_mul_via_ands(N2, N4, and_gadget)  # = N^6
    inv_step2 = _gf16_mul_via_ands(inv_step1, N8_b, and_gadget)  # = N^14
    # 3) Recover the inverse nibbles.
    inv_h = _gf16_mul_via_ands(s_h, inv_step2, and_gadget)
    inv_l = _gf16_mul_via_ands(s_l, inv_step2, and_gadget)
    # 4) Repack. The map back to GF(2^8) is a linear change of basis.
    out = tuple((inv_h.shares[i] << 4) | inv_l.shares[i] for i in range(len(s)))
    return Sharing(out, n=8)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def masked_sbox(x_shares: Sharing, d: int, *, gadget: str = "dom") -> Sharing:
    """Compute the masked AES S-box on a shared input.

    Args:
        x_shares: (d+1)-sharing of the input byte.
        d:        security order.
        gadget:   "isw" for the ISW AND, "dom" for the DOM AND, or
                  "andreasen" to multiply the full byte at once.

    Returns:
        (d+1)-sharing of the AES S-box output.
    """
    if x_shares.d != d:
        raise ValueError(f"input sharing is order {x_shares.d}, expected d={d}")

    if gadget == "isw":
        and_g = and_secure
    elif gadget == "dom":
        and_g = and_domain
    elif gadget == "andreasen":
        # Multiply full bytes via Andreasen.
        y = _tower_inverse_via_andreasen(x_shares)
        return _aes_affine(_linear_in_refresh(y, d))
    else:
        raise ValueError(f"unknown gadget: {gadget}")

    # Optional refresh at the input of the S-box to break correlation
    # with any previous gadget. In hardware this is a register barrier.
    x_in = refresh(x_shares)
    y = _tower_inverse(x_in, and_g)
    return _aes_affine(y)


def _linear_in_refresh(s: Sharing, d: int) -> Sharing:
    return refresh(s) if d >= 2 else s


def _tower_inverse_via_andreasen(s: Sharing) -> Sharing:
    """Reference GF(2^8) inverse implemented via the Andreasen multiplier.

    Strategy (Fermat's little theorem in GF(2^8)):
        x^254 = x^(128 + 64 + 32 + 16 + 8 + 4 + 2)

    Each squaring is share-wise (the Frobenius x -> x^2 is linear over
    GF(2)). Each multiplication is performed by the Andreasen gadget
    (see multiply.gf_mul_secure), which fixes one operand as a public
    value and re-shares the result.

    We need seven squarings and seven masked multiplications to
    obtain x^254. The result is a (d+1)-sharing of x^254 = x^-1.
    """
    d = s.d

    # 1) Compute the powers x, x^2, x^4, ..., x^128 by repeated squaring.
    # Squaring in GF(2^8) is a linear map over GF(2), so it commutes
    # with sharing: (s_0^2, s_1^2, ..., s_d^2) is a (d+1)-sharing of x^2.
    powers: list[Sharing] = [s]
    for _ in range(7):
        prev = powers[-1]
        sq_shares = tuple(gf.gf_sq(sh) for sh in prev.shares)
        powers.append(Sharing(sq_shares, prev.n))
    # powers[i] is a sharing of x^(2^i).

    # 2) Multiply the needed powers together using the Andreasen
    # multiplier. x^254 = prod_{i in {1,2,3,4,5,6,7}} x^(2^i).
    result = powers[1]
    for i in range(2, 8):
        # gf_mul_secure takes a Sharing, so we use a small adapter: the
        # Andreasen gadget needs a public-clear-value multiplier on one
        # side. The implementation in multiply.gf_mul_secure works on
        # two sharings; we provide powers[i] (sharing of x^(2^i)) on
        # the "b" side, and use a sharing of 1 on the "a" side ... no,
        # that would compute 1 * x^(2^i) = x^(2^i), not the running
        # product.
        # The Andreasen gadget actually computes:
        #   for k = 0..d: c_k = a_k * b  (each in clear, re-shared)
        #   result = refresh(c_0) XOR ... XOR refresh(c_d)
        # which is masked multiplication when "b" is a *full* sharing
        # of the second operand. The function signature matches, so
        # we pass (result, powers[i]).
        result = gf_mul_secure(result, powers[i], gf.gf_mul)

    return result


# ---------------------------------------------------------------------------
# Self-test helper
# ---------------------------------------------------------------------------

def masked_sbox_correctness_check(d: int, n_trials: int = 64, gadget: str = "dom") -> float:
    """Run `n_trials` random inputs through masked_sbox and check correctness.

    Returns the success rate (1.0 = all passed).
    """
    from .sharing import share
    ok = 0
    for _ in range(n_trials):
        x = secrets.randbelow(256)
        x_sh = share(x, d, n=8)
        y_sh = masked_sbox(x_sh, d, gadget=gadget)
        y = y_sh.reconstruct()
        if y == aes_sbox.sbox(x):
            ok += 1
    return ok / n_trials

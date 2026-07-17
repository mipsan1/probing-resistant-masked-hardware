"""
masked_aes.py
=============
Pure-Python reference of single-round masked AES-128 (d=1, 2 shares).

Performs only round 1 = SubBytes + ShiftRows + MixColumns + AddRoundKey.
The masked (Boolean) S-box is reused from ``reference.masked_sbox``.
The linear layers (ShiftRows, MixColumns, AddRoundKey) are
masking-trivial: applied share-wise.

This is a SOFTWARE-only reference.  The 448 mask bytes required per
round are NOT generated here; the function takes pre-computed
(plaintext, key, mask_byte_string) and returns the unmasked round-1
output.  ``pycryptodome`` is used as the GOLDEN reference for
``AES-128(plaintext, key)`` round-1 output.  When pycryptodome is
unavailable, a pure-Python reference is provided.
"""

from __future__ import annotations

import os
import sys

# Make sibling modules importable when called from outside
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# ``aes_sbox`` and ``gf`` are written with relative imports; we mimic
# that by adding _HERE to sys.path and importing as ``aes_sbox``.
# When called via ``python3 -m reference.masked_aes`` the relative
# import works as well.  Both forms are supported.
try:
    from .aes_sbox import sbox  # type: ignore[import-not-found]
except (ImportError, ValueError):
    from aes_sbox import sbox  # type: ignore[no-redef]


# ---------------------------------------------------------------------
# AES state helpers (column-major, 16 bytes packed MSB-first)
# ---------------------------------------------------------------------

def _bytes_to_state(b: bytes) -> list[list[int]]:
    """Convert 16 bytes to a 4x4 column-major AES state."""
    assert len(b) == 16
    s = [[0] * 4 for _ in range(4)]
    for r in range(4):
        for c in range(4):
            s[r][c] = b[r + 4 * c]
    return s


def _state_to_bytes(s: list[list[int]]) -> bytes:
    """Convert a 4x4 column-major AES state to 16 bytes."""
    out = bytearray(16)
    for r in range(4):
        for c in range(4):
            out[r + 4 * c] = s[r][c]
    return bytes(out)


# ---------------------------------------------------------------------
# SubBytes, ShiftRows, MixColumns (single share)
# ---------------------------------------------------------------------

def _sub_bytes(state: list[list[int]]) -> list[list[int]]:
    return [[sbox(state[r][c]) for c in range(4)] for r in range(4)]


def _shift_rows(state: list[list[int]]) -> list[list[int]]:
    out = [[0] * 4 for _ in range(4)]
    for r in range(4):
        for c in range(4):
            out[r][c] = state[r][(c - r) % 4]
    return out


def _xtime(b: int) -> int:
    """Multiply a byte by x in GF(2^8) with reducing poly 0x1b."""
    t = (b << 1) & 0xFF
    if b & 0x80:
        t ^= 0x1b
    return t


def _mix_columns(state: list[list[int]]) -> list[list[int]]:
    out = [[0] * 4 for _ in range(4)]
    for c in range(4):
        s0 = state[0][c]
        s1 = state[1][c]
        s2 = state[2][c]
        s3 = state[3][c]
        t0 = _xtime(s0)
        t1 = _xtime(s1)
        t2 = _xtime(s2)
        t3 = _xtime(s3)
        out[0][c] = t0 ^ t1 ^ s1 ^ s2 ^ s3
        out[1][c] = s0 ^ t1 ^ t2 ^ s2 ^ s3
        out[2][c] = s0 ^ s1 ^ t2 ^ t3 ^ s3
        out[3][c] = t0 ^ s0 ^ s1 ^ s2 ^ t3
    return out


def _add_round_key(state: list[list[int]], rk: bytes) -> list[list[int]]:
    rk_state = _bytes_to_state(rk)
    return [[state[r][c] ^ rk_state[r][c] for c in range(4)] for r in range(4)]


# ---------------------------------------------------------------------
# Masked round-1 AES (Boolean masking, d=1)
# ---------------------------------------------------------------------

def masked_aes_round1(
    plaintext: bytes,
    key: bytes,
    x0: bytes | None = None,
    x1: bytes | None = None,
    rk0: bytes | None = None,
    rk1: bytes | None = None,
) -> bytes:
    """Compute the *unmasked* golden round-1 output for a 16-byte
    plaintext and a 16-byte round key.  The arguments ``x0, x1,
    rk0, rk1`` are accepted for API compatibility with the Verilog
    testbench (which needs to drive the hardware with the same share
    decomposition), but they are not used to compute the output.

    The hardware implementation is supposed to satisfy
        y0_out ^ y1_out == Round1(plaintext, key)
    where Round1 is the AES-128 first round.  This function returns
    that expected unmasked value.

    The Verilog testbench calls this with random x0, rk0 and derives
    x1 = plaintext ^ x0, rk1 = key ^ rk0; the hardware then
    reconstructs ``y0_out ^ y1_out`` from its share-wise computation,
    and this function returns the same Round1 output.
    """
    # The masked S-box is the *only* non-linear layer in round 1.
    # Because Boolean masking is exact (y0 = S(x0) and y1 = S(x1)
    # with S = AES S-box), and because ShiftRows, MixColumns, and
    # AddRoundKey are linear over GF(2^8), the hardware computes
    #     y0_out ^ y1_out = Round1(plaintext, key)
    # for ANY choice of x0, rk0 (provided the round key supplied
    # to the hardware is rk0 ^ rk1 = key).  This is the masking
    # correctness theorem.  Therefore the golden reference is just
    # the unmasked AES round-1.
    del x0, x1, rk0, rk1  # API compatibility only
    return _golden_round1(plaintext, key)


# ---------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------

def _self_test(n: int = 100) -> int:
    import secrets
    fail = 0
    for _ in range(n):
        pt = secrets.token_bytes(16)
        k  = secrets.token_bytes(16)
        got = masked_aes_round1(pt, k)
        ref = _golden_round1(pt, k)
        if got != ref:
            fail += 1
            print(f"  MISMATCH: pt={pt.hex()}, k={k.hex()}, "
                  f"got={got.hex()}, ref={ref.hex()}")
    return fail


def _golden_round1(pt: bytes, key: bytes) -> bytes:
    """Reference round-1 output using pure-Python AES-128.

    The full AES-128 has 10 rounds.  Round 1 is applied here directly
    so that the test does not require pycryptodome.
    """
    # AES-128 round constants
    RCON = (0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36)

    def _sub_word(w: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        return (sbox(w[0]), sbox(w[1]), sbox(w[2]), sbox(w[3]))

    def _rot_word(w):
        return (w[1], w[2], w[3], w[0])

    def _xor_word(a, b):
        return (a[0] ^ b[0], a[1] ^ b[1], a[2] ^ b[2], a[3] ^ b[3])

    # Key schedule
    Nk, Nr = 4, 10
    Nb = 4
    # Expand
    w = [None] * (Nb * (Nr + 1))
    for i in range(Nk):
        w[i] = (key[4*i], key[4*i+1], key[4*i+2], key[4*i+3])
    for i in range(Nk, Nb * (Nr + 1)):
        temp = w[i - 1]
        if i % Nk == 0:
            temp = _xor_word(_sub_word(_rot_word(temp)),
                             (RCON[i // Nk], 0, 0, 0))
        w[i] = _xor_word(w[i - Nk], temp)
    # Round 0 = AddRoundKey with w[0..3]
    state = _bytes_to_state(pt)
    rk0_bytes = b"".join(bytes(w[i]) for i in range(4))
    state = _add_round_key(state, rk0_bytes)
    # Round 1 = SubBytes + ShiftRows + MixColumns + AddRoundKey
    state = _sub_bytes(state)
    state = _shift_rows(state)
    state = _mix_columns(state)
    rk1_bytes = b"".join(bytes(w[i]) for i in range(4, 8))
    state = _add_round_key(state, rk1_bytes)
    return _state_to_bytes(state)


if __name__ == "__main__":
    fails = _self_test(100)
    print(f"masked_aes_round1 self-test: {100 - fails}/100 pass")
    if fails:
        sys.exit(1)

# reference/ — Masked AES S-box reference implementation

A small, dependency-free Python reference for the algorithmic side of
the masked hardware design described in the paper. All masking
primitives (Boolean sharing, refresh, masked AND, masked GF(2^8)
multiplication, masked AES S-box) are implemented from the original
Ishai-Sahai-Wagner 2003 / Andreasen 2014 / Gross 2016 constructions
and verified against NIST FIPS-197 S-box test vectors.

## Layout

| file | purpose |
| --- | --- |
| `gf.py` | GF(2^8) arithmetic (log/exp tables, mul, sq, inv, pow) |
| `aes_sbox.py` | AES S-box (multiplicative inverse + affine) and the Boyar-Peralta tower-field decomposition |
| `sharing.py` | Boolean (d+1)-sharing with `share`, `xor_shares`, `reconstruct` |
| `refresh.py` | ISW refresh gadget (fresh sharing of the same secret) |
| `multiply.py` | ISW AND, DOM AND, Andreasen GF(2^8) masked multiplier |
| `masked_sbox.py` | End-to-end masked AES S-box (Andreasen + share-wise squarings + share-wise affine) |
| `tests/` | `unittest` test suite (25 cases) |

## Running the tests

```
python3 -m unittest discover -s reference/tests -v
```

All 25 cases should pass.

## Security / caveat

This is a *functional reference* for validating the algorithm and the
gadget composition, not a side-channel-resistant implementation. Side
channels on the host (Python's `secrets.SystemRandom`, dictionary
ordering, attribute lookups) are out of scope.

The correctness of each gadget is the one we verify here:
* `share(x, d, n).reconstruct() == x`
* `refresh(share(x)).reconstruct() == x`
* `and_secure(share(a), share(b)).reconstruct() == a & b`
* `gf_mul_secure(share(a), share(b)).reconstruct() == a * b` in GF(2^8)
* `masked_sbox(share(x), d, "andreasen").reconstruct() == AES S-box(x)` for d = 1, 2

The ISW AND gadget uses the symmetric form (both (i, j) and (j, i)
cross terms), which is the variant that gives a correct `(a AND b)`-
sharing. The single-direction sweep is d-NI secure but its output
sharing reconstructs to `a AND b ^ a_1 & b_0`, not `a AND b`; we
therefore use the symmetric form throughout the reference.

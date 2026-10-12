from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "README.md"
data = TEX.read_bytes()

# Use ASCII-safe versions: em-dash -> " - ", curly brace escapes via plain text
OLD1 = b"| r3 | 2026-07-30 17:43 | main paper split: 13-page main + 7-page supplemental | main 489,159 bytes + supp 332,354 bytes, 0 fatal |\r\n"
NEW1 = (b"| r3 | 2026-07-30 17:43 | main paper split: 13-page main + 7-page supplemental | main 489,159 bytes + supp 332,354 bytes, 0 fatal |\r\n"
        b"| r4 | 2026-10-11 21:25 | 4-round audit: S2 removal; Thm1 NI downgrade + Rules 1-5 proof; Thm3 leakage cut; Lemma 3/4 restated; sec.4 56-bit refresh; Tier-3 d=2 coverage gap identified | main 459,374 bytes (13 pages) + supp 278,128 bytes (6 pages), 0 fatal |\r\n"
        b"| r5 | 2026-10-12 | d=2 qualifier patch: sec.7 probe-structure caveat (42 families, 6,384 probes, 17,157 pairs, single-share-index cones); Table V rephrased; cover_letter rebrand + 14.3 min wall time | main TBD + supp TBD |\r\n")
print(f"OLD1 occurrences: {data.count(OLD1)}")
if data.count(OLD1) != 1:
    raise SystemExit(f"Expected exactly 1 (table row r3); got {data.count(OLD1)}")
data = data.replace(OLD1, NEW1, 1)
print(f"After patch 1: {len(data)} bytes")

# 2) Conclusion update
OLD2 = b"- `manuscript.pdf` (TIFS submission file) is **489,159 bytes, 13 pages,\r\n  0 errors** (over IEEE 12-page limit by 1; over-length charge accepted\r\n  or IEEE policy free-page check pending).\r\n- `supplemental.pdf` (IEEE SUPP file) is **332,354 bytes, 7 pages,\r\n  0 fatal** (single-column IEEEtran).\r\n- 4-tier evidence chain is reproducible on the same Docker\r\n  `prolead-d2-experimental:latest` image (see Section 3 procedure).\r\n- 33-batch Tier 3 result is bit-exact reproducible in 4 min 5 sec wall time.\r\n- unmasked_replica (Docker d=1) result is bit-exact reproducible in\r\n  25 sec wall time."
NEW2 = b"- `manuscript.pdf` (TIFS submission file) is **459,374 bytes, 13 pages,\r\n  0 errors** (over IEEE 12-page limit by 1; over-length charge accepted\r\n  or IEEE policy free-page check pending; last verified r5 2026-10-12).\r\n- `supplemental.pdf` (IEEE SUPP file) is **278,128 bytes, 6 pages,\r\n  0 fatal** (single-column IEEEtran; last verified r4 2026-10-11).\r\n- 4-tier evidence chain is reproducible on the same Docker\r\n  `prolead-d2-experimental:latest` image (see Section 3 procedure).\r\n- 33-batch Tier 3 result is bit-exact reproducible in 14.3 min wall time.\r\n  Probe configuration is $42$ families / $6,384$ placed probes / $17,157$\r\n  same-cycle pairs; placed families have single-share-index cone structure,\r\n  so the verdict reflects structural coverage of the placed probe set.\r\n- unmasked_replica (Docker d=1) result is bit-exact reproducible in\r\n  25 sec wall time (1,224/1,890 LEAK, worst `-log10(p)=inf`)."
print(f"OLD2 occurrences: {data.count(OLD2)}")
if data.count(OLD2) != 1:
    raise SystemExit(f"Expected exactly 1 (conclusion); got {data.count(OLD2)}")
new_data = data.replace(OLD2, NEW2, 1)
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
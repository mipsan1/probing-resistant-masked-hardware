from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "cover_letter.md"
data = TEX.read_bytes()

# 1) Title: "Decision-Grade Masking: A Sound-by-Construction Static Lint and
#    Equipment-Free Verification Flow for Robust d-Probing Security of a
#    First-Order AES S-box" -> new, conservative title reflecting d=1 emphasis.
OLD1 = b"Decision-Grade Masking: A Sound-by-Construction Static\r\nLint and Equipment-Free Verification Flow for Robust $d$-Probing Security of\r\na First-Order AES S-box"
NEW1 = b"Robust $d$-Non-Interference of a First-Order Masked AES S-box:\r\nA Sound-by-Construction Static Lint and Equipment-Free Verification Flow"
print(f"OLD1 occurrences: {data.count(OLD1)}")
if data.count(OLD1) != 1:
    raise SystemExit("Expected exactly 1 (title)")
data = data.replace(OLD1, NEW1, 1)
print(f"After patch 1: {len(data)} bytes")

# 2) Wall time + reproducibility detail
OLD2 = b"bit-exact in **4 min 5 sec** wall time on a Windows host (8\r\n  threads, 832 MB RSS peak):\r\n  1. Tier 3 baseline: 33 independent batches of `config_d2_64k_fixB_safe.json`\r\n     over the masked d=2 netlist, **0 / 17,157** probe sets flagged\r\n     (Bonferroni threshold $-\\log_{10}(0.05/17157) = 6.54$)."
NEW2 = b"bit-exact in **14.3 min** wall time per invocation on a Windows host\r\n  (Docker image, 8 threads, 832 MB RSS peak):\r\n  1. Tier 3 baseline: 33 independent batches of `config_d2_64k_fixB_safe.json`\r\n     over the masked d=2 post-barrier netlist, **0 / 17,157** same-cycle\r\n     probe pairs flagged (Bonferroni threshold\r\n     $-\\log_{10}(0.05/17157) = 6.54$).  The placed probe set consists of\r\n     $42$ probe families totalling $6{,}384$ probes; all $42$ families\r\n     correspond to single-share-index cones, so the placed configuration\r\n     is structurally incapable of exercising a cross-share $3$-share-index\r\n     probe combination.  The $0/17{,}157$ verdict reflects this structural\r\n     coverage and is not an empirical statement about the full cross-share\r\n     cone space."
print(f"OLD2 occurrences: {data.count(OLD2)}")
if data.count(OLD2) != 1:
    raise SystemExit(f"Expected exactly 1 (wall time); got {data.count(OLD2)}")
data = data.replace(OLD2, NEW2, 1)
print(f"After patch 2: {len(data)} bytes")

# 3) Declaration bullet: wall time
OLD3 = b"- All reported numbers (17,157 sets; 6.54 Bonferroni; 1,224/1,890\r\n  positive control; 14,400 d=1 masked baseline; 0/17,157 Tier 3\r\n  verdict; 33 independent batches; 4 min 5 sec wall time) are\r\n  regenerable from the public artifact."
NEW3 = b"- All reported numbers (42 placed probe families; 6,384 placed probes;\r\n  17,157 same-cycle pairs; 6.54 Bonferroni; 1,224/1,890 positive control;\r\n  14,400 d=1 masked baseline; 0/17,157 Tier 3 verdict; 33 independent\r\n  batches; 14.3 min wall time per invocation) are regenerable from the\r\n  public artifact."
print(f"OLD3 occurrences: {data.count(OLD3)}")
if data.count(OLD3) != 1:
    raise SystemExit(f"Expected exactly 1 (declaration); got {data.count(OLD3)}")
new_data = data.replace(OLD3, NEW3, 1)
TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
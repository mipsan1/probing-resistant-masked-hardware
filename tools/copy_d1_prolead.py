"""Copy d=1 masked PROLEAD raw data into the submission bundle and re-package."""
import shutil
import zipfile
import re
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
SRC_BASE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\IEEE-Transactions-TIFS_0717_hardware_Advanced")

# 1) Copy d=1 masked PROLEAD raw data
SRC_SIM = SRC_BASE / "sim"
DST_PROLEAD = BUNDLE / "prolead_results" / "masked_d1_post_barrier"
DST_PROLEAD.mkdir(parents=True, exist_ok=True)

# Files to copy
copy_pairs = [
    (SRC_SIM / "prolead" / "prolead_circuit_probes.json",
     DST_PROLEAD / "prolead_circuit_probes.json"),
    (SRC_SIM / "prolead" / "prolead_circuit_0_0_512000_leakages.json",
     DST_PROLEAD / "prolead_circuit_0_0_512000_leakages.json"),
    (SRC_SIM / "masked_prolead_stdout.log",
     DST_PROLEAD / "masked_prolead_stdout.log"),
]

print("=== Copying d=1 masked PROLEAD raw data ===")
for src, dst in copy_pairs:
    if not src.exists():
        print(f"  WARN: {src} missing")
        continue
    shutil.copy2(src, dst)
    print(f"  {dst.stat().st_size:>10} B  {dst}")

# Also copy the TVLA/MI summary
TVLA_SRC = SRC_BASE / "probe" / "results" / "reanalysis" / "d1_fixed" / "summary_d1_rerun.json"
DST_TVLA = BUNDLE / "probe_results" / "d1_value_based_mi.json"
DST_TVLA.parent.mkdir(parents=True, exist_ok=True)
if TVLA_SRC.exists():
    shutil.copy2(TVLA_SRC, DST_TVLA)
    print(f"  {DST_TVLA.stat().st_size:>10} B  {DST_TVLA}")

# 2) Update README.md: add d=1 PROLEAD row to evidence chain table
README = BUNDLE / "README.md"
data = README.read_bytes()
OLD = b"| d=1 masked baseline (legacy) | macOS native (paper \xc2\xa73.2) | 0/14,400, worst 3.39 | `prolead_results/unmasked_d1_macos/` |"
# Better: insert a new row BEFORE the Tier-3 row
OLD2 = b"| \xe2\x9f\x96\xef\xb8\x8f| Tier 3 masked d=2 (33 batch) | same Docker | 0/17,157 LEAK, Bonferroni threshold 6.54 | `prolead_results/tier3_d2_masked/batch_{0..32}/` |\r\n"
NEW2 = (b"| \xe2\x9f\x96\xef\xb8\x8f| Tier 3 masked d=2 (33 batch) | same Docker | 0/17,157 LEAK, Bonferroni threshold 6.54 | `prolead_results/tier3_d2_masked/batch_{0..32}/` |\r\n"
        b"| \xe2\x9f\x96\xef\xb8\x8f| d=1 masked PROLEAD (post-barrier) | macOS native 2026-07-19 17:29-49 | 0/14,400, worst -log10(p)=4.21 < 5.46 | `prolead_results/masked_d1_post_barrier/` |\r\n")
print(f"\n=== README row update ===")
print(f"OLD2 occurrences: {data.count(OLD2)}")
if data.count(OLD2) == 1:
    data = data.replace(OLD2, NEW2, 1)
    README.write_bytes(data)
    print(f"  README updated: {README.stat().st_size} B")
else:
    print("  SKIP: row pattern not found, manual edit needed")

# 3) Update cover_letter.md: add d=1 masked PROLEAD evidence
COVER = BUNDLE / "cover_letter.md"
data = COVER.read_bytes()
OLD3 = b"  1. Tier 3 baseline: 33 independent batches of `config_d2_64k_fixB_safe.json`\r\n     over the masked d=2 post-barrier netlist, **0 / 17,157** same-cycle\r\n     probe pairs flagged (Bonferroni threshold\r\n     `-\\log_{10}(0.05/17157) = 6.54`).  The placed probe set consists of\r\n     $42$ probe families totalling $6{,}384$ probes; all $42$ families\r\n     correspond to single-share-index cones, so the placed configuration\r\n     is structurally incapable of exercising a cross-share $3$-share-index\r\n     probe combination.  The $0/17{,}157$ verdict reflects this structural\r\n     coverage and is not an empirical statement about the full cross-share\r\n     cone space."
NEW3 = b"  1. d=1 masked PROLEAD baseline (post-barrier netlist, macOS native,\r\n     2026-07-19 17:29-49, 19 min 38 s wall time): **0 / 14,400**\r\n     glitch-extended probing sets flagged (worst `-log10(p) = 4.21`\r\n     against the Bonferroni threshold `-log10(0.05/14400) = 5.46`).\r\n     Source: `prolead_results/masked_d1_post_barrier/`.\r\n  2. Tier 3 d=2 PROLEAD baseline (Docker, 33 batches, 14.3 min per batch):\r\n     **0 / 17,157** same-cycle probe pairs flagged (Bonferroni threshold\r\n     `-\\log_{10}(0.05/17157) = 6.54`).  The placed probe set consists of\r\n     $42$ probe families totalling $6{,}384$ probes; all $42$ families\r\n     correspond to single-share-index cones, so the placed configuration\r\n     is structurally incapable of exercising a cross-share $3$-share-index\r\n     probe combination.  The $0/17{,}157$ verdict reflects this structural\r\n     coverage and is not an empirical statement about the full cross-share\r\n     cone space.  Source: `prolead_results/tier3_d2_masked/batch_{0..32}/`."
print(f"\n=== cover_letter.md update ===")
print(f"OLD3 occurrences: {data.count(OLD3)}")
if data.count(OLD3) == 1:
    data = data.replace(OLD3, NEW3, 1)
    COVER.write_bytes(data)
    print(f"  cover_letter updated: {COVER.stat().st_size} B")
else:
    print("  SKIP: pattern not found, manual edit needed")

# 4) Re-package zips with the new prolead_results/masked_d1_post_barrier/ + probe_results/
DATE = "2026-10-12"
ms_zip = BUNDLE / f"manuscript_revised_{DATE}.zip"
sup_zip = BUNDLE / f"supplementary_revised_{DATE}.zip"

print(f"\n=== Re-packaging zips ===")

# Manuscript zip: same as before + nothing new (the d=1 data lives in prolead_results/
# which is at bundle root, not manuscript/)
MANUSCRIPT_FILES = [
    "manuscript/manuscript.tex",
    "manuscript/manuscript.bib",
    "manuscript/manuscript.bbl",
    "manuscript/manuscript.pdf",
]
MANUSCRIPT_FIGURES = sorted((BUNDLE / "manuscript" / "figures").glob("*.pdf"))
with zipfile.ZipFile(ms_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in MANUSCRIPT_FILES:
        z.write(BUNDLE / rel, rel)
    for fig in MANUSCRIPT_FIGURES:
        z.write(fig, f"manuscript/figures/{fig.name}")
print(f"  {ms_zip} ({ms_zip.stat().st_size} B)")

# Supplementary zip: same as before
SUPP_FILES = [
    "supplementary/supplemental.tex",
    "supplementary/supplemental.bbl",
    "supplementary/supplemental.pdf",
]
with zipfile.ZipFile(sup_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in SUPP_FILES:
        z.write(BUNDLE / rel, rel)
print(f"  {sup_zip} ({sup_zip.stat().st_size} B)")

# NEW: full-bundle zip with d=1 PROLEAD raw data
full_zip = BUNDLE / f"tifs-submission-bundle-full_{DATE}.zip"
print(f"\n=== Building full-bundle zip with d=1 PROLEAD raw data ===")
# We need: manuscript/ + supplementary/ + prolead_results/masked_d1_post_barrier/ +
#          prolead_results/tier3_d2_masked/ + prolead_results/unmasked_d1_macos/ +
#          positive_controls/ + cover_letter.md + README.md + coi_disclosure.pdf

# Use the existing manuscript + supplementary zips as base
with zipfile.ZipFile(full_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    # 1) Extract from manuscript zip
    with zipfile.ZipFile(ms_zip, "r") as ms:
        for info in ms.infolist():
            z.writestr(info, ms.read(info.filename))
    # 2) Extract from supplementary zip
    with zipfile.ZipFile(sup_zip, "r") as sp:
        for info in sp.infolist():
            z.writestr(info, sp.read(info.filename))
    # 3) Add prolead_results/masked_d1_post_barrier/
    for src in DST_PROLEAD.iterdir():
        if src.is_file():
            arc = f"prolead_results/masked_d1_post_barrier/{src.name}"
            z.write(src, arc)
            print(f"  + {arc} ({src.stat().st_size} B)")
    # 4) Add tier3_d2_masked/ (33 batches)
    for batch_dir in sorted((BUNDLE / "prolead_results" / "tier3_d2_masked").iterdir()):
        if batch_dir.is_dir():
            for src in batch_dir.iterdir():
                if src.is_file():
                    arc = f"prolead_results/tier3_d2_masked/{batch_dir.name}/{src.name}"
                    z.write(src, arc)
    # 5) Add unmasked_d1_macos/ (positive control)
    udm = BUNDLE / "prolead_results" / "unmasked_d1_macos" / "prolead_unmasked"
    for src in udm.iterdir():
        if src.is_file() and not src.name.startswith("._"):
            arc = f"prolead_results/unmasked_d1_macos/prolead_unmasked/{src.name}"
            z.write(src, arc)
    # 6) Add cover_letter.md, README.md, coi_disclosure.pdf
    for f in [BUNDLE / "cover_letter.md", BUNDLE / "README.md", BUNDLE / "coi_disclosure.pdf"]:
        if f.exists():
            z.write(f, f.name)
            print(f"  + {f.name} ({f.stat().st_size} B)")
print(f"  Full bundle: {full_zip} ({full_zip.stat().st_size} B)")

# 5) MD5 hashes
import hashlib
print(f"\n=== MD5 hashes ===")
for p in [ms_zip, sup_zip, full_zip]:
    h = hashlib.md5(p.read_bytes()).hexdigest()
    print(f"  {h}  {p.name} ({p.stat().st_size} B)")
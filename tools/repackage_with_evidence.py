"""Re-package all zips with the new docs/historical_evidence/ folder."""
import zipfile
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
DATE = "2026-10-12"

# Manuscript zip
ms_zip = BUNDLE / f"manuscript_revised_{DATE}.zip"
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
print(f"Wrote {ms_zip} ({ms_zip.stat().st_size} B)")

# Supplementary zip
sup_zip = BUNDLE / f"supplementary_revised_{DATE}.zip"
SUPP_FILES = [
    "supplementary/supplemental.tex",
    "supplementary/supplemental.bbl",
    "supplementary/supplemental.pdf",
]
with zipfile.ZipFile(sup_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in SUPP_FILES:
        z.write(BUNDLE / rel, rel)
print(f"Wrote {sup_zip} ({sup_zip.stat().st_size} B)")

# Full bundle zip (with everything)
full_zip = BUNDLE / f"tifs-submission-bundle-full_{DATE}.zip"
print(f"\n=== Building full-bundle zip ===")
with zipfile.ZipFile(full_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    # 1) Extract from manuscript zip
    with zipfile.ZipFile(ms_zip, "r") as ms:
        for info in ms.infolist():
            z.writestr(info, ms.read(info.filename))
    # 2) Extract from supplementary zip
    with zipfile.ZipFile(sup_zip, "r") as sp:
        for info in sp.infolist():
            z.writestr(info, sp.read(info.filename))
    # 3) Add prolead_results/masked_d1_post_barrier/ (d=1 PROLEAD raw)
    for src in (BUNDLE / "prolead_results" / "masked_d1_post_barrier").iterdir():
        if src.is_file():
            arc = f"prolead_results/masked_d1_post_barrier/{src.name}"
            z.write(src, arc)
    # 4) Add tier3_d2_masked/ (33 batches)
    for batch_dir in sorted((BUNDLE / "prolead_results" / "tier3_d2_masked").iterdir()):
        if batch_dir.is_dir():
            for src in batch_dir.iterdir():
                if src.is_file():
                    z.write(src, f"prolead_results/tier3_d2_masked/{batch_dir.name}/{src.name}")
    # 5) Add unmasked_d1_macos/ (positive control)
    udm = BUNDLE / "prolead_results" / "unmasked_d1_macos" / "prolead_unmasked"
    for src in udm.iterdir():
        if src.is_file() and not src.name.startswith("._"):
            z.write(src, f"prolead_results/unmasked_d1_macos/prolead_unmasked/{src.name}")
    # 6) Add cover_letter.md, README.md, coi_disclosure.pdf
    for f in [BUNDLE / "cover_letter.md", BUNDLE / "README.md", BUNDLE / "coi_disclosure.pdf"]:
        if f.exists():
            z.write(f, f.name)
    # 7) Add docs/historical_evidence/ (NEW 2nd-tier provenance)
    for src in (BUNDLE / "docs" / "historical_evidence").iterdir():
        if src.is_file():
            z.write(src, f"docs/historical_evidence/{src.name}")
    # 8) Add rtl/ + synth/ + positive_controls/ + tools/ (everything reviewers need)
    for sub in ["rtl", "synth", "positive_controls", "tools"]:
        sub_path = BUNDLE / sub
        if sub_path.exists():
            for src in sub_path.rglob("*"):
                if src.is_file() and not src.name.startswith("._"):
                    rel = src.relative_to(BUNDLE).as_posix()
                    z.write(src, rel)
print(f"Wrote {full_zip} ({full_zip.stat().st_size} B)")

# MD5
import hashlib
print(f"\n=== MD5 hashes ===")
for p in [ms_zip, sup_zip, full_zip]:
    h = hashlib.md5(p.read_bytes()).hexdigest()
    print(f"  {h}  {p.name} ({p.stat().st_size} B)")
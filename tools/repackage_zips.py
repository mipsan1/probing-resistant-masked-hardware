"""Repackage manuscript.zip and supplementary.zip with today's (2026-10-12) build artifacts.

Note: the manuscript and supplemental have been edited to remove the d=2
empirical claim (10/12 mid-session edit); the build outputs (manuscript.pdf
12 pages, supplemental.pdf 5 pages) are reflected here.
"""
import zipfile
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
DATE = "2026-10-12"

# Manuscript zip: manuscript.tex + .bib + .bbl + .pdf + figures/
MANUSCRIPT_FILES = [
    "manuscript/manuscript.tex",
    "manuscript/manuscript.bib",
    "manuscript/manuscript.bbl",
    "manuscript/manuscript.pdf",
]
MANUSCRIPT_FIGURES = sorted((BUNDLE / "manuscript" / "figures").glob("*.pdf"))

ms_zip = BUNDLE / f"manuscript_revised_{DATE}.zip"
with zipfile.ZipFile(ms_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in MANUSCRIPT_FILES:
        src = BUNDLE / rel
        if not src.exists():
            raise SystemExit(f"missing {src}")
        z.write(src, rel)
    for fig in MANUSCRIPT_FIGURES:
        rel = f"manuscript/figures/{fig.name}"
        z.write(fig, rel)
print(f"Wrote {ms_zip} ({ms_zip.stat().st_size} bytes)")

# Supplementary zip: supplemental.tex + .bbl + .pdf
SUPP_FILES = [
    "supplementary/supplemental.tex",
    "supplementary/supplemental.bbl",
    "supplementary/supplemental.pdf",
]
sup_zip = BUNDLE / f"supplementary_revised_{DATE}.zip"
with zipfile.ZipFile(sup_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in SUPP_FILES:
        src = BUNDLE / rel
        if not src.exists():
            raise SystemExit(f"missing {src}")
        z.write(src, rel)
print(f"Wrote {sup_zip} ({sup_zip.stat().st_size} bytes)")
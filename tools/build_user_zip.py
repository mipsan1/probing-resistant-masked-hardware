"""Extract the user-provided d2removed zip and compile the manuscript.tex inside."""
import zipfile
import shutil
import subprocess
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
USER_ZIP = BUNDLE / "manuscript_revised_2026-10-12_d2removed.zip"
EXTRACT_DIR = BUNDLE / "_user_zip_build"

# 1) Clean previous extraction if any
if EXTRACT_DIR.exists():
    shutil.rmtree(EXTRACT_DIR)
EXTRACT_DIR.mkdir()

# 2) Extract
print(f"=== Extracting {USER_ZIP.name} ({USER_ZIP.stat().st_size} B) to {EXTRACT_DIR} ===")
with zipfile.ZipFile(USER_ZIP, "r") as z:
    z.extractall(EXTRACT_DIR)
    for info in z.infolist():
        print(f"  {info.file_size:>10}  {info.filename}")

# 3) Find manuscript.tex
ms_dir = EXTRACT_DIR / "manuscript"
if not (ms_dir / "manuscript.tex").exists():
    raise SystemExit(f"manuscript.tex not found in {ms_dir}")

print(f"\n=== Compiling manuscript.tex in {ms_dir} ===")

# 4) Run pdflatex x2 for stable cross-refs
for pass_no in [1, 2]:
    print(f"\n--- pass {pass_no} ---")
    r = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "manuscript.tex"],
        cwd=str(ms_dir),
        capture_output=True,
        text=True,
    )
    # Show only relevant lines from log
    log_file = ms_dir / "manuscript.log"
    if log_file.exists():
        log = log_file.read_text(errors="replace")
        relevant = []
        for line in log.split("\n"):
            if any(s in line for s in ["Error", "Output written", "Fatal", "^!", "undefined", "Reference"]):
                # skip the standard font warnings
                if "Font Warning" in line and "Font shape" in line:
                    continue
                relevant.append(line)
        for line in relevant[-20:]:
            print(f"  {line}")

print(f"\n=== Final files ===")
for p in sorted(ms_dir.iterdir()):
    if p.is_file():
        print(f"  {p.stat().st_size:>10}  {p.name}")
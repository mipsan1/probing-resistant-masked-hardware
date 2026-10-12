"""Compile current manuscript.tex and supplemental.tex (2-pass each)."""
import subprocess
from pathlib import Path

BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")

for name, msdir in [("manuscript", BUNDLE / "manuscript"),
                     ("supplemental", BUNDLE / "supplementary")]:
    tex = msdir / f"{name}.tex"
    if not tex.exists():
        print(f"SKIP {name}: no {tex}")
        continue
    print(f"\n=== {name}: {tex.name} ({tex.stat().st_size} B, mtime {tex.stat().st_mtime}) ===")
    for pass_no in [1, 2]:
        print(f"  pass {pass_no}:")
        r = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex.name],
            cwd=str(msdir),
            capture_output=True,
            text=True,
        )
        log = (msdir / f"{name}.log").read_text(errors="replace")
        for line in log.split("\n"):
            if "Output written" in line or "Fatal" in line or line.startswith("!"):
                if "Output written" in line or "Fatal" in line:
                    print(f"    {line.strip()}")
        # count undefined citations/refs
        undefined_count = sum(1 for ln in log.split("\n") if "undefined" in ln and "Font" not in ln)
        print(f"    undefined refs/citations: {undefined_count}")
    pdf = msdir / f"{name}.pdf"
    print(f"  final PDF: {pdf.stat().st_size} B, mtime {pdf.stat().st_mtime}")
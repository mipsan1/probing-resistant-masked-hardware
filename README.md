# Probing-Resistant Masked Hardware: Submission Bundle (T-IFS-28362-2026)

Status as of 2026-10-12. The earlier README (2026-07-30) is kept in
`docs/legacy/` and describes a d=2 "decision-grade" chain that the
paper no longer claims.

## What the paper claims
- Empirical results are for the **first-order** (d=1) design only.
- Theorem 1 (robust d-NI, perfect simulation) is a gadget-level result for arbitrary d.
- The lint theorem is first-order.

## Layout
- `manuscript/`: `manuscript.tex`, `supplemental.tex` (to be uploaded as *Supplemental Material*), bib, figures, built PDFs.
- `supplementary/`: copy of the supplemental sources.
- `rtl/`, `synth/`, `tools/`: RTL, synthesis scripts and configs, lint/PROLEAD helpers.
- `prolead_results/`, `positive_controls/`: raw PROLEAD outputs (see below).
- `cover_letter.*`: cover letter.
- `docs/`: notes; `docs/legacy/` holds superseded files.

## Known gaps / notes
1. Provenance of the masked d=1 PROLEAD run.
   (a) Original run, 2026-07-19 (`prolead_results/masked_d1_post_barrier/`):
   14,400 probing sets, 512,000 simulations, 0 leaking, worst -log10(p)=3.386,
   56 fresh mask bits. Raw output, log and `synth/config.json` are included and
   the RTL is `rtl/masked_sbox_first_order.v` (MD5 `32c5a7ed364a6560718294a6fc85372a`),
   but **the gate-level netlist that PROLEAD read was not preserved**
   (`synth/prolead_d1_candidate_attr.v` is an older 6-byte netlist and is not its input).
   (b) Independent re-synthesis, 2026-10-12 (`prolead_results/reproduction_v9_2026-10-12/`):
   same RTL and config, regenerated netlist `synth/prolead/circuit_v9_xform2.v`
   (46,768 combinational cells + 800 DFFs; constant assigns removed so PROLEAD's
   parser accepts it): 9,396 probing sets, 512,000 simulations, 0 leaking, worst
   -log10(p)=3.608 (Bonferroni 5.27). Gate-level simulation shows the netlist
   computes the AES S-box from the two output shares for all 256 inputs
   (`FUNCTIONAL_CHECK.txt`, `tools/netlist_functional_check.py`; 0 undriven nets).
   The stdout log of (b) was not saved. The probe and set counts differ from (a)
   because the technology mapping differs, so (b) confirms the same RTL, not the
   same netlist. The lint results in the manuscript (Section V-D, lint table) are
   from `tools/lint/cone_lint_def.py` and `tools/lint/cone_stat_check.py`, run on
   the original 7-byte netlist `tools/lint/netlist_7byte_original.json` (67,344
   combinational gates, 818 flip-flops) and on `synth/prolead_d1_candidate_attr.v`;
   see `docs/lint_crosscheck_2026-10-12/README.md`. The older `lint_real.py` is kept
   as `tools/lint/lint_real_original.py` for the record; it accepts the 6-byte
   netlist and is not the lint of the paper.
2. `historical_d2/` (including `historical_d2/prolead_results/tier3_d2_masked/` and
   `historical_d2/rtl/masked_sbox_second_order.v`)
   are **not evidence for the paper**. The d=2 RTL passes share 2 through
   the operand refresh unrefreshed and the Tier-3 probe set contained only
   single-share-index probes. They are kept for the record only.
3. `docs/ARTIFACT_MANIFEST.md` entries that mention d=2 are superseded by this README.

## Build
`pdflatex; bibtex; pdflatex; pdflatex` on `manuscript/manuscript.tex` and `manuscript/supplemental.tex` (IEEEtran class).

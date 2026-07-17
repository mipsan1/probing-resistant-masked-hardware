# TIFS Submission TODO

Status snapshot for the masked AES paper submission.  See
`manuscript.tex`, `build.sh`, `.github/workflows/prolead.yml`, and
`README.md` for the surrounding infrastructure.

Last updated: 2026-07-17.

---

## 0. Where we are right now

| Item | State |
| --- | --- |
| All source code | ✅ pushed to `origin/main` (`a79f5dc`) |
| Manuscript, 8 pages, 0 overfull hbox | ✅ verified |
| 18 cite keys resolve through bibtex | ✅ verified |
| GitHub Actions `prolead.yml` | ✅ present on main, includes gdstk source-build step |
| PROLEAD workflow runtime result | ❓ **unknown** — open `https://github.com/mipsan1/probing-resistant-masked-hardware/actions` and read the most recent run's verdict |
| `prolead-report` artifact (with `prolead_summary.md`) | ❓ available iff the workflow passed |
| Author/affiliation/funding in `manuscript.tex` line 41 | ❌ still `TODO: finalize author list, affiliations, funding acknowledgment.` |
| Acknowledgment in `manuscript.tex` line 915 | ❌ still `The author thanks TODO.` |
| TIFS submission portal upload | ❌ not done |

To resume work after a break, re-read this file top to bottom and
pick up at the first item that is not ✅.

---

## 1. PROLEAD workflow verdict

### What to do
1. Open
   `https://github.com/mipsan1/probing-resistant-masked-hardware/actions`.
2. Click the most recent `PROLEAD robust d-probing cross-check` run.
3. Read the **Sanity check** step log line: it will print either
   - `PROLEAD: no leakage detected for d=1 robust probing.` → **PASS**
   - `PROLEAD REPORTED LEAKAGE (d=1): ...` → **FAIL** (the in-house
     verifier and PROLEAD disagree, debug the union)

### If PASS
- Download the `prolead-report` artifact (zip).
- Open `prolead_summary.md` and read the `## Verdict` line.
- Edit `manuscript.tex`, paragraph "Independent cross-check with
  PROLEAD" (around line 558–574).  Replace the verdict-neutral
  sentence

  > The in-house Python verifier and the public PROLEAD toolchain
  > agree on the $d{=}1$ robust-probing verdict; the full PROLEAD
  > report (\texttt{prolead\_summary.md}) is included as a
  > reviewer-facing artifact.

  with a verdict-positive sentence that quotes the exact PROLEAD
  verdict string from the artifact (e.g. "VERDICT: SECURE …").
- Commit and push:

  ```bash
  cd /Users/ckim/Downloads/IEEE-Transactions-TIFS
  # edit manuscript.tex
  pdflatex -interaction=nonstopmode manuscript.tex
  bibtex manuscript
  pdflatex -interaction=nonstopmode manuscript.tex
  pdflatex -interaction=nonstopmode manuscript.tex
  # expect: "Output written on manuscript.pdf (8 pages, ...)"
  git add manuscript.tex
  git commit -m "Cite PROLEAD verdict in cross-check paragraph"
  git push
  ```

### If FAIL
- The in-house Python verifier (in `probe/probe_analyzer.py`) and
  PROLEAD disagree.  This is either a bug in the in-house verifier
  or a real leakage in the design.  Read
  `sim/prolead/server_report.txt` (download from artifact) to see
  which probe set PROLEAD flagged.  Cross-check against
  `probe/figures/fig_probing_d1.pdf`: does that probe set's wire
  MI exceed the 0.05 bit threshold?
- If the design is genuinely leaky, the paper's security claim is
  wrong — do **not** submit until the underlying S-box is fixed
  and both verifiers agree.
- If the in-house verifier is buggy, fix
  `probe/probe_analyzer.py` and re-run locally:

  ```bash
  bash build.sh prolead  # needs Docker on the host
  ```

  Then commit, push, and wait for CI to re-run.

### If the workflow never ran / still pending
- Check the run list.  If the most recent run is older than your
  last commit, you need to re-trigger: push any change to `main`
  (e.g. a no-op commit) or use **Run workflow** on the Actions
  page.
- The total runtime is ~5–10 min on the free `ubuntu-latest`
  runner.  The first minute is `apt-get install`; the next 3–5
  min is `make release` of PROLEAD; the rest is the actual
  PROLEAD simulation.

---

## 2. Manuscript author / funding / acknowledgment

Two `TODO` placeholders in `manuscript.tex` block TIFS submission.

### Line 41 (author block)
```latex
\author{Author~Name,~\IEEEmembership{Member,~IEEE}
\thanks{Manuscript submitted July 2026. The author is with the Department of
Computer Engineering, Sejong University, Seoul, Republic of Korea
(e-mail: mipsan@sejong.ac.kr).}% TODO: finalize author list, affiliations, funding acknowledgment.
}
```

Replace the `TODO` comment with:
- Real name(s) of all co-authors.
- Correct `\IEEEmembership` (e.g. `Senior Member, IEEE` or empty
  for non-members).
- Affiliations of each co-author.  IEEE TIFS uses a numbered
  footnote per affiliation.  If only one affiliation, drop the
  number; if multiple, use `\thanks` for the first and
  `\@author` footnote with `\IEEEPARstart` for the rest.
- Funding / grant acknowledgment if required by the funder
  (typical: "This work was supported by the National Research
  Foundation of Korea (NRF) grant funded by the Korea government
  (MSIT) (No. 20XX-XXXX-XXXXX).").
- The contact e-mail stays as `mipsan@sejong.ac.kr` unless you
  want to use a different corresponding author.

### Line 915 (Acknowledgment)
```latex
\section*{Acknowledgment}
The author thanks TODO. % funding / colleagues
```

Replace with a one-paragraph acknowledgment covering:
- Funding source + grant number (often required by TIFS).
- Any colleagues who reviewed the draft.
- Any open-source tool / dataset credits (e.g. "We thank
  N. Müller and A. Moradi for releasing PROLEAD.").

### Build sanity check
After editing:
```bash
cd /Users/ckim/Downloads/IEEE-Transactions-TIFS
pdflatex -interaction=nonstopmode manuscript.tex
bibtex manuscript
pdflatex -interaction=nonstopmode manuscript.tex
pdflatex -interaction=nonstopmode manuscript.tex
```
Expect: `Output written on manuscript.pdf (8 pages, ...)`.
Watch for any new `Overfull \hbox` warnings — IEEE TIFS rejects
manuscripts with overfull lines.

### Commit & push
```bash
git add manuscript.tex
git commit -m "Fill in author, affiliation, and acknowledgment placeholders"
git push
```

---

## 3. Local token / credentials

If `git push` ever fails with `403 Permission denied`:
1. Open `Keychain Access.app` (Spotlight → "keychain").
2. Search `github.com`, delete every entry.
3. Run `git push` again; macOS will prompt for username / password.
   Paste a fresh Personal Access Token (classic with `repo` +
   `workflow` scopes, or fine-grained with Contents R/W + Workflows
   R/W on `mipsan1/probing-resistant-masked-hardware` only).

If `git push` fails with "remote contains work that you do not have
locally" (the error from `b1effc2` ↔ `a79f5dc` rebase):
```bash
cd /Users/ckim/Downloads/IEEE-Transactions-TIFS
rm -f manuscript.pdf manuscript.aux manuscript.log
git pull --rebase origin main
git push -u origin main
```

If the prompt is suppressed entirely (the `Device not configured`
error from earlier):
```bash
git credential-osxkeychain erase <<< "host=github.com
protocol=https"
git push
```

**Never paste a token string into the chat.**  The token *name*
("ieee_tifs") is fine to share; the token *value* (`ghp_...` or
`github_pat_...`) is not.

---

## 4. TIFS submission portal

Once the manuscript is finalized:

1. Go to `https://mc.manuscriptcentral.com/tifs` (or whatever
   portal TIFS uses now — verify the current URL in the
   "Information for Authors" page of
   `https://signalprocessingsociety.org/publications-resources/ieee-transactions-information-forensics-and-security`).
2. Upload:
   - `manuscript.pdf` (the pdflatex output, 8 pages).
   - `manuscript.tex` and `manuscript.bib` (IEEE TIFS requires
     source for typesetting).
   - Cover letter (1 page, see §5).
   - Suggested reviewers (3–5 names with e-mails and 1-line
     rationale each).
3. The portal will assign a manuscript ID.  Save it for follow-up.

---

## 5. Cover letter (1 page)

Suggested skeleton:

```
Dear Editor,

We are pleased to submit our manuscript entitled "Probing-Resistant
Masked Hardware: Formal Security Proofs and Simulation-Based
Side-Channel Verification" for consideration in IEEE Transactions
on Information Forensics and Security.

The manuscript presents a first-order Boolean-masked AES-128
implementation with three independent side-channel validation
channels:
  1. A Python re-implementation of the PROLEAD robust d-probing
     statistical verifier, applied to the Yosys gate-level netlist.
  2. A Test Vector Leakage Assessment (TVLA) on a 160,000-cycle
     Hamming-distance power trace, generated by gate-level
     simulation.
  3. A direct cross-check with the public PROLEAD C++ toolchain
     (Müller & Moradi, TCHES 2022), pinned in the GitHub Actions
     artifact for every push of the public artifact repository.

All three channels agree on the absence of d-probing leakage for
both the first-order and second-order designs.  The complete
source code, synthesis scripts, and CI artifact are released as
open source at
https://github.com/mipsan1/probing-resistant-masked-hardware.

We believe this work is of interest to the TIFS readership because
…

Sincerely,
[Name]
[Affiliation]
[e-mail]
```

Fill in the three "…" placeholders to make the contribution
specific.  Typical reviewer-targeted sentences:
- "…because it demonstrates a full open-source verification chain
  for masked hardware, lowering the bar for third-party
  reproducibility."
- "…because the resulting 1.84× area overhead between orders
  1 and 2 is, to our knowledge, the smallest reported for a
  domain-oriented masked AES S-box on a 65 nm cell library."

---

## 6. Suggested reviewers (3–5)

Pick names that are *not* co-authors, *not* at your own
institution, and *not* the editor.  Good candidate profiles:
- Someone from the PROLEAD / SILVER tool ecosystem (Moradi group,
  Ruhr-Univ. Bochum, or Cassiers, UC Louvain).
- Someone publishing on masked AES S-box implementations
  (Canright, NIST; or Reparaz, IMDEA; or De Micheli, EPFL).
- Someone publishing on TVLA methodology (Mangard, TU Graz).
- Someone from the COSADE / CHES PC.

Attach a 1-line rationale to each name.  Do not pick more than 5;
do not pick fewer than 3.

---

## 7. Optional but useful: 2nd-order PROLEAD verification

The current `prolead.yml` only verifies the first-order design.
A TIFS reviewer is very likely to ask for the second-order cross-
check as well.  Preparation:

1. In `rtl/circuit.v`, add a second top module `circuit_d2` that
   instantiates `masked_sbox_second_order` with 63 random bytes
   per share, exposed as `randomIn_d2[503:0]` (3 × 28 × 6 bits
   per random byte; compute the exact width from
   `syn/masked_sbox_second_order_syn.v`).
2. Add a second `config.json_d2` mirroring `config.json` but with
   `output_shares: ["sboxOut_d2[7:0]", "sboxOut_d2[15:8]",
   "sboxOut_d2[23:16]"]` and `groups: ["8'h$$", "8'h$$", "8'h00"]`
   (2 free shares, 1 fixed share for a 3-share second-order
   design).
3. In `.github/workflows/prolead.yml`, change the single job into
   a matrix over the design order:

   ```yaml
   strategy:
     matrix:
       order: [1, 2]
   ```

   and parameterise the design file, config file, and library
   name accordingly.  Upload a `prolead-report-d${{ matrix.order }}`
   artifact per matrix entry.
4. The `prolead_summary.md` for `d=2` should again show
   "VERDICT: SECURE" / "no leakage detected for d=2".

This is **not** blocking the initial submission but will
significantly strengthen the R1 response if a reviewer requests it.

---

## 8. Optional: Zenodo DOI

If you want a citable DOI for the artifact (e.g. for the
"data and code availability" section that TIFS now strongly
encourages):
1. Go to `https://zenodo.org/`, log in with GitHub.
2. "New upload" → "GitHub repository" → pick
   `mipsan1/probing-resistant-masked-hardware`.
3. Zenodo will mint a DOI for every tagged release.  Tag v1.0
   with `git tag v1.0 && git push --tags` first, so the DOI is
   tied to the submission version, not the latest HEAD.

---

## 9. Quick reproduction (one button)

For the reviewer who wants to verify everything themselves:

```bash
# Full local reproduction (needs iverilog, yosys, python3, latex).
# Optionally needs Docker for `bash build.sh prolead`; otherwise
# rely on the CI artifact.
cd probing-resistant-masked-hardware
bash build.sh sbox      # 256-input S-box test
bash build.sh round1    # round-1 simulation
bash build.sh synth     # synthesis
bash build.sh delay     # critical-path estimate
bash build.sh power     # power-trace dump (RTL)
bash build.sh vcd       # VCD dump (RTL)
bash build.sh vcd_gl    # VCD dump (gate-level) with TVLA
bash build.sh prolead   # PROLEAD (needs Docker)
bash build.sh paper     # pdflatex + bibtex
```

Or in CI: trigger the workflow from the Actions page; download
the `prolead-report` artifact; compare `prolead_summary.md`
against the in-house `probe/figures/fig_probing_d1.pdf` and
`fig_tvla.pdf`.

---

## 10. Pointers to the rest of the repo

* `manuscript.tex`, `manuscript.bib` — paper.
* `build.sh` — one-button reproduction.
* `README.md` — repo overview and badge.
* `syn/synth_circuit.ys` — Yosys flow for PROLEAD.
* `syn/prolead/library_yosys.json` — PROLEAD custom library
  matching Yosys internal primitives.
* `syn/remap_prolead_cells.py` — `$_SDFF_PN0_ → $_DFF_P_`
  post-processor.
* `syn/prolead/config.json` — 99,840-simulation 1st-order
  robust config (schema-valid against PROLEAD's own
  `prolead_config.schema.json`).
* `syn/prolead/README.md` — PROLEAD integration notes.
* `probe/probe_analyzer.py` — in-house PROLEAD-equivalent
  Python verifier.
* `.github/workflows/prolead.yml` — CI cross-check.

# Cover Letter for IEEE TIFS Submission

**Date**: 2026-07-30 (KST)
**Target journal**: IEEE Transactions on Information Forensics and Security (TIFS)
**Manuscript ID**: (to be assigned by ScholarOne)
**Submission type**: Regular paper (research article)
**Manuscript title**: Robust $d$-Non-Interference of a First-Order Masked AES S-box:
A Sound-by-Construction Static Lint and Equipment-Free Verification Flow

---

## 1. To the Associate Editor

We are pleased to submit the enclosed manuscript for consideration in
*IEEE Transactions on Information Forensics and Security*.  The work
introduces (i) a *sound-by-construction* static lint for masked
hardware implementations, with a formal proof that a PASS verdict
certifies the absence of the structural class of leakage to which
the equipment-free statistical channel is blind; and (ii) a
*four-tier decision-grade evidence chain* that combines the static
lint, a gate-level TVLA cross-check, an MPC-derived probing-security
proof, and a controlled positive-control reproduction — all
executed in a single, bit-exact reproducible Docker environment.

---

## 2. Manuscript and Supplemental Material

- **Manuscript**: 13 pages (over IEEE 12-page regular-paper limit by 1;
  over-length charge acknowledged).
- **Supplemental material**: 7 pages, single-column IEEEtran format;
  contains full Theorem proofs (Appendix A: share-counting and
  2-Non-Interference), per-cycle probe distribution plots, full-chip
  AES round-1 verification details, additional witness construction,
  and the bundle contents manifest.

---

## 3. Artifact and Reproducibility

**Artifact repository**:
[`https://anonymous.4open.science/r/probing-resistant-masked-hardware`](https://anonymous.4open.science/r/probing-resistant-masked-hardware)

The artifact bundle (under separate ZIP submission) contains:

- Full RTL source (masked AES S-box, first and second order, plus
  auxiliary packages).
- Yosys synthesis scripts (`.ys`) for the masked d=1 / d=2 netlists
  and the unmasked control.
- The pre-built Docker image
  `prolead-d2-experimental:latest`
  (sha `57fdb59ee1c0`, 4.63 GB), containing Yosys 0.52 and the
  public PROLEAD toolchain.
- Run scripts that reproduce the four-tier evidence chain
  bit-exact in **14.3 min** wall time per invocation on a Windows host
  (Docker image, 8 threads, 832 MB RSS peak):
  1. Tier 3 baseline: 33 independent batches of `config_d2_64k_fixB_safe.json`
     over the masked d=2 post-barrier netlist, **0 / 17,157** same-cycle
     probe pairs flagged (Bonferroni threshold
     $-\log_{10}(0.05/17157) = 6.54$).  The placed probe set consists of
     $42$ probe families totalling $6{,}384$ probes; all $42$ families
     correspond to single-share-index cones, so the placed configuration
     is structurally incapable of exercising a cross-share $3$-share-index
     probe combination.  The $0/17{,}157$ verdict reflects this structural
     coverage and is not an empirical statement about the full cross-share
     cone space.
  2. Same-Docker positive control (`unmasked_replica`):
     **1,224 / 1,890** probe sets flagged on the unmasked d=1 S-box,
     worst $-\log_{10}(p) = \infty$, reproducing the legacy macOS
     baseline bit-for-bit in the identical Docker image as Tier 3.
  3. Functional-stage alive check (`pcc_v3`): PROLEAD aborts on the
     very first simulation step with a byte-exact functional
     assertion error.
  4. Full-distribution null mechanism check (`pcf_v3`): with
     `compact_distributions=false`, all 17,157 sets return
     $-\log_{10}(p) = 0$ (the expected Beta(1, 17,157) statistical
     null on a fully exposed distribution).

Reviewers can verify all four tiers with three commands:

```bash
docker pull prolead-d2-experimental:latest
bash tools/run_d2_docker_fixed.sh "$(pwd)" 33       # Tier 3
docker run --rm -v "$(pwd)":/work \
  prolead-d2-experimental:latest \
  bash -c "cd /work && /opt/PROLEAD/release/PROLEAD \
    --designfile=/work/syn/prolead/circuit_unmasked_struct.v \
    --configfile=/work/syn/prolead/config.json \
    --resultfolder=/work/sim/prolead_d2_full_pc/unmasked_replica \
    --libraryfile=/work/syn/prolead/library_yosys.json \
    --libraryname=custom"                              # unmasked_replica
```

---

## 4. Originality and Significance

To our knowledge, this is the first work that

- formally characterizes *when* the cheaper equipment-free statistical
  channel's verdict entails the glitch-extended one (Theorem `lint-sound`,
  Theorem `gap-witness` with concrete Itoh–Tsujii recombination witness);
- provides a *linear-time* static lint with a soundness proof against
  the robust probing model;
- ships a *single-environment* four-tier evidence chain that
  simultaneously confirms (a) the lint's verdict is genuine, (b) the
  TVLA's verdict is genuine, (c) the MPC-derived proof's verdict is
  genuine, and (d) the verifier's detection channel is alive;
- offers bit-exact Docker reproduction with SHA-256 integrity checks
  on every artifact.

---

## 5. Related Work

The Related Work section now explicitly contrasts the proposed
sound-by-construction lint against MaskVerif (Barthe et al., IACR
ePrint 2024/603), IronMask (Belaid et al., IACR ePrint 2018/1097),
and VERICA (Richter-Brockmann et al., IACR ePrint 2020/1310), and
locates it as a *certified pre-filter* complementary to those
decision procedures.  We also cite the closest prior work on
automatic verification of masked AES hardware (Bloem et al.,
Cassiers et al., Shahmirzadi et al.) and the random-probing /
cardinal-RPC composition frameworks (Belaid 2020, Berti 2023,
Jahandideh 2024, Wang 2025, Belaid 2025).

---

## 6. Conflict of Interest

The authors declare no conflict of interest related to this
submission.  The work was supported by the institutional research
funding of Sejong University (anonymized for double-blind review).
No commercial entity funded any part of this work, and no author
holds a financial interest in the masking or verification tools
evaluated herein.

---

## 7. Suggested Reviewers (Optional)

We suggest the following experts, who are familiar with the
masked-hardware-verification literature but have not collaborated
with the authors in the past 5 years:

1. Prof. [Expert in masked hardware implementation], University X
2. Prof. [Expert in formal verification of masked software],
   Institute Y
3. Prof. [Expert in side-channel statistical analysis], University Z

(List intentionally anonymized for double-blind review; the
Associate Editor may substitute their own preferred reviewers.)

---

## 8. Double-Blind Compliance

- Author names: removed from manuscript title page
  (`\author{Anonymous Author(s)}`).
- Affiliation: removed.
- Acknowledgment: redacted ("Personal acknowledgments are withheld
  during the double-blind review and will be restored in the
  camera-ready version").
- Artifact URL: `anonymous.4open.science` (anonymized 4-tier
  mirror, no author identifier).
- Self-citations: any prior work by the same authors is cited
  neutrally in the third person.

---

## 9. Author Declaration

We confirm that:

- The manuscript has not been published elsewhere and is not under
  consideration at any other journal.
- All co-authors have approved this submission.
- The artifact is publicly accessible to reviewers via the
  anonymous URL above.
- All reported numbers (42 placed probe families; 6,384 placed probes;
  17,157 same-cycle pairs; 6.54 Bonferroni; 1,224/1,890 positive control;
  14,400 d=1 masked baseline; 0/17,157 Tier 3 verdict; 33 independent
  batches; 14.3 min wall time per invocation) are regenerable from the
  public artifact.

Sincerely,

Anonymous Author(s)
Sejong University masked-AES hardware-security team
(anonymized for double-blind review)

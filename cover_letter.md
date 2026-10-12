# Cover Letter

**Date**: 2026-10-12
**Journal**: IEEE Transactions on Information Forensics and Security
**Manuscript ID**: T-IFS-28362-2026 (existing draft; resubmission of the same manuscript, not a new submission)
**Title**: Probing-Resistant Masked Hardware: Formal Security Proofs and Simulation-Based Side-Channel Verification

Dear Editor,

Following the editorial notice of 9 October 2026, the appendix that was
previously uploaded as a separate file has been relabeled as **Supplemental
Material** and is uploaded as such. The main manuscript is self-contained and
is 13 pages or fewer in the two-column IEEE format.

## Contributions

- A characterization of the *soundness gap* between equipment-free
  value-based statistical verification and glitch-extended probing, through a
  cone-non-completeness condition. A first-order lint based on it is shown
  sound (a PASS makes the two verdicts coincide), and an explicit first-order
  witness shows that the gap is real (Theorems 3 and 4; Supplemental Material S2).
- A masked multiplication gadget (DOM with register barrier) proven robust
  $d$-NI with perfect simulation for arbitrary $d$ (Theorem 1), and a
  first-order AES S-box built from it.
- Equipment-free verification of the first-order design with PROLEAD
  ($0/14{,}400$ probing sets at $512{,}000$ simulations), gate-level TVLA/MI,
  and the lint, with an unmasked positive control.

## Scope

The empirical evaluation targets the first-order design; the gadget-level
proof (Theorem 1) holds for arbitrary $d$, and the lint theorem is stated at
first order. Limitations are discussed in the paper.

## Supplemental Material

Corrected PROLEAD worst-case value, the explicit gap witness, the
pre-barrier PROLEAD history, extended discussion, further verifiers, and
full-chip details.

## Artifact

RTL, synthesis scripts, lint, PROLEAD configurations and results are available at https://github.com/mipsan1/probing-resistant-masked-hardware and in the artifact bundle accompanying the submission.

## Declarations

The manuscript is not published elsewhere or under consideration at another
journal. The author approves this submission. No conflict of interest.

Sincerely,

Cheonshik Kim

Department of Computer Engineering, Sejong University, Seoul

mipsan@sejong.ac.kr

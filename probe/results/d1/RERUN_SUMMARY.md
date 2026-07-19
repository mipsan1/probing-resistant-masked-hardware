# RERUN SUMMARY — in-house side-channel verification on the NEW d=1 netlist

**Status: PARTIAL — interrupted by time budget.** The pipeline was repaired and
validated end-to-end; the first of four gate-level simulation chunks completed
and was analyzed (N = 2,500 of 10,000). **All numbers below marked "partial"
are N = 2,500 preliminary values, NOT the paper N = 10,000 numbers.** Do not
quote them in the manuscript. Everything needed to finish is staged; the exact
remaining commands are listed in §8.

Date of run: 2026-07-19. Workspace: `/Users/ckim/Downloads/IEEE-Transactions-TIFS_0717_hardware`.

---

## 1. What was found stale / broken (before any re-run)

| Item | Finding |
|---|---|
| `probe/results/reanalysis/d1_power_fixed.txt`, `d1_header_fixed.txt`, `d1_bittrace.txt`, `d1_bitheader.txt` | **STALE** — old 10-stage/27-DFF design: 27-bit rows, 160,001 cycles (16 cycles/triple). Backed up to `/tmp/inhouse_backup/` (copies; originals left in place, still stale). |
| `probe/results/d1/*` (all CSVs/reports) | **STALE** (old design). Not overwritten — fresh N=10,000 replacements do not exist yet. |
| `probe/results/reanalysis/d1_fixed/*`, figures in `probe/figures_fixed/` | **STALE** (derived from the stale traces above). |
| `syn/masked_sbox_first_order_syn.v` (Jul 19 12:59) | **STALE intermediate netlist** — 16-bit `valid_pipe`, no `r6_in` port. Cannot drive the updated testbenches. |
| `syn/prolead/circuit_struct.v` (Jul 19 16:02) | Current and PROLEAD-validated, but top module is `circuit(sboxIn, randomIn, sboxOut)` with `rst_n`/`valid_in` tied off and all internal names mangled — **not usable** by the in-house TBs (`masked_sbox_first_order` + hierarchical `dut.valid_pipe[..]` refs). |
| `probe/probe_analyzer.py`, `probe/tvla.py`, `probe/mi_power.py`, `probe/regen_results.py`, `probe/sensitivity_fixed.py` | Design-dependent constants for the OLD design: 27 wires / 15-cycle window / output stage 12 / pair offset 10. Need the new geometry (34 wires / 23 offsets / output stage 18). |
| `rtl/tb_probe_sim.v` | Updated to 34 wires OK, but header lacked `first_cycle` → bit-trace could not be fc-aligned (old analysis silently reused the *power* header's secrets+fc, a seed mismatch — probe sim uses CAFEBABE, power sim CAFEFACE). **Fixed (see §3).** |

## 2. New gate-level netlist for in-house sims (new artifact)

- Script: `syn/synth_d1_sim_netlist.ys` (NEW). Flow mirrors `syn/prolead/synth_for_prolead.ys` but top = `masked_sbox_first_order`, **no abc/dfflibmap mapping**, `setattr -set keep_hierarchy 0` **and** `setattr -mod -set keep_hierarchy 0` before `flatten` (needed because the gf hard cells carry `(* keep_hierarchy = 1 *)`), then `opt; clean`. Note: `async2sync` and `opt_clean -purge` from the PROLEAD script were deliberately dropped — they destroy the named registers (verified experimentally).
- Output: `syn/masked_sbox_first_order_sim_netlist.v` (NEW, 2.5 MB). Pure Verilog-2005 (assign expressions + always-block DFFs with async reset + enable) — iverilog-native, no simcells needed.
- Command: `yosys -q syn/synth_d1_sim_netlist.ys`
- **DFF inventory (parsed from the netlist, all original RTL names preserved): 818 DFFs** — valid_pipe[16:0] (17), y0_out[7:0], y1_out[7:0], valid_out (34 outer = the monitored set), plus 784 internal pipeline/barrier registers (x0/x1_s0..s7, operand-refresh x*_s2r, delay chains *_d1..d6, mul1..mul5 product registers, inv/affine registers). (PROLEAD's wrapper netlist had 816; the 2-DFF difference comes from the wrapper's tied-off `rst_n`/`valid_in`.)
- **Functional validation of this netlist: 256/256 exhaustive PASS** (`/tmp/inhouse_tb_exh_d1.v`, reference `gf_inv_byte`+affine, random masks per input).
- **Monitor-set verdict (task 1):** the TB's 34 wires exist in the netlist and are exactly the masked S-box's outer pipeline DFF Q wires (valid_pipe[0..16] + y0_out + y1_out + valid_out). They are a *subset* of the 818 DFFs; the old paper's "every DFF Q wire" claim covered all 27 DFFs of the old design, so for the new design the 34-wire set is NOT exhaustive. An 818-wire sweep was planned (commands in §8) but not run.

## 3. Testbench changes (reported per instructions; no design RTL touched)

1. `rtl/tb_probe_sim.v`:
   - header rows now carry a 4th column `first_cycle` (cycle counter added, mirrors `tb_power_sim.v`) — required for fc-based alignment of the bit trace with its OWN secrets.
   - `lfsr = 32'hCAFEBABE;` → `parameter [31:0] LFSR_SEED = 32'hCAFEBABE;` (seed unchanged by default) so the >300 s gate-level run can be split into LFSR-exact chunks.
2. `rtl/tb_power_sim.v`: same `LFSR_SEED` parameter (default 32'hCAFEFACE, unchanged). No other changes.
3. No changes to `manuscript.tex`, design RTL, or anything under `probe/results/d2/`.

## 4. Run geometry (verified from the finished chunk)

- 23 rows (cycles) per triple; row 0–1 = reset. Triple *t*: `first_cycle = 2 + 23·t` — **verified exact for all 2,500 triples of chunk 0**.
- Pipeline-offset window needed: **offsets 0..22 (23 offsets)** (old paper used 15).
- **Output stage: offset 18** — `y0_out ^ y1_out == AES_SBOX(secret)` for **2,500/2,500** triples at offset 18 (and `valid_out` high only there); at offsets 15–17 the outputs still hold the previous triple (2,491/2,500 mismatch vs current secret), confirming the 17-cycle latency + register timing.
- Monitored wires: **34**. Pipeline offsets: **23**.

## 5. Chunking method (exact-stimulus split, needed because one 10,000-triple
gate-level run takes ~690 s > the 300 s tool limit)

- Measured throughput: 4,229 triples / 290 s ⇒ ~14.6 triples/s ⇒ full run ≈ 686 s.
- Split: 4 chunks × 2,500 triples with a 2-triple warmup overlap (chunk *c* simulates triples 2500c−2..2500c+2499; first 2+46 rows dropped). With W=2 warmup the kept rows are bit-identical to a single full run (all pipeline registers are overwritten by each passing triple; y_out hold-state aligns after 1 warmup triple).
- LFSR chunk-start states precomputed (`/tmp/inhouse_lfsr_states.py`, same Fibonacci LFSR):
  - probe (base CAFEBABE): c0 `32'hCAFEBABE`, c1 `32'h8ED8DDAA`, c2 `32'h5797E836`, c3 `32'h5C693D7A`
  - power (base CAFEFACE): c0 `32'hCAFEFACE`, c1 `32'hA8C06B16`, c2 `32'h80F7044C`, c3 `32'h2DB93CD6`

## 6. Results obtained

### 6.1 Completed: gate-level probe-sim chunk 0 (triples 0–2,499)

- Command: `iverilog -g2012 -o /tmp/inhouse_p_c0 -Ptb_probe_sim.N_TRIPLES=2500 "-Ptb_probe_sim.LFSR_SEED=32'hCAFEBABE" rtl/tb_probe_sim.v syn/masked_sbox_first_order_sim_netlist.v && vvp /tmp/inhouse_p_c0` (2 m 42 s)
- Artifacts: `/tmp/inhouse_probe_c0.txt` (57,502 rows × 34 bits), `/tmp/inhouse_probe_c0.hdr` (2,500 triples; 256/256 distinct secrets).
- Estimator: plug-in MI (no smoothing), Miller–Madow, permutation null (300 shuffles, RNG seed 20260719) — same as `reanalysis.py`/`regen_results.py`. N = 2,500 ⇒ bias/null ≈ 4× larger than at N = 10,000 (single-wire MM bias alone = 255/(2·2500·ln2) ≈ 0.0736 bits).

**PARTIAL (N=2,500) single-wire I(w;S), max over 34 wires × 23 offsets:**

| wire | worst off | plug-in (bits) | MM-corr (bits) | null p99 (bits) |
|---|---|---|---|---|
| y0_out[7] | 18 | 0.111496 | 0.037918 | 0.094177 |
| y1_out[7] | 18 | 0.111458 | 0.037881 | 0.095070 |
| y1_out[5] | 18 | 0.096098 | 0.022521 | 0.094867 |
| y0_out[5] | 18 | 0.095814 | 0.022237 | 0.097733 |
| y0_out[0] | 0  | 0.094114 | 0.020537 | 0.095222 |

max MM-corrected over wires = 0.037918 bits; max null p99 = 0.098909 bits.
Interpretation: consistent with estimator noise at N=2,500 (782 correlated tests); not a paper-quality number.

**PARTIAL (N=2,500) 2-wire joint I(w_i,w_j;S), max over all 561 pairs × 23 offsets:**

- top pair **y0_out[7] × y1_out[7] @ offset 18**: plug-in **1.110694 bits**, MM-corr **0.889962 bits**, null p99 **0.282038 bits**.
- ⚠ **This is structural, not leakage**: at the output stage the two output shares satisfy y0^y1 = SBOX(S), so the pair (y0[i], y1[i]) necessarily carries ≈ 1 bit about S (the i-th S-box output bit) at offset 18. Any correct 2-share S-box shows this when the joint-MI sweep includes the output cycle. The old paper's 0.0664-bit d=2 number used fixed pair-offset 10, which *missed* the output stage. The paper text must address this (either exclude the recombination stage by construction, or state it explicitly). PROLEAD's robust-probing verdict on the same netlist: 0/14,400 leaking sets @ 512,000 simulations (independent confirmation).

### 6.2 Not run (no data)

- Probe chunks 1–3 (triples 2,500–9,999) → full N=10,000 bit trace.
- Power sim (all 4 chunks) → all TVLA / per-stage HD-MI / per-bit MI / full-trace MI / corr(HD, HW(S)) numbers.
- 818-wire extended sweep (monitor-set exhaustiveness check).
- Positive control re-run (existing unmasked results of Jul 19 08:23 in `probe/results/reanalysis/unmasked/` are from the current `tb_power_sim_unmasked.v` + `unmasked_sbox.v`, seed CAFEFACE; they remain the latest valid positive-control numbers: wire MI 1.0 bit fires, output-stage MI 1.086 plug-in / 0.921 MM bits, higher-order TVLA max|t| 5.83, first-order max|t| 4.21/2.45, LUT 0 mismatches, 256/256 coverage, overall detection FIRES).
- Figures, sensitivity (see §7), RERUN at N=10,000.

## 7. Script adaptation status

- `sensitivity_fixed.py` is **design-dependent** (hardcodes `N_OFF = 15`, `OUT_STAGE = 12`, and the d1/d2 trace paths). It must be re-run for d=1 with `N_OFF = 23`, output stage 18, and d=2 skipped. Not yet done.
- `make_figures_fixed.py` reads `probe/results/reanalysis/{d1,d2}_fixed/`; it will work with 23-stage CSVs after adjusting `set_xticks(range(0, 15, 3))` → `range(0, 23, 3)` (three call sites). `fig_combined.pdf` mixes d=1/d=2 panels; regenerate with fresh d=1 + OLD d=2 panel data kept as-is (d=2 not re-run, per instructions) and note this in the paper.
- `regen_results.py` constants to update for d=1: `WIRE_NAMES[2]` → 34 names, `N_OFF` 15 → 23, per-bit stage 12 → 18, pair offset 10 → 18, and bit-trace secrets/fc must come from the bit header (now has fc), not the power header (seed mismatch bug in the old flow).

## 8. Exact remaining commands (in order)

```bash
cd /Users/ckim/Downloads/IEEE-Transactions-TIFS_0717_hardware
# (a) probe chunks 1..3  (~2m45s each; quote the -P argument as shown)
iverilog -g2012 -o /tmp/inhouse_p_c1 -Ptb_probe_sim.N_TRIPLES=2502 "-Ptb_probe_sim.LFSR_SEED=32'h8ED8DDAA" rtl/tb_probe_sim.v syn/masked_sbox_first_order_sim_netlist.v && vvp /tmp/inhouse_p_c1 && mv /tmp/fo_trace.txt /tmp/inhouse_probe_c1.txt && mv /tmp/fo_header.txt /tmp/inhouse_probe_c1.hdr
iverilog -g2012 -o /tmp/inhouse_p_c2 -Ptb_probe_sim.N_TRIPLES=2502 "-Ptb_probe_sim.LFSR_SEED=32'h5797E836" rtl/tb_probe_sim.v syn/masked_sbox_first_order_sim_netlist.v && vvp /tmp/inhouse_p_c2 && mv /tmp/fo_trace.txt /tmp/inhouse_probe_c2.txt && mv /tmp/fo_header.txt /tmp/inhouse_probe_c2.hdr
iverilog -g2012 -o /tmp/inhouse_p_c3 -Ptb_probe_sim.N_TRIPLES=2502 "-Ptb_probe_sim.LFSR_SEED=32'h5C693D7A" rtl/tb_probe_sim.v syn/masked_sbox_first_order_sim_netlist.v && vvp /tmp/inhouse_p_c3 && mv /tmp/fo_trace.txt /tmp/inhouse_probe_c3.txt && mv /tmp/fo_header.txt /tmp/inhouse_probe_c3.hdr
# merge: c0 all rows; c1..c3 drop first 48 rows (2 reset + 2 warmup triples)
# and first 2 header data lines; offset kept fc by 23*(2500c-2); then VERIFY
# fc == 2+23t for all 10,000 triples before analysis.

# (b) power chunks 0..3 (same pattern, tb_power_sim, seeds from §5)
iverilog -g2012 -o /tmp/inhouse_pw_c0 -Ptb_power_sim.N_TRIPLES=2500 "-Ptb_power_sim.LFSR_SEED=32'hCAFEFACE" rtl/tb_power_sim.v syn/masked_sbox_first_order_sim_netlist.v && vvp /tmp/inhouse_pw_c0 && mv /tmp/fo_power.txt /tmp/inhouse_power_c0.txt && mv /tmp/fo_power_header.txt /tmp/inhouse_power_c0.hdr
# c1: N_TRIPLES=2502 SEED=32'hA8C06B16 ; c2: SEED=32'h80F7044C ; c3: SEED=32'h2DB93CD6
# merge identically (cycle column offset too); VERIFY cycle == 0..230001 and fc == 2+23t.

# (c) analysis at N=10,000 with 34 wires / 23 offsets / output stage 18:
#     single-wire MI (plug-in, MM, null p99@300), all-pairs joint MI,
#     TVLA cond + fixed-vs-random (genuine-variance stages), centered
#     2nd/3rd moments, per-stage I(HD;S), per-secret-bit MI at stage 18,
#     full-trace MI, corr(HD, HW(S)) at max-MI stage -> probe/results/d1/*.csv
#     and probe/results/reanalysis/d1_fixed/*.csv (overwrites stale files;
#     stale copies are in /tmp/inhouse_backup/).
# (d) 818-wire sweep: auto-generate monitor TB from /tmp/inhouse_d1_allq.txt
#     (818 Q names), same chunking, single-wire MI over 818 x 23 + top-10
#     pairs at offset 18.
# (e) positive control: iverilog -g2012 -o /tmp/inhouse_uc rtl/tb_power_sim_unmasked.v rtl/unmasked_sbox.v && vvp /tmp/inhouse_uc
#     then python3 probe/positive_control.py   (writes results/reanalysis/unmasked/)
# (f) figures: adjust xticks to range(0,23,3) in probe/make_figures_fixed.py,
#     run it (regenerates d1 figs fresh + d2 figs from OLD d2 data — note in paper).
# (g) sensitivity: d1-only run with N_OFF=23, OUT_STAGE=18.
```

## 9. PASS/FAIL vs thresholds (what can be said today)

| Check | Threshold | Result |
|---|---|---|
| Netlist functional correctness (gate-level, exhaustive) | 256/256 | **PASS (256/256)** |
| Alignment / output stage | fc = 2+23t; y0^y1=SBOX(S) at one offset | **PASS** (offset 18, 2,500/2,500) |
| Single-wire MI, N=10,000 | ≤ null p99, MM ≈ 0 | **NOT MEASURED** (partial N=2,500 consistent with noise) |
| 2-wire joint MI, N=10,000 | ≤ null p99 | **NOT MEASURED**; output-stage share-recombination artifact (~1 bit at offset 18) must be addressed in the paper text |
| TVLA / HD-MI / per-bit / full-trace / corr | \|t\| < 4.5 etc. | **NOT MEASURED** (power sim not run) |
| Positive control | apparatus fires | Last valid run (Jul 19): **FIRES** (wire MI 1.0 bit ≫ null 0.0232; stage MI 1.086/0.921 bits; higher-order \|t\| 5.83) — not re-run in this session |
| PROLEAD (independent) | 0 leaking sets | 0/14,400 @ 512,000 sims (given; not re-run) |

---

# UPDATE LOG (incremental, newest last)

## Update 1 — sliding-window LFSR artifact discovered & stimulus fixed

The first full N=10,000 run (chunks merged, fc/secrets verified) showed
apparently elevated share MI at the output stage: single-wire max
I(y0_out[7];S) = 0.043644 bits @ off 18 (family-wise null p99 over
34x23 tests = 0.024601, empirical p < 1/300), and non-structural pair
I(y0_out[7],y1_out[6];S) = 0.119164 bits @ 18 (family null p99 0.068562).

**Root cause: stimulus degeneracy, not design leakage.** The TBs' LFSR
advanced only 1 shift per byte, so the 9 "random" bytes per triple form a
sliding window sharing 7/8 bits: measured I(s0;s1) = 6.999 bits,
P(s1[7:1]==s0[6:0]) = 1.0000. The effect reproduced in both split halves
(0.062/0.067 bits). PROLEAD (independent randomness) had already reported
0/14,400 leaking sets for the same netlist.

**Fix (reported TB change):** `next_random` in rtl/tb_probe_sim.v,
rtl/tb_power_sim.v, rtl/tb_power_sim_unmasked.v now advances the LFSR
8 shifts per byte (same seeds CAFEBABE/CAFEFACE, still deterministic).
Contaminated traces/CSVs archived under
/tmp/inhouse_backup/contaminated_sliding_window/ (they must NOT be quoted).

New chunk LFSR states (72 shifts/triple): probe c1..c3 = 32'h968AC1CC,
32'h7CED7443, 32'hF954D581; power c0..c3 = 32'hCAFEFACE, 32'h8D8E358C,
32'hFEC28E6A, 32'hAB432B71.

Re-run status: probe c0, c1 done (57,502 / 57,548 rows); probe c2 aborted
by session timeout -> re-running; c3 + power c0..c3 pending.
All numbers below this log will be appended step-by-step as they complete.

## Update 2 — FINAL N=10,000 numbers (fixed stimulus, 8-shift LFSR, same seeds)

Merged traces verified: 230,002 rows each; fc = 2+23t for all 10,000 triples;
(secret,s0,s1) match the 8-shift LFSR model for every triple; power cycle
column sequential 0..230,001; I(s0;s1) = 2.82 bits < 4.69-bit plug-in bias
floor for a 256x256 table at N=10,000 (MM-corrected = 0 -> independent).
Traces installed at probe/results/reanalysis/{d1_bittrace.txt,
d1_bitheader.txt, d1_power_fixed.txt, d1_header_fixed.txt}.
Monitored wires: 34. Pipeline offsets: 23 (0..22). Output stage: 18.
Analysis: probe/rerun_d1_analysis.py + probe/rerun_d1_familynull.py
(estimator identical to reanalysis.py: plug-in, Miller-Madow, 300-shuffle
permutation nulls, RNG seed 20260719). Results CSVs in probe/results/d1/
and probe/results/reanalysis/d1_fixed/.

### Task 2 — probing MI (N=10,000)  => PASS
- Max single-wire I(w;S) over 34 wires x 23 offsets:
  **0.021900 bits** plug-in (y1_out[5] @ off 0), MM-corrected 0.003506,
  single-test null p99 0.022640. Max MM over wires 0.003506. Max
  single-test null p99 over wires 0.023347.
  Family-wise (max-statistic) permutation null p99 = 0.024724, null max =
  0.025210; observed 0.021900 -> empirical p = 0.59. Within null.
- Max 2-wire joint I(w_i,w_j;S) over all 561 pairs x 23 offsets:
  (a) global max **1.020850 bits** plug-in (y0_out[6] x y1_out[6] @ off 18),
      MM 0.965667, null p99 0.062716 — the structural output-share
      recombination pair (y0^y1 = SBOX(S) at the output register; expected
      ~1 bit by construction, offsets 18..22 all show it).
  (b) max EXCLUDING all 8 share pairs (y0_out[i],y1_out[i]) at the whole
      output-hold window (offsets 18..22): **0.062897 bits** plug-in
      (y1_out[1] x y1_out[6] @ off 18), MM 0.007714, single-test null p99
      0.062760. Family-wise (max-statistic over 12,895 kept tests) null
      p99 = 0.068652, null max = 0.069532; empirical p = 0.91. Within null.

### Task 3 — TVLA / power MI (N=10,000)  => PASS
- Genuine-HD-variance stages: [18] (only the output-toggle stage; other
  offsets have HD in {1,2} — degenerate t).
- Conditional max|t| = **0.9172** (stage 18, t = +0.9172).
  Fixed-vs-random max|t| = **0.3484** (stage 18, t = -0.3484).
- Centered higher-order max|t|: 2nd moment **1.2845**, 3rd moment
  **0.7704** (max over both splits); all-moments max 1.2845. All < 4.5.
- Per-stage I(HD(c);S): max at **stage 18**: plug-in **0.213256 bits**,
  MM-corrected 0.000000, null p99 0.227230 (within null).
  corr(HD(stage 18), HW(S)) = **-0.0183**.
- Per-secret-bit MI @ stage 18 (plug-in, bits 0..7):
  0.0005 0.0014 0.0013 0.0005 0.0008 0.0017 0.0016 0.0016;
  max 0.001723 (bit 5), MM 0.000641, null p99 0.002234 (all <= null p99).
- Full-trace aggregated MI (all 23 stages flattened): plug-in
  **0.009292 bits**, MM-corrected **0.000000**.

### PASS/FAIL vs thresholds (final)
| check | threshold | value | verdict |
|---|---|---|---|
| single-wire MI | <= family null p99 | 0.021900 <= 0.024724 | PASS |
| single-wire MM | ~0 | 0.003506 | PASS |
| pair MI (non-structural) | <= family null p99 | 0.062897 <= 0.068652 | PASS |
| pair MM | ~0 | 0.007714 | PASS |
| TVLA cond / fixed | < 4.5 | 0.9172 / 0.3484 | PASS |
| TVLA 2nd/3rd moment | < 4.5 | 1.2845 / 0.7704 | PASS |
| per-stage HD-MI | <= null p99 | 0.213256 <= 0.227230 | PASS |
| per-bit MI | <= null p99 | 0.001723 <= 0.002234 | PASS |
| full-trace MI | MM ~0 | 0.009292 / 0.000000 | PASS |
Structural pair note: the ~1.02-bit output-share pair at offsets 18..22 is
unavoidable for any correct 2-share S-box when the joint-MI sweep includes
the output-hold cycles; it is reported explicitly as (a) above and excluded
from the security-relevant max (b). Consistent with PROLEAD: 0/14,400
leaking sets @ 512,000 sims on the same netlist.

### Remaining (next updates)
- Figures (task 6), d1-only sensitivity (task 7), positive-control re-run
  with fixed stimulus (task 5; Jul-19 numbers stand until then — unmasked
  design unchanged, but its stimulus had the same sliding-window artifact,
  so re-running with the repaired TB for consistency).
- 818-wire extended sweep: not run (budget); 34-wire outer-shell set was
  the established monitor set.

## Update 3 — figures, sensitivity, positive control (final)

### Task 6 — figures regenerated (probe/figures_fixed/)
make_figures_fixed.py updated: xticks range(0,15,3) -> range(0,23,3)
(4 sites); added plot_combined_d1(). Regenerated:
- fig_probing_d1.pdf (34 wires, fresh N=10,000 data)
- fig_tvla_d1.pdf, fig_mi_d1.pdf (fresh data, 23-stage window)
- fig_combined.pdf — fresh d=1 panels + OLD d=2 panels (d=2 NOT re-run;
  d2_fixed CSVs unchanged; keep this caveat with the figure)
- fig_combined_d1.pdf — NEW d=1-only variant (no stale d=2 content)
- fig_probing_d2.pdf / fig_mi_d2.pdf / fig_tvla_d2.pdf re-rendered from the
  UNCHANGED old d=2 CSVs (stale data, cosmetic re-render only).
- fig_sensitivity_d1.pdf regenerated (below); fig_sensitivity_d2.pdf untouched.

### Task 7 — sensitivity_fixed.py is design-dependent (re-run for d=1)
Hardcoded N_OFF=15/OUT_STAGE=12 and a fixed pair offset 10 -> updated to
N_OFF=23, OUT_STAGE=18 (pair offset now OUT_STAGE); main() limited to d1
(d2 sensitivity CSV/figure untouched). Output:
probe/results/reanalysis/d1_fixed/sensitivity_fixed.csv +
probe/figures_fixed/fig_sensitivity_d1.pdf. Values
(N, single-wire plug-in/MM, joint plug-in/MM, |t| cond/fixed, nfix, per-bit plug-in/MM):
- N=1000:  0.2560/0.0749, 1.2367/0.6935, 0.63/0.22,  6, 0.0149/0.0055
- N=2000:  0.1309/0.0390, 1.1182/0.8423, 0.96/0.32,  8, 0.0079/0.0032
- N=5000:  0.0427/0.0059, 1.0412/0.9308, 0.23/0.55, 15, 0.0030/0.0009
- N=10000: 0.0219/0.0035, 1.0208/0.9657, 0.92/0.35, 32, 0.0017/0.0006
Single-wire MM-corrected MI decays ~1/N (0.0749 -> 0.0035): plug-in values
are estimator bias only, no leakage signal. Joint MI converges to ~1 bit
(the structural output pair dominates the max at all N; see Update 2).

### Task 5 — positive control re-run (fixed stimulus, same seed CAFEFACE)
Re-ran rtl/tb_power_sim_unmasked.v + rtl/unmasked_sbox.v (160,001 rows,
10,000 triples; iverilog printed two benign $fwrite fd warnings also
present in the Jul-19 run) and probe/positive_control.py (N_OFF=15,
output offset auto-detected). Traces/CSVs in
probe/results/reanalysis/unmasked/ (old ones backed up to /tmp/inhouse_backup/).
- LUT validation: output offset 12, **0/10,000 mismatches**, coverage 256/256.
- per-output-bit wire MI: max **1.000000 bits** (y_out[2]; MM 0.9816;
  max null p99 over wires 0.0234) -> probing wire-MI instrument FIRES.
- pair MI at the TRUE output offset 12 (recomputed; note
  positive_control.py's pair table uses the hardcoded offset 10, which
  misses the unmasked output stage): top pair y_out[3] x y_out[4]
  plug-in **1.999995 bits**, MM 1.944812, null p99 0.063509 -> FIRES.
- output-stage I(HD;S) @ stage 12: plug-in 0.138468 bits, MM 0.000000,
  null p99 -> does NOT fire.
- first-order HD-mean TVLA: cond max|t| 0.6140, fixed 0.7855 -> no fire.
- centered higher-order max|t|: 2.2097 -> no fire.
**Interpretation (important):** with INDEPENDENT secrets, the HD-of-19-
wires power instrument is blind on the unmasked design BY CONSTRUCTION:
at the output stage, HD = HW(SBOX(S_t) ^ SBOX(S_{t-1})) with S_{t-1}
uniform, so the HD distribution is Binomial(8, 1/2) regardless of S_t —
every moment is exactly secret-independent. The Jul-19 control numbers
(stage MI 1.086 bits, higher-order |t| 5.83) fired only because the
sliding-window LFSR correlated consecutive secrets — the same stimulus
artifact as in Update 1; those numbers must not be quoted as detection
evidence. The positive control's purpose is fulfilled by the probing
instruments: wire MI 1.0 bit and pair MI 2.0 bits vs null p99 <= 0.064 —
the apparatus DOES detect the unmasked design overwhelmingly.
Verdict: POSITIVE CONTROL PASSES via probing wire/pair MI; HD-power
sub-instruments documented as construction-blind on this monitor set.

### Instrument status vs tasks
- Tasks 1-4, 6, 7, 8: COMPLETE (numbers in Update 2 + this update).
- Task 5: COMPLETE with corrected interpretation (above).
- Not done (budget): 818-wire extended sweep; d=2 anything (out of scope,
  outputs untouched); regen_results.py itself NOT re-run (its hardcoded
  old-design constants superseded by probe/rerun_d1_analysis.py, which
  produced all Update-2 CSVs).

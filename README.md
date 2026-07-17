# Probing-Resistant Masked Hardware

[![PROLEAD cross-check](https://github.com/mipsan1/probing-resistant-masked-hardware/actions/workflows/prolead.yml/badge.svg)](https://github.com/mipsan1/probing-resistant-masked-hardware/actions/workflows/prolead.yml)

A first-order Boolean-masked AES-128 implementation in Verilog,
with full RTL/gate-level equivalence verification and synthesis
results.  This repository accompanies the IEEE TIFS submission
*Probing-Resistant Masked Hardware: A First-Order Masked AES
Round 1*.  The badge above links to the PROLEAD robust
$d$-probing verification run on every push; the resulting
`prolead-report` artifact contains the full PROLEAD report
(`prolead_summary.md`).

## What is here

* **RTL**: A 16-S-box masked AES-128 round 1, with first-order
  Boolean masking and a domain-oriented S-box.  Also a
  second-order S-box for comparison.
* **Testbenches**: 256-input exhaustive S-box tests, 100-random
  round tests, power-trace dumper.
* **Synthesis**: Yosys 0.67+ flow, producing a flat gate-level
  netlist that preserves the `$_DFF_*_` primitives needed for
  iverilog gate-level simulation.
* **Area report**: Cell counts, technology-mapped comparison,
  critical-path delay estimate.
* **Probe evaluation**: TVLA, mutual-information, and probing
  scripts for the standalone S-box (see `probe/`).
* **Paper**: `manuscript.tex`, `manuscript.bib`, and the IEEEtran
  class file.  Compiles with `pdflatex` + `bibtex`.

## Repository layout

```
.
├── rtl/                      Verilog sources + testbenches
│   ├── masked_sbox_pkg.v               shared GF(2^8) helpers
│   ├── masked_sbox_first_order.v       first-order S-box
│   ├── masked_sbox_second_order.v      second-order S-box
│   ├── masked_aes_round1.v             16-S-box masked round 1
│   ├── tb_masked_sbox.v                RTL S-box self-check
│   ├── tb_masked_sbox_exhaustive.v     256-input RTL S-box
│   ├── tb_masked_sbox_exhaustive_syn.v gate-level S-box
│   ├── tb_masked_aes_round1.v          round 1 testbench
│   └── tb_power_dump.v                 per-cycle trace dumper
├── syn/                      Synthesis
│   ├── synth_round1.ys                 Yosys flow
│   ├── masked_aes_round1_syn.v         round 1 gate-level netlist
│   ├── gen_power_dump.py               trace generator
│   ├── run_power_dump_rtl.sh           RTL trace dump
│   ├── run_power_dump.sh               gate-level trace dump
│   ├── estimate_delay_json.py          critical-path estimator
│   └── AREA_REPORT.md                  cell counts + delay
├── probe/                    Probe-evaluation scripts
│   ├── tvla.py                          Welch's t-test
│   ├── mi_power.py                      mutual information
│   ├── sensitivity.py                   per-bit sensitivity
│   ├── probe_analyzer.py                main analyzer
│   └── EVALUATION_SUMMARY.md            results summary
├── sim/                      Run-time data (vector files)
├── reference/                Reference implementations
├── PROLEAD/                  PROLEAD tool source (not built)
├── manuscript.tex            Paper source
├── manuscript.bib            Bibliography
└── IEEEtran.cls              LaTeX class
```

## Reproducing the results

### 1. RTL simulation (fast)

```sh
cd rtl/
iverilog -g2012 -I. -o /tmp/sb_sim \
    tb_masked_sbox_exhaustive.v \
    masked_sbox_first_order.v masked_sbox_second_order.v \
    masked_sbox_pkg.v
vvp /tmp/sb_sim
# expected: first-order 256/256 pass, second-order 256/256 pass
```

### 2. Gate-level synthesis + simulation

```sh
cd syn/
yosys -s synth_round1.ys
cd ../rtl/
iverilog -g2012 -I. -o /tmp/r1_gl \
    tb_masked_aes_round1.v \
    ../syn/masked_aes_round1_syn.v
vvp /tmp/r1_gl
# expected: 100/100 pass
```

### 3. Power-trace dump (per-cycle, RTL)

```sh
cd syn/
python3 gen_power_dump.py           # 10K vectors
bash run_power_dump_rtl.sh
# Output: sim/power_dump.txt (per-cycle y0_out, y1_out bits)
```

### 4. Critical-path delay estimate

```sh
cd syn/
yosys -p "read_verilog -sv ../rtl/*.v; \
          hierarchy -check -top masked_aes_round1_first_order; \
          flatten; proc; opt; fsm; opt; memory; opt; techmap; opt; clean; \
          write_json masked_aes_round1_flat.json"
python3 estimate_delay_json.py masked_aes_round1_flat.json
# expected: critical path ~ 410 unit-delay ≈ 20.5 ns (65 nm CMOS)
```

### 5. Probe evaluation (S-box)

```sh
cd probe/
python3 probe_analyzer.py
# Output: results/ + figures/ (TVLA, MI, sensitivity)
```

### 6. Paper build

```sh
cd <repo root>
pdflatex manuscript
bibtex  manuscript
pdflatex manuscript
pdflatex manuscript
```

## Tool requirements

* **iverilog** ≥ 11 (with `-g2012` and `$value$plusargs` support)
* **Yosys** ≥ 0.55 (tested on 0.67+)
* **Python** ≥ 3.9
* **LaTeX**: TeX Live 2022+ with `IEEEtran` class
* **BibTeX** (TeX Live distribution)
* **Optional**:
  - **PROLEAD** (Linux, requires Boost 1.71+, libomp, gdstk, flint)
  - **VCS / Modelsim** for production gate-level sims
  - **OpenSTA** for accurate timing on a real Liberty file

## Notes

* The gate-level netlist is **not** mapped to a specific standard
  cell library.  Cell counts are a fair area proxy but the
  critical-path delay estimate (unit-delay model) is coarse.  For
  a real tape-out, supply a Liberty file and run `abc -liberty`.
* PROLEAD's C++ toolchain cannot be built on macOS hosts (Boost +
  libflint + libgmp + libmpfr + OpenMP dependency chain, plus
  Apple clang's lack of `-fopenmp`).  The
  `.github/workflows/prolead.yml` workflow runs the same
  `syn/run_prolead_docker.sh` recipe on a free Linux runner for
  every push to `main` (and on `workflow_dispatch` for manual
  reproduction); the resulting `prolead-report` artifact contains
  `prolead_summary.md` with PROLEAD's verdict.
* Per-cycle power-trace dumping at 10K vectors is too slow for
  iverilog in a single-threaded sim — the RTL flow dumps ~1.5K
  cycles in <1 s; the gate-level flow dumps the same in ~2 min.

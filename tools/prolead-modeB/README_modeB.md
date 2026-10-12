# PROLEAD mode B run bundle (macOS / Apple Silicon)

This bundle closes the last empirical cell in `tab:lint-vs-prolead`
(the B row) by running PROLEAD on the single-domain-pipeline-bypassed
variant of `masked_sbox_first_order`. Expected wall time on an M3
16 GB laptop: **~30-60 min** for the 128 K smoke test, **~2-4 h** for
the 512 K final run.

## 1. Files in this bundle

| File | Purpose |
|------|---------|
| `make_mode_B_netlist.py` | JSON netlist transformer (bypass 16 DFFs) |
| `prolead_config_modeB.yaml` | PROLEAD config template (edit before use) |
| `build_and_run_mode_B.sh` | One-shot Homebrew + build + run |
| `README_modeB.md` | this file |

## 2. Directory layout on your MacBook

Create a fresh working directory and place files exactly like this:

```
~/prolead-modeB/                       <-- run scripts from here
├── build_and_run_mode_B.sh            <-- from this bundle
├── make_mode_B_netlist.py             <-- from this bundle
└── design/
    ├── netlist.json                   <-- YOUR baseline Yosys JSON netlist
    ├── modeB_dffs.txt                 <-- YOUR list of 16 DFF instance names
    └── prolead_config_modeB.yaml      <-- from this bundle, then edited
```

After the first run, the script creates:

```
~/prolead-modeB/
├── PROLEAD/                           <-- cloned + built
├── design/
│   ├── netlist_modeB.json             <-- auto-generated
│   └── netlist_modeB.v                <-- auto-generated (yosys)
└── results/
    └── modeB_smoke_YYYYMMDD_HHMMSS.log
```

## 3. One-time prerequisites

```bash
# Homebrew (skip if already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Xcode CLT (for clang/git)
xcode-select --install    # answer prompt if it appears
```

The run script installs `boost`, `libomp`, `cmake`, `yosys`,
`python@3.12` automatically on first invocation.

## 4. Preparing the two YOUR-side inputs

### 4a. `design/netlist.json`

This is the same file you used with `lint_real.py` for the paper's
baseline lint experiment (produced by Yosys `write_json` on
`masked_sbox_first_order` after `flatten`). Copy it into `design/`.

### 4b. `design/modeB_dffs.txt`

One DFF instance name per line -- the 16 single-domain pipeline
registers that variant B bypasses. Two ways to produce this list:

- **From your existing `lint_real.py` run**: it classified DFFs into
  single-domain / BLINDED-cross / UNBLINDED. Mode B was defined as
  the 16 registered stages that sit downstream of DOM cross-product
  refresh (single-domain, no operand-refresh). If your lint script
  did not dump this list, rerun with a `--print-modeB` flag or grep
  its diagnostic output for the 16 names it printed when you produced
  the mode B ablation result (DFF leak 0 / OUT leak 0).

- **Manual identification**: the 16 instances are the retiming DFFs
  between Itoh--Tsujii stages that carry already-refreshed single-
  domain values. Instance names typically match a pattern like
  `pipe_reg_*` or `stage[0-4]_dff_*` in the Yosys JSON. Run

  ```bash
  python3 make_mode_B_netlist.py --in design/netlist.json | grep -i pipe
  ```

  to inspect candidates, then commit 16 names to `modeB_dffs.txt`.

### 4c. Config YAML

The simplest and safest procedure:

1. Copy your existing **baseline** PROLEAD YAML (the one that produced
   `0/14,400 @ 512K`) to `design/prolead_config_modeB.yaml`.
2. Change **only** two fields, marked `[MODEB]` in the template:
   - `hdl_files:` -> `- design/netlist_modeB.v`
   - `reports.report_file:` -> `results/modeB_report.txt`
3. Everything else -- shares, randomness, order, cycles, probing set
   size -- **must stay identical to baseline** for the cross-check to
   be meaningful.

The provided template shows the expected structure but its `shares`
and `randomness` sections must be replaced with your baseline values.

## 5. Executing

```bash
cd ~/prolead-modeB
chmod +x build_and_run_mode_B.sh

# smoke test first (~30-60 min on M3)
./build_and_run_mode_B.sh

# after smoke passes, final run (~2-4 h on M3)
./build_and_run_mode_B.sh --full
```

The script uses `caffeinate` so the Mac will not sleep during the run.
Keep the lid open for best thermal performance.

## 6. Interpreting the log

At the end of the run, look for:

```
=== Result ===
leaking probing sets:  0 / 14400          <-- expected PASS
...
```

Any non-zero count means variant B leaks under a glitch-extended
probe, which would *contradict* the lint's PASS verdict and require
investigation. A zero count confirms lint soundness on this variant
and closes the empirical cross-check.

## 7. What to send back

One file:

```
~/prolead-modeB/results/modeB_full_YYYYMMDD_HHMMSS.log
```

With that log, the B row of `tab:lint-vs-prolead` can be updated in
`manuscript.tex` (replace `pending (cloud)` with the numeric verdict)
and P1 empirical closure is complete.

## 8. Troubleshooting

- **`ld: library 'omp' not found`** -> `brew link --force libomp` then
  re-run the build.
- **PROLEAD CMake fails on `find_package(Boost ...)`** -> export
  `BOOST_ROOT=$(brew --prefix boost)` before invoking cmake.
- **`fatal error: 'omp.h' file not found`** -> confirm
  `$(brew --prefix libomp)/include/omp.h` exists; if using
  Homebrew's `llvm` instead of Apple clang, set
  `CC=$(brew --prefix llvm)/bin/clang` before running.
- **Memory pressure warning** -> lower `performance.max_ram_gb` in the
  YAML to 8, or reduce `compact_distribution` from 32 to 16.
- **DFFs not found in netlist** -> your instance names in
  `modeB_dffs.txt` do not match the JSON. Run
  `python3 make_mode_B_netlist.py --in design/netlist.json` with no
  `--dff-list` to print a candidate roster.

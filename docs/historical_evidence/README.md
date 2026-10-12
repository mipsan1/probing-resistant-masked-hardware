Historical Evidence (2nd-tier provenance)
============================================

This folder contains the original 7/19/2026 PROLEAD logs, the
value-based TVLA/MI summary, and analysis notes from the macOS native
runs that produced the 0/14,400 verdict reported in the paper.

These logs are the 2nd tier of the proof-of-correctness strategy:

1. **1st tier** (numerical / simulator-based reproduction): NOT in this
   bundle. Requires Verilator/iverilog + cycle-accurate simulation +
   TVLA/MI recomputation. Will be added in a TIFS minor revision if
   requested.
2. **2nd tier** (historical logs + RTL provenance): THIS FOLDER.
   - RTL MD5 `32c5a7ed364a6560718294a6fc85372a` (current) ==
     7/19 15:57 RTL == the RTL used to synthesize the 7/19 PROLEAD
     input netlist. Verified.
   - PROLEAD config (7/19 17:23, in `synth/config.json`) is preserved
     in the current bundle. 7-byte `randomIn[55:0]`, 19 clock cycles,
     512,000 simulations, d=1, transitional leakage = true.
   - 7/19 PROLEAD stdout (file 01) records 56 fresh mask signals,
     15,200 placable probes, 14,400 unique probing sets, consistent
     with the 7-byte, 19-cycle, 7-multiplication+operand-refresh
     design that the current RTL describes.
   - 7/19 unmasked positive control (file 02) flags 1,224/1,890 sets
     with worst -log10(p) = inf, demonstrating that the PROLEAD
     channel is alive and capable of detecting leaks when the design
     is unmasked.
   - Value-based TVLA / MI (file 04) on the d=1 masked S-box shows
     max |t| = 0.92 (under 4.5), wire max MI = 0.022 (under null p99
     0.023), and pair MI = 0.97, consistent with the theoretical
     analysis (Theorem 3 in the paper, robust d-NI under noisy
     leakage evaluation).
   - 7/19 13:24 `circuit_struct_attr.v` (file 08) is the macOS synth
     result, but it is a 6-byte randomIn netlist (pre-r6_in RTL),
     NOT the 7/19 PROLEAD input. See file 08 for details.

Together, these logs record that the 7/19 PROLEAD run used the RTL with
the MD5 above and the configuration preserved in `synth/config.json`. The
gate-level netlist of that run was not preserved and has not been
reproduced bit-exactly; runs of regenerated netlists differ in probe counts
and are listed in the top-level README.

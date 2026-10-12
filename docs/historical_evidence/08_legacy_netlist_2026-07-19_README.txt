Historical netlist (do NOT use as 7/19 PROLEAD input)
======================================================

This file is `circuit_struct_attr.v` (9.1 MB) from the 7/19 13:24 synth run
on macOS native. It is preserved here only as historical context, NOT as
the netlist that PROLEAD consumed for the 7/19 17:24-50 run.

Why it is not the 7/19 PROLEAD input:
- This netlist has `input [47:0] randomIn` (6 bytes, 48 bits), but the
  7/19 PROLEAD config.json has `always_random_inputs: ["randomIn[55:0]"]`
  (7 bytes, 56 bits).
- 6-byte netlist corresponds to the pre-r6_in RTL (r0..r5 only, no
  operand-refresh byte for mul1's x^4 path).
- The 7/19 PROLEAD stdout logged "Successfully matched 56 fresh mask
  signals" (7 bytes), so the actual input netlist was 7 bytes.
- The 7/19 PROLEAD stdout also logged "15200 placable probes", but this
  6-byte netlist (when run through the same PROLEAD on 10/12 09:38)
  flagged 22/12,384 sets with worst -log10(p) = 16.76. That verdict
  is consistent with an unmasked / barrier-less variant, not the
  masked post-barrier design.

The actual 7/19 17:24 PROLEAD input netlist (7-byte randomIn, 15,200
probes, 14,400 unique sets, 0 LEAK) was synthesized from the 7/19
15:57 RTL (`masked_sbox_first_order.v` MD5
`32c5a7ed364a6560718294a6fc85372a`, identical to the current bundle
RTL) but the synth result was not preserved in any of the bundle
paths we have today.

To reproduce functional equivalence from the current bundle:
1. `rtl/masked_sbox_first_order.v` (current, MD5 matches 7/19 15:57) +
   `rtl/circuit.v` (7-byte wrapper) +
   `synth/synth_circuit.ys` (or `_v9.ys` for abc -fast)
   -> `synth/prolead/circuit_v9.v` (gate-level, 7-byte randomIn)
2. `synth/config.json` (PROLEAD config, matches 7/19 17:23) +
   `synth/library_yosys.json` (with 7/19 13:37 cell set)
   -> `prolead-d2-experimental` (or `prolead-masked-aes`) Docker image

This reproduces the 7/19 PROLEAD (0/14,400) verdict via the Docker
flow. A bit-exact reproduction of the 7/19 netlist (line-for-line
Verilog equality) is not possible in the current Windows environment
because:
- The current yosys 0.52 emit format leaves `reg [7:0]` declarations in
  the post-synth netlist; the 7/19 macOS-native yosys emitted a cleaner
  gate-level netlist with no `reg` declarations.
- The current synth flow uses `$_XNOR_` cells, which the current
  PROLEAD library does not declare; the 7/19 library used `XNOR`
  cells (which PROLEAD accepted).

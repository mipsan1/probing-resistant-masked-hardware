# Step 4: Yosys Gate-Level Synthesis

Yosys 0.67+ generic-synthesis flow for the first-order (d=1) and
second-order (d=2) masked AES S-box designs.

## Files

| file | purpose |
| --- | --- |
| `synth_first_order.ys`     | Quick synth + stat (no netlist dump) |
| `synth_first_order_full.ys` | Full flow with `write_verilog` |
| `synth_second_order.ys`    | Quick synth + stat (no netlist dump) |
| `synth_second_order_full.ys` | Full flow with `write_verilog` |
| `masked_sbox_first_order_syn.v`  | First-order gate-level netlist (Yosys output) |
| `masked_sbox_second_order_syn.v` | Second-order gate-level netlist (Yosys output) |
| `AREA_REPORT.md` | Cell counts, ratios, equivalence summary |

## How to reproduce

```sh
cd syn/
yosys -s synth_first_order_full.ys
yosys -s synth_second_order_full.ys
```

## Post-synthesis equivalence check

```sh
cd ../rtl/
iverilog -g2012 -I. -o /tmp/sim_syn tb_masked_sbox_exhaustive_syn.v \
    ../syn/masked_sbox_first_order_syn.v \
    ../syn/masked_sbox_second_order_syn.v
/tmp/sim_syn
```

Expected output: `first-order: 256 pass, 0 fail`, `second-order: 256 pass, 0 fail`.

## Synthesis flow details

The Yosys `synth` command runs:

1. `proc` — convert processes to netlists
2. `opt` — peephole optimization
3. `fsm` — finite-state-machine encoding
4. `memory` — map memory primitives
5. `techmap` — technology mapping (to internal `$_*_` cells)
6. `abc -fast` — technology-independent logic synthesis via ABC
7. `opt` — final cleanup
8. `clean` — remove unused cells/wires

The output is a netlist of generic 2-input gates (`$_AND_`, `$_XOR_`,
etc.) — *not* mapped to a specific standard cell library. This is
fine for an academic paper on masking where the design is
portable and the cell count is a fair area proxy.

For an ASIC tape-out one would replace `abc -fast` with a target
library (e.g. `synth -top ... -liberty <sky130.lib>`) and re-run.

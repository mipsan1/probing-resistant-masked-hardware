// =====================================================================
// circuit.v
// =====================================================================
// PROLEAD-compatible top-level wrapper around our masked S-box.
// Maps the (x0, x1) input share pair to PROLEAD's expected
// `sboxIn[15:0]` bus and (y0, y1) output to `sboxOut[15:0]`.  The
// 7 fresh-randomness bytes (six r_01 masks of Algorithm 1 plus one
// operand-refresh byte for mul1) are exposed as a single 56-bit bus
// `randomIn[55:0]` so PROLEAD treats them as one combined group.
//
// This is the file PROLEAD sees; the rest of our design is unchanged
// RTL.  Yosys flattens it down to a single `circuit` module for
// PROLEAD's gate-level analysis.
// =====================================================================

`ifndef CIRCUIT_V
`define CIRCUIT_V

`timescale 1ns/1ps

module circuit (
    input              clk,
    input  [15:0]      sboxIn,
    input  [55:0]      randomIn,
    output [15:0]      sboxOut
);

    // 1. Repack input shares
    wire [7:0] x0 = sboxIn[7:0];
    wire [7:0] x1 = sboxIn[15:8];

    // 2. Repack 7 random bytes (6 x r_01 + 1 operand refresh)
    wire [7:0] r0  = randomIn[  0 +: 8];
    wire [7:0] r1  = randomIn[  8 +: 8];
    wire [7:0] r2  = randomIn[ 16 +: 8];
    wire [7:0] r3  = randomIn[ 24 +: 8];
    wire [7:0] r4  = randomIn[ 32 +: 8];
    wire [7:0] r5  = randomIn[ 40 +: 8];
    wire [7:0] r6  = randomIn[ 48 +: 8];

    wire       v_in;
    wire       v_out;
    wire [7:0] y0, y1;

    // 3. The actual masked S-box instance
    masked_sbox_first_order u_sbox (
        .clk(clk),
        .rst_n(1'b1),
        .valid_in(1'b1),
        .x0_in(x0),
        .x1_in(x1),
        .r0_in (r0),  .r1_in (r1),  .r2_in (r2),
        .r3_in (r3),  .r4_in (r4),  .r5_in (r5),
        .r6_in (r6),
        .valid_out(v_out),
        .y0_out(y0),
        .y1_out(y1)
    );

    // 4. Output share packing
    assign sboxOut[7:0]  = y0;
    assign sboxOut[15:8] = y1;

    // Tie off unused internal signals (avoid PROLEAD unused-signal errors)
    assign v_in  = 1'b0;

endmodule

`endif

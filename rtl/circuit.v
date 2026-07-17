// =====================================================================
// circuit.v
// =====================================================================
// PROLEAD-compatible top-level wrapper around our masked S-box.
// Maps the (x0, x1) input share pair to PROLEAD's expected
// `sboxIn[15:0]` bus and (y0, y1) output to `sboxOut[15:0]`.  The
// 28 fresh-randomness bytes are exposed as a single 224-bit bus
// `randomIn[223:0]` so PROLEAD treats them as one combined group.
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
    input  [223:0]     randomIn,
    output [15:0]      sboxOut
);

    // 1. Repack input shares
    wire [7:0] x0 = sboxIn[7:0];
    wire [7:0] x1 = sboxIn[15:8];

    // 2. Repack 28 random bytes
    wire [7:0] r0  = randomIn[  0 +: 8];
    wire [7:0] r1  = randomIn[  8 +: 8];
    wire [7:0] r2  = randomIn[ 16 +: 8];
    wire [7:0] r3  = randomIn[ 24 +: 8];
    wire [7:0] r4  = randomIn[ 32 +: 8];
    wire [7:0] r5  = randomIn[ 40 +: 8];
    wire [7:0] r6  = randomIn[ 48 +: 8];
    wire [7:0] r7  = randomIn[ 56 +: 8];
    wire [7:0] r8  = randomIn[ 64 +: 8];
    wire [7:0] r9  = randomIn[ 72 +: 8];
    wire [7:0] r10 = randomIn[ 80 +: 8];
    wire [7:0] r11 = randomIn[ 88 +: 8];
    wire [7:0] r12 = randomIn[ 96 +: 8];
    wire [7:0] r13 = randomIn[104 +: 8];
    wire [7:0] r14 = randomIn[112 +: 8];
    wire [7:0] r15 = randomIn[120 +: 8];
    wire [7:0] r16 = randomIn[128 +: 8];
    wire [7:0] r17 = randomIn[136 +: 8];
    wire [7:0] r18 = randomIn[144 +: 8];
    wire [7:0] r19 = randomIn[152 +: 8];
    wire [7:0] r20 = randomIn[160 +: 8];
    wire [7:0] r21 = randomIn[168 +: 8];
    wire [7:0] r22 = randomIn[176 +: 8];
    wire [7:0] r23 = randomIn[184 +: 8];
    wire [7:0] r24 = randomIn[192 +: 8];
    wire [7:0] r25 = randomIn[200 +: 8];
    wire [7:0] r26 = randomIn[208 +: 8];
    wire [7:0] r27 = randomIn[216 +: 8];

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
        .r0_in (r0),  .r1_in (r1),  .r2_in (r2),  .r3_in (r3),
        .r4_in (r4),  .r5_in (r5),  .r6_in (r6),  .r7_in (r7),
        .r8_in (r8),  .r9_in (r9),  .r10_in(r10), .r11_in(r11),
        .r12_in(r12), .r13_in(r13), .r14_in(r14), .r15_in(r15),
        .r16_in(r16), .r17_in(r17), .r18_in(r18), .r19_in(r19),
        .r20_in(r20), .r21_in(r21), .r22_in(r22), .r23_in(r23),
        .r24_in(r24), .r25_in(r25), .r26_in(r26), .r27_in(r27),
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

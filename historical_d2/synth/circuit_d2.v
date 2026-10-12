// =====================================================================
// circuit_d2.v
// =====================================================================
// PROLEAD-compatible top-level wrapper around the second-order (3-share)
// masked S-box.  Mirrors rtl/circuit.v (d=1) exactly:
//   - input shares  (x0, x1, x2) -> sboxIn[23:0]
//   - output shares (y0, y1, y2) -> sboxOut[23:0]
//   - 19 fresh-randomness bytes (6 multiplications x 3 cross-term bytes
//     r01/r02/r12 + 1 operand-refresh byte r18) exposed as one 152-bit
//     bus randomIn[151:0] so PROLEAD treats them as one combined group.
// =====================================================================

`ifndef CIRCUIT_D2_V
`define CIRCUIT_D2_V

`timescale 1ns/1ps

module circuit (
    input              clk,
    input  [23:0]      sboxIn,
    input  [151:0]     randomIn,
    output [23:0]      sboxOut
);

    // 1. Repack input shares
    wire [7:0] x0 = sboxIn[7:0];
    wire [7:0] x1 = sboxIn[15:8];
    wire [7:0] x2 = sboxIn[23:16];

    // 2. Repack 19 random bytes
    wire [7:0] r0  = randomIn[   0 +: 8];  // mul1 r_01
    wire [7:0] r1  = randomIn[   8 +: 8];  // mul1 r_02
    wire [7:0] r2  = randomIn[  16 +: 8];  // mul1 r_12
    wire [7:0] r3  = randomIn[  24 +: 8];  // mul2 r_01
    wire [7:0] r4  = randomIn[  32 +: 8];  // mul2 r_02
    wire [7:0] r5  = randomIn[  40 +: 8];  // mul2 r_12
    wire [7:0] r6  = randomIn[  48 +: 8];  // mul3 r_01
    wire [7:0] r7  = randomIn[  56 +: 8];  // mul3 r_02
    wire [7:0] r8  = randomIn[  64 +: 8];  // mul3 r_12
    wire [7:0] r9  = randomIn[  72 +: 8];  // mul4 r_01
    wire [7:0] r10 = randomIn[  80 +: 8];  // mul4 r_02
    wire [7:0] r11 = randomIn[  88 +: 8];  // mul4 r_12
    wire [7:0] r12 = randomIn[  96 +: 8];  // mul5 r_01
    wire [7:0] r13 = randomIn[ 104 +: 8];  // mul5 r_02
    wire [7:0] r14 = randomIn[ 112 +: 8];  // mul5 r_12
    wire [7:0] r15 = randomIn[ 120 +: 8];  // inv  r_01
    wire [7:0] r16 = randomIn[ 128 +: 8];  // inv  r_02
    wire [7:0] r17 = randomIn[ 136 +: 8];  // inv  r_12
    wire [7:0] r18 = randomIn[ 144 +: 8];  // mul1 operand refresh (x^4 path)

    wire       v_in;
    wire       v_out;
    wire [7:0] y0, y1, y2;

    // 3. The actual masked S-box instance (second order)
    masked_sbox_second_order u_sbox (
        .clk(clk),
        .rst_n(1'b1),
        .valid_in(1'b1),
        .x0_in(x0),
        .x1_in(x1),
        .x2_in(x2),
        .r0_in (r0),  .r1_in (r1),  .r2_in (r2),
        .r3_in (r3),  .r4_in (r4),  .r5_in (r5),
        .r6_in (r6),  .r7_in (r7),  .r8_in (r8),
        .r9_in (r9),  .r10_in(r10), .r11_in(r11),
        .r12_in(r12), .r13_in(r13), .r14_in(r14),
        .r15_in(r15), .r16_in(r16), .r17_in(r17),
        .r18_in(r18),
        .valid_out(v_out),
        .y0_out(y0),
        .y1_out(y1),
        .y2_out(y2)
    );

    // 4. Output share packing
    assign sboxOut[7:0]   = y0;
    assign sboxOut[15:8]  = y1;
    assign sboxOut[23:16] = y2;

    // Tie off unused internal signals (avoid PROLEAD unused-signal errors)
    assign v_in  = 1'b0;

endmodule

`endif

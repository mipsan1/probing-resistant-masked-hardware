// =====================================================================
// circuit_d2_nomask.v
// =====================================================================
// PC-G: structurally identical to circuit_d2.v EXCEPT every mask byte
// r0..r18 is tied to 8'h00.  This removes the masking barrier without
// changing the share-decomposition wiring; if mask reuse / share
// independence is the only thing keeping the masked d=2 design silent,
// this wrapper should flag as LEAK in the same way the unmasked d=1
// design (1,224/1,890 at 512k) flagged.
// =====================================================================

`ifndef CIRCUIT_D2_NOMASK_V
`define CIRCUIT_D2_NOMASK_V

`timescale 1ns/1ps

module circuit (
    input              clk,
    input  [23:0]      sboxIn,
    input  [151:0]     randomIn,    // unused but kept for PROLEAD interface
    output [23:0]      sboxOut
);

    wire [7:0] x0 = sboxIn[7:0];
    wire [7:0] x1 = sboxIn[15:8];
    wire [7:0] x2 = sboxIn[23:16];

    // Tie all 19 mask bytes to 8'h00 (masking barrier removed).
    // randomIn is still 152-bit to keep the PROLEAD-top interface
    // identical to circuit_d2.v; we just don't connect it through.
    wire [7:0] r0  = 8'h00;
    wire [7:0] r1  = 8'h00;
    wire [7:0] r2  = 8'h00;
    wire [7:0] r3  = 8'h00;
    wire [7:0] r4  = 8'h00;
    wire [7:0] r5  = 8'h00;
    wire [7:0] r6  = 8'h00;
    wire [7:0] r7  = 8'h00;
    wire [7:0] r8  = 8'h00;
    wire [7:0] r9  = 8'h00;
    wire [7:0] r10 = 8'h00;
    wire [7:0] r11 = 8'h00;
    wire [7:0] r12 = 8'h00;
    wire [7:0] r13 = 8'h00;
    wire [7:0] r14 = 8'h00;
    wire [7:0] r15 = 8'h00;
    wire [7:0] r16 = 8'h00;
    wire [7:0] r17 = 8'h00;
    wire [7:0] r18 = 8'h00;

    wire       v_out;
    wire [7:0] y0, y1, y2;

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

    assign sboxOut[7:0]   = y0;
    assign sboxOut[15:8]  = y1;
    assign sboxOut[23:16] = y2;
endmodule

`endif

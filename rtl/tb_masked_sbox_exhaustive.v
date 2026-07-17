// =====================================================================
// tb_masked_sbox_exhaustive.v
// Exhaustive (256-input) self-checking testbench for masked_sbox_first_order
// and masked_sbox_second_order.
//
// For every byte x in 0..255:
//   1. Generate a fresh (d+1)-sharing of x using the LFSR.
//   2. Drive the shares into the DUT and assert valid_in for 1 cycle.
//   3. Wait for valid_out (pipeline depth ~10 cycles).
//   4. Reconstruct the secret (XOR all shares) and compare to
//      the FIPS-197 AES S-box value.
// =====================================================================

`ifndef TB_MASKED_SBOX_EXHAUSTIVE_V
`define TB_MASKED_SBOX_EXHAUSTIVE_V

`timescale 1ns/1ps

`include "masked_sbox_pkg.v"

module tb_masked_sbox_exhaustive;

  // ------------------------------------------------------------------
  // 32-bit maximal-length LFSR (x^32 + x^22 + x^2 + x + 1) for
  // reproducible random share generation.
  // ------------------------------------------------------------------
  reg [31:0] lfsr;
  function [7:0] next_random;
    input dummy;
    begin
      lfsr = {lfsr[30:0],
              lfsr[31] ^ lfsr[21] ^ lfsr[1] ^ lfsr[0]};
      next_random = lfsr[7:0];
    end
  endfunction

  // ------------------------------------------------------------------
  // Reference AES S-box (combinational function inside the testbench).
  //   sbox(x) = aes_affine(gf_inv(x))
  //   gf_inv(0) = 0 by convention.
  // ------------------------------------------------------------------
  function [7:0] ref_sbox;
    input [7:0] x;
    reg [7:0] inv;
    reg [7:0] y;
    integer r;
    begin
      inv = masked_sbox_pkg::gf_inv_byte(x);
      y = 8'h00;
      for (r = 0; r < 8; r = r + 1) begin
        y[r] = inv[r] ^ inv[(r + 4) % 8] ^ inv[(r + 5) % 8]
                       ^ inv[(r + 6) % 8] ^ inv[(r + 7) % 8];
      end
      ref_sbox = y ^ 8'h63;
    end
  endfunction

  // ------------------------------------------------------------------
  // Clock and reset
  // ------------------------------------------------------------------
  reg clk;
  reg rst_n;
  initial clk = 1'b0;
  always #5 clk = ~clk;  // 100 MHz

  // ------------------------------------------------------------------
  // First-order DUT
  // ------------------------------------------------------------------
  reg valid_in_1;
  reg [7:0] x0_1, x1_1;
  reg [7:0] r0_1, r1_1, r2_1, r3_1, r4_1, r5_1;
  reg [7:0] r6_1, r7_1, r8_1, r9_1, r10_1, r11_1;
  reg [7:0] r12_1, r13_1, r14_1, r15_1, r16_1, r17_1;
  reg [7:0] r18_1, r19_1, r20_1, r21_1, r22_1, r23_1;
  reg [7:0] r24_1, r25_1, r26_1, r27_1;
  wire valid_out_1;
  wire [7:0] y0_1, y1_1;

  masked_sbox_first_order dut1 (
      .clk(clk),
      .rst_n(rst_n),
      .valid_in(valid_in_1),
      .x0_in(x0_1), .x1_in(x1_1),
      .r0_in(r0_1), .r1_in(r1_1), .r2_in(r2_1), .r3_in(r3_1),
      .r4_in(r4_1), .r5_in(r5_1), .r6_in(r6_1), .r7_in(r7_1),
      .r8_in(r8_1), .r9_in(r9_1), .r10_in(r10_1), .r11_in(r11_1),
      .r12_in(r12_1), .r13_in(r13_1), .r14_in(r14_1), .r15_in(r15_1),
      .r16_in(r16_1), .r17_in(r17_1), .r18_in(r18_1), .r19_in(r19_1),
      .r20_in(r20_1), .r21_in(r21_1), .r22_in(r22_1), .r23_in(r23_1),
      .r24_in(r24_1), .r25_in(r25_1), .r26_in(r26_1), .r27_in(r27_1),
      .valid_out(valid_out_1),
      .y0_out(y0_1), .y1_out(y1_1)
  );

  // ------------------------------------------------------------------
  // Second-order DUT
  // ------------------------------------------------------------------
  reg valid_in_2;
  reg [7:0] x0_2, x1_2, x2_2;
  reg [7:0] r00, r01, r02, r03, r04, r05;
  reg [7:0] r06, r07, r08, r09, r10, r11;
  reg [7:0] r12, r13, r14, r15, r16, r17;
  reg [7:0] r18, r19, r20, r21, r22, r23;
  reg [7:0] r24, r25, r26, r27, r28, r29;
  reg [7:0] r30, r31, r32, r33, r34, r35;
  reg [7:0] r36, r37, r38, r39, r40, r41;
  reg [7:0] r42, r43, r44, r45, r46, r47;
  reg [7:0] r48, r49, r50, r51, r52, r53;
  reg [7:0] r54, r55, r56, r57, r58, r59;
  reg [7:0] r60, r61, r62;
  wire valid_out_2;
  wire [7:0] y0_2, y1_2, y2_2;

  masked_sbox_second_order dut2 (
      .clk(clk),
      .rst_n(rst_n),
      .valid_in(valid_in_2),
      .x0_in(x0_2), .x1_in(x1_2), .x2_in(x2_2),
      .r00(r00), .r01(r01), .r02(r02),
      .r03(r03), .r04(r04), .r05(r05),
      .r06(r06), .r07(r07), .r08(r08),
      .r09(r09), .r10(r10), .r11(r11),
      .r12(r12), .r13(r13), .r14(r14),
      .r15(r15), .r16(r16), .r17(r17),
      .r18(r18), .r19(r19), .r20(r20),
      .r21(r21), .r22(r22), .r23(r23),
      .r24(r24), .r25(r25), .r26(r26),
      .r27(r27), .r28(r28), .r29(r29),
      .r30(r30), .r31(r31), .r32(r32),
      .r33(r33), .r34(r34), .r35(r35),
      .r36(r36), .r37(r37), .r38(r38),
      .r39(r39), .r40(r40), .r41(r41),
      .r42(r42), .r43(r43), .r44(r44),
      .r45(r45), .r46(r46), .r47(r47),
      .r48(r48), .r49(r49), .r50(r50),
      .r51(r51), .r52(r52), .r53(r53),
      .r54(r54), .r55(r55), .r56(r56),
      .r57(r57), .r58(r58), .r59(r59),
      .r60(r60), .r61(r61), .r62(r62),
      .valid_out(valid_out_2),
      .y0_out(y0_2), .y1_out(y1_2), .y2_out(y2_2)
  );

  // ------------------------------------------------------------------
  // Stimulus: 256 inputs, both DUTs
  // ------------------------------------------------------------------
  integer i;
  integer pass1, fail1, pass2, fail2;
  reg [7:0] sec, s0, s1, s2, expected;
  reg [7:0] in_flight_1, in_flight_2;
  reg seen_valid_1, seen_valid_2;

  initial begin
    pass1 = 0; fail1 = 0;
    pass2 = 0; fail2 = 0;
    in_flight_1 = 8'h00; in_flight_2 = 8'h00;
    seen_valid_1 = 1'b0; seen_valid_2 = 1'b0;
    lfsr = 32'hDEADBEEF;
    rst_n = 1'b0;
    valid_in_1 = 1'b0;
    valid_in_2 = 1'b0;
    #20 rst_n = 1'b1;

    for (i = 0; i < 256; i = i + 1) begin
      sec = i[7:0];
      expected = ref_sbox(sec);

      // ---- First-order: s0 ^ s1 = sec ----
      s0 = next_random(1'b0);
      s1 = sec ^ s0;
      x0_1 = s0;  x1_1 = s1;
      r0_1  = next_random(1'b0);  r1_1  = next_random(1'b0);
      r2_1  = next_random(1'b0);  r3_1  = next_random(1'b0);
      r4_1  = next_random(1'b0);  r5_1  = next_random(1'b0);
      r6_1  = next_random(1'b0);  r7_1  = next_random(1'b0);
      r8_1  = next_random(1'b0);  r9_1  = next_random(1'b0);
      r10_1 = next_random(1'b0);  r11_1 = next_random(1'b0);
      r12_1 = next_random(1'b0);  r13_1 = next_random(1'b0);
      r14_1 = next_random(1'b0);  r15_1 = next_random(1'b0);
      r16_1 = next_random(1'b0);  r17_1 = next_random(1'b0);
      r18_1 = next_random(1'b0);  r19_1 = next_random(1'b0);
      r20_1 = next_random(1'b0);  r21_1 = next_random(1'b0);
      r22_1 = next_random(1'b0);  r23_1 = next_random(1'b0);
      r24_1 = next_random(1'b0);  r25_1 = next_random(1'b0);
      r26_1 = next_random(1'b0);  r27_1 = next_random(1'b0);

      in_flight_1 = sec;
      seen_valid_1 = 1'b0;
      @(negedge clk);
      valid_in_1 = 1'b1;
      @(negedge clk);
      valid_in_1 = 1'b0;

      // wait for valid_out_1
      forever begin
        @(posedge clk);
        if (valid_out_1 && !seen_valid_1) begin
          seen_valid_1 = 1'b1;
          if ((y0_1 ^ y1_1) !== expected) begin
            $display("FAIL first-order: input=0x%02h expected=0x%02h got=0x%02h (y0=0x%02h y1=0x%02h)",
                     in_flight_1, expected, y0_1 ^ y1_1, y0_1, y1_1);
            fail1 = fail1 + 1;
          end else begin
            pass1 = pass1 + 1;
          end
          // one extra cycle to clear valid
          @(posedge clk);
          break;
        end
      end

      // ---- Second-order: s0 ^ s1 ^ s2 = sec ----
      s0 = next_random(1'b0);
      s1 = next_random(1'b0);
      s2 = sec ^ s0 ^ s1;
      x0_2 = s0;  x1_2 = s1;  x2_2 = s2;
      r00 = next_random(1'b0); r01 = next_random(1'b0); r02 = next_random(1'b0);
      r03 = next_random(1'b0); r04 = next_random(1'b0); r05 = next_random(1'b0);
      r06 = next_random(1'b0); r07 = next_random(1'b0); r08 = next_random(1'b0);
      r09 = next_random(1'b0); r10 = next_random(1'b0); r11 = next_random(1'b0);
      r12 = next_random(1'b0); r13 = next_random(1'b0); r14 = next_random(1'b0);
      r15 = next_random(1'b0); r16 = next_random(1'b0); r17 = next_random(1'b0);
      r18 = next_random(1'b0); r19 = next_random(1'b0); r20 = next_random(1'b0);
      r21 = next_random(1'b0); r22 = next_random(1'b0); r23 = next_random(1'b0);
      r24 = next_random(1'b0); r25 = next_random(1'b0); r26 = next_random(1'b0);
      r27 = next_random(1'b0); r28 = next_random(1'b0); r29 = next_random(1'b0);
      r30 = next_random(1'b0); r31 = next_random(1'b0); r32 = next_random(1'b0);
      r33 = next_random(1'b0); r34 = next_random(1'b0); r35 = next_random(1'b0);
      r36 = next_random(1'b0); r37 = next_random(1'b0); r38 = next_random(1'b0);
      r39 = next_random(1'b0); r40 = next_random(1'b0); r41 = next_random(1'b0);
      r42 = next_random(1'b0); r43 = next_random(1'b0); r44 = next_random(1'b0);
      r45 = next_random(1'b0); r46 = next_random(1'b0); r47 = next_random(1'b0);
      r48 = next_random(1'b0); r49 = next_random(1'b0); r50 = next_random(1'b0);
      r51 = next_random(1'b0); r52 = next_random(1'b0); r53 = next_random(1'b0);
      r54 = next_random(1'b0); r55 = next_random(1'b0); r56 = next_random(1'b0);
      r57 = next_random(1'b0); r58 = next_random(1'b0); r59 = next_random(1'b0);
      r60 = next_random(1'b0); r61 = next_random(1'b0); r62 = next_random(1'b0);

      in_flight_2 = sec;
      seen_valid_2 = 1'b0;
      @(negedge clk);
      valid_in_2 = 1'b1;
      @(negedge clk);
      valid_in_2 = 1'b0;

      forever begin
        @(posedge clk);
        if (valid_out_2 && !seen_valid_2) begin
          seen_valid_2 = 1'b1;
          if ((y0_2 ^ y1_2 ^ y2_2) !== expected) begin
            $display("FAIL second-order: input=0x%02h expected=0x%02h got=0x%02h (y0=0x%02h y1=0x%02h y2=0x%02h)",
                     in_flight_2, expected, y0_2 ^ y1_2 ^ y2_2, y0_2, y1_2, y2_2);
            fail2 = fail2 + 1;
          end else begin
            pass2 = pass2 + 1;
          end
          @(posedge clk);
          break;
        end
      end
    end

    $display("=================================================");
    $display("  Exhaustive test (256 inputs x 2 DUTs):");
    $display("    first-order:  %0d pass, %0d fail", pass1, fail1);
    $display("    second-order: %0d pass, %0d fail", pass2, fail2);
    $display("=================================================");
    if ((fail1 != 0) || (fail2 != 0)) $fatal;
    $finish;
  end

  // Safety watchdog
  initial begin
    #1000000;
    $display("TIMEOUT");
    $fatal;
  end

endmodule

`endif

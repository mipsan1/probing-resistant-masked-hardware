// =====================================================================
// tb_power_sim_d2.v
// Gate-level power simulation for the SECOND-ORDER masked S-box.
// Same idea as tb_power_sim.v, but the d=2 design has 35 DFFs:
//   10 valid_pipe + 8*3 output shares + 1 valid_out = 35
// =====================================================================

`timescale 1ns/1ps

module tb_power_sim_d2;

  parameter N_TRIPLES = 10000;

  reg clk;
  reg rst_n;
  reg valid_in;
  reg [7:0] x0_in, x1_in, x2_in;
  reg [7:0] r00, r01, r02, r03, r04, r05, r06, r07, r08, r09;
  reg [7:0] r10, r11, r12, r13, r14, r15, r16, r17, r18, r19;
  reg [7:0] r20, r21, r22, r23, r24, r25, r26, r27, r28, r29;
  reg [7:0] r30, r31, r32, r33, r34, r35, r36, r37, r38, r39;
  reg [7:0] r40, r41, r42, r43, r44, r45, r46, r47, r48, r49;
  reg [7:0] r50, r51, r52, r53, r54, r55, r56, r57, r58, r59;
  reg [7:0] r60, r61, r62;
  wire valid_out;
  wire [7:0] y0_out, y1_out, y2_out;

  masked_sbox_second_order dut (
      .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
      .x0_in(x0_in), .x1_in(x1_in), .x2_in(x2_in),
      .r00(r00), .r01(r01), .r02(r02), .r03(r03), .r04(r04),
      .r05(r05), .r06(r06), .r07(r07), .r08(r08), .r09(r09),
      .r10(r10), .r11(r11), .r12(r12), .r13(r13), .r14(r14),
      .r15(r15), .r16(r16), .r17(r17), .r18(r18), .r19(r19),
      .r20(r20), .r21(r21), .r22(r22), .r23(r23), .r24(r24),
      .r25(r25), .r26(r26), .r27(r27), .r28(r28), .r29(r29),
      .r30(r30), .r31(r31), .r32(r32), .r33(r33), .r34(r34),
      .r35(r35), .r36(r36), .r37(r37), .r38(r38), .r39(r39),
      .r40(r40), .r41(r41), .r42(r42), .r43(r43), .r44(r44),
      .r45(r45), .r46(r46), .r47(r47), .r48(r48), .r49(r49),
      .r50(r50), .r51(r51), .r52(r52), .r53(r53), .r54(r54),
      .r55(r55), .r56(r56), .r57(r57), .r58(r58), .r59(r59),
      .r60(r60), .r61(r61), .r62(r62),
      .valid_out(valid_out),
      .y0_out(y0_out), .y1_out(y1_out), .y2_out(y2_out)
  );

  reg [31:0] lfsr;
  function [7:0] next_random;
    input dummy;
    begin
      lfsr = {lfsr[30:0],
              lfsr[31] ^ lfsr[21] ^ lfsr[1] ^ lfsr[0]};
      next_random = lfsr[7:0];
    end
  endfunction

  integer power_fd;
  integer header_fd;

  reg [7:0] s0, s1, s2;
  integer t;

  reg [34:0] prev_dff;
  reg [34:0] curr_dff;
  integer cycle_idx;
  integer hd;
  integer kk;

  initial begin
    prev_dff = 35'b0;
    cycle_idx = 0;
  end

  always @(posedge clk) begin
    curr_dff[0]  = dut.valid_pipe[0];
    curr_dff[1]  = dut.valid_pipe[1];
    curr_dff[2]  = dut.valid_pipe[2];
    curr_dff[3]  = dut.valid_pipe[3];
    curr_dff[4]  = dut.valid_pipe[4];
    curr_dff[5]  = dut.valid_pipe[5];
    curr_dff[6]  = dut.valid_pipe[6];
    curr_dff[7]  = dut.valid_pipe[7];
    curr_dff[8]  = dut.valid_pipe[8];
    curr_dff[9]  = dut.valid_pipe[9];
    curr_dff[10] = dut.y0_out[0];
    curr_dff[11] = dut.y0_out[1];
    curr_dff[12] = dut.y0_out[2];
    curr_dff[13] = dut.y0_out[3];
    curr_dff[14] = dut.y0_out[4];
    curr_dff[15] = dut.y0_out[5];
    curr_dff[16] = dut.y0_out[6];
    curr_dff[17] = dut.y0_out[7];
    curr_dff[18] = dut.y1_out[0];
    curr_dff[19] = dut.y1_out[1];
    curr_dff[20] = dut.y1_out[2];
    curr_dff[21] = dut.y1_out[3];
    curr_dff[22] = dut.y1_out[4];
    curr_dff[23] = dut.y1_out[5];
    curr_dff[24] = dut.y1_out[6];
    curr_dff[25] = dut.y1_out[7];
    curr_dff[26] = dut.y2_out[0];
    curr_dff[27] = dut.y2_out[1];
    curr_dff[28] = dut.y2_out[2];
    curr_dff[29] = dut.y2_out[3];
    curr_dff[30] = dut.y2_out[4];
    curr_dff[31] = dut.y2_out[5];
    curr_dff[32] = dut.y2_out[6];
    curr_dff[33] = dut.y2_out[7];
    curr_dff[34] = dut.valid_out;
    hd = 0;
    for (kk = 0; kk < 35; kk = kk + 1)
      hd = hd + curr_dff[kk] ^ prev_dff[kk];
    $fwrite(power_fd, "%0d %0d\n", cycle_idx, hd);
    cycle_idx = cycle_idx + 1;
    prev_dff <= curr_dff;
  end

  initial begin
    clk = 0;
    rst_n = 0;
    valid_in = 0;
    x0_in = 0; x1_in = 0; x2_in = 0;
    {r00, r01, r02, r03, r04, r05, r06, r07, r08, r09,
     r10, r11, r12, r13, r14, r15, r16, r17, r18, r19,
     r20, r21, r22, r23, r24, r25, r26, r27, r28, r29,
     r30, r31, r32, r33, r34, r35, r36, r37, r38, r39,
     r40, r41, r42, r43, r44, r45, r46, r47, r48, r49,
     r50, r51, r52, r53, r54, r55, r56, r57, r58, r59,
     r60, r61, r62} = 0;
    lfsr = 32'hDEADBEEF;

    power_fd = $fopen("/tmp/d2_power.txt", "w");
    header_fd = $fopen("/tmp/d2_power_header.txt", "w");
    if (power_fd == 0 || header_fd == 0) begin
      $display("ERROR: cannot open power/header file");
      $finish;
    end
    $fwrite(header_fd, "# secret s0 s1 s2 first_cycle_of_this_triple\n");

    #20 rst_n = 1;

    for (t = 0; t < N_TRIPLES; t = t + 1) begin
      s0 = next_random(1'b0);
      s1 = next_random(1'b0);
      s2 = next_random(1'b0);
      x0_in = s0; x1_in = s1; x2_in = s2;
      r00 = next_random(1'b0); r01 = next_random(1'b0);
      r02 = next_random(1'b0); r03 = next_random(1'b0);
      r04 = next_random(1'b0); r05 = next_random(1'b0);
      r06 = next_random(1'b0); r07 = next_random(1'b0);
      r08 = next_random(1'b0); r09 = next_random(1'b0);
      r10 = next_random(1'b0); r11 = next_random(1'b0);
      r12 = next_random(1'b0); r13 = next_random(1'b0);
      r14 = next_random(1'b0); r15 = next_random(1'b0);
      r16 = next_random(1'b0); r17 = next_random(1'b0);
      r18 = next_random(1'b0); r19 = next_random(1'b0);
      r20 = next_random(1'b0); r21 = next_random(1'b0);
      r22 = next_random(1'b0); r23 = next_random(1'b0);
      r24 = next_random(1'b0); r25 = next_random(1'b0);
      r26 = next_random(1'b0); r27 = next_random(1'b0);
      r28 = next_random(1'b0); r29 = next_random(1'b0);
      r30 = next_random(1'b0); r31 = next_random(1'b0);
      r32 = next_random(1'b0); r33 = next_random(1'b0);
      r34 = next_random(1'b0); r35 = next_random(1'b0);
      r36 = next_random(1'b0); r37 = next_random(1'b0);
      r38 = next_random(1'b0); r39 = next_random(1'b0);
      r40 = next_random(1'b0); r41 = next_random(1'b0);
      r42 = next_random(1'b0); r43 = next_random(1'b0);
      r44 = next_random(1'b0); r45 = next_random(1'b0);
      r46 = next_random(1'b0); r47 = next_random(1'b0);
      r48 = next_random(1'b0); r49 = next_random(1'b0);
      r50 = next_random(1'b0); r51 = next_random(1'b0);
      r52 = next_random(1'b0); r53 = next_random(1'b0);
      r54 = next_random(1'b0); r55 = next_random(1'b0);
      r56 = next_random(1'b0); r57 = next_random(1'b0);
      r58 = next_random(1'b0); r59 = next_random(1'b0);
      r60 = next_random(1'b0); r61 = next_random(1'b0);
      r62 = next_random(1'b0);

      $fwrite(header_fd, "%02h %02h %02h %02h %0d\n",
              s0 ^ s1 ^ s2, s0, s1, s2, cycle_idx);

      @(negedge clk);
      valid_in = 1'b1;
      @(negedge clk);
      valid_in = 1'b0;
      repeat (15) @(posedge clk);
    end

    $fclose(power_fd);
    $fclose(header_fd);
    $display("Done. %0d triples, %0d cycles total.", N_TRIPLES, cycle_idx);
    $finish;
  end

  always #5 clk = ~clk;

  initial begin
    #(N_TRIPLES * 200 + 100000);
    $display("TIMEOUT");
    $fatal;
  end

endmodule

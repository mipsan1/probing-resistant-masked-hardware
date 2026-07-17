// =====================================================================
// tb_power_sim.v
// Gate-level power simulation testbench. Drives the first-order
// masked S-box with N random input triples, dumps VCD for all
// internal wires, AND records per-cycle switching activity (number
// of DFF bits that toggled between consecutive cycles).
//
// Output files:
//   /tmp/fo_power.vcd   - VCD dump of the entire DUT
//   /tmp/fo_power.txt   - one row per clock edge: cycle_index hd
//                         (hd = number of DFF bits that toggled)
//   /tmp/fo_power_header.txt - one row per input triple
// =====================================================================

`timescale 1ns/1ps

module tb_power_sim;

  parameter N_TRIPLES = 10000;

  reg clk;
  reg rst_n;
  reg valid_in;
  reg [7:0] x0_in, x1_in;
  reg [7:0] r0_in, r1_in, r2_in, r3_in;
  reg [7:0] r4_in, r5_in, r6_in, r7_in;
  reg [7:0] r8_in, r9_in, r10_in, r11_in;
  reg [7:0] r12_in, r13_in, r14_in, r15_in;
  reg [7:0] r16_in, r17_in, r18_in, r19_in;
  reg [7:0] r20_in, r21_in, r22_in, r23_in;
  reg [7:0] r24_in, r25_in, r26_in, r27_in;
  wire valid_out;
  wire [7:0] y0_out, y1_out;

  masked_sbox_first_order dut (
      .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
      .x0_in(x0_in), .x1_in(x1_in),
      .r0_in(r0_in), .r1_in(r1_in), .r2_in(r2_in), .r3_in(r3_in),
      .r4_in(r4_in), .r5_in(r5_in), .r6_in(r6_in), .r7_in(r7_in),
      .r8_in(r8_in), .r9_in(r9_in), .r10_in(r10_in), .r11_in(r11_in),
      .r12_in(r12_in), .r13_in(r13_in), .r14_in(r14_in), .r15_in(r15_in),
      .r16_in(r16_in), .r17_in(r17_in), .r18_in(r18_in), .r19_in(r19_in),
      .r20_in(r20_in), .r21_in(r21_in), .r22_in(r22_in), .r23_in(r23_in),
      .r24_in(r24_in), .r25_in(r25_in), .r26_in(r26_in), .r27_in(r27_in),
      .valid_out(valid_out),
      .y0_out(y0_out), .y1_out(y1_out)
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

  reg [7:0] s0, s1;
  integer t;

  // ------------------------------------------------------------------
  // VCD dump - commented out for speed; uncomment to dump full VCD
  // ------------------------------------------------------------------
  // initial begin
  //   $dumpfile("/tmp/fo_power.vcd");
  //   $dumpvars(0, tb_power_sim);
  // end

  // ------------------------------------------------------------------
  // Per-cycle switching activity (Hamming distance model)
  //
  // We sample the 27 DFF Q wires at every posedge clk, compute
  // hd[i] = sum over wires of (current[i] XOR prev[i]), and write
  // "cycle_index hd_value" to the power file.
  // ------------------------------------------------------------------
  reg [26:0] prev_dff;
  reg [26:0] curr_dff;
  integer cycle_idx;
  integer hd;
  integer kk;

  initial begin
    prev_dff = 27'b0;
    cycle_idx = 0;
  end

  always @(posedge clk) begin
    // Sample current DFFs
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
    curr_dff[26] = dut.valid_out;
    // Hamming distance
    hd = 0;
    for (kk = 0; kk < 27; kk = kk + 1)
      hd = hd + curr_dff[kk] ^ prev_dff[kk];
    $fwrite(power_fd, "%0d %0d\n", cycle_idx, hd);
    cycle_idx = cycle_idx + 1;
    prev_dff <= curr_dff;
  end

  // ------------------------------------------------------------------
  // Stimulus
  // ------------------------------------------------------------------
  initial begin
    clk = 0;
    rst_n = 0;
    valid_in = 0;
    x0_in = 0; x1_in = 0;
    r0_in = 0; r1_in = 0; r2_in = 0; r3_in = 0;
    r4_in = 0; r5_in = 0; r6_in = 0; r7_in = 0;
    r8_in = 0; r9_in = 0; r10_in = 0; r11_in = 0;
    r12_in = 0; r13_in = 0; r14_in = 0; r15_in = 0;
    r16_in = 0; r17_in = 0; r18_in = 0; r19_in = 0;
    r20_in = 0; r21_in = 0; r22_in = 0; r23_in = 0;
    r24_in = 0; r25_in = 0; r26_in = 0; r27_in = 0;
    lfsr = 32'hCAFEFACE;

    power_fd = $fopen("/tmp/fo_power.txt", "w");
    header_fd = $fopen("/tmp/fo_power_header.txt", "w");
    if (power_fd == 0 || header_fd == 0) begin
      $display("ERROR: cannot open power/header file");
      $finish;
    end
    $fwrite(header_fd, "# secret s0 s1 first_cycle_of_this_triple\n");

    #20 rst_n = 1;

    for (t = 0; t < N_TRIPLES; t = t + 1) begin
      s0 = next_random(1'b0);
      s1 = next_random(1'b0);
      x0_in = s0;
      x1_in = s1;
      r0_in  = next_random(1'b0); r1_in  = next_random(1'b0);
      r2_in  = next_random(1'b0); r3_in  = next_random(1'b0);
      r4_in  = next_random(1'b0); r5_in  = next_random(1'b0);
      r6_in  = next_random(1'b0); r7_in  = next_random(1'b0);
      r8_in  = next_random(1'b0); r9_in  = next_random(1'b0);
      r10_in = next_random(1'b0); r11_in = next_random(1'b0);
      r12_in = next_random(1'b0); r13_in = next_random(1'b0);
      r14_in = next_random(1'b0); r15_in = next_random(1'b0);
      r16_in = next_random(1'b0); r17_in = next_random(1'b0);
      r18_in = next_random(1'b0); r19_in = next_random(1'b0);
      r20_in = next_random(1'b0); r21_in = next_random(1'b0);
      r22_in = next_random(1'b0); r23_in = next_random(1'b0);
      r24_in = next_random(1'b0); r25_in = next_random(1'b0);
      r26_in = next_random(1'b0); r27_in = next_random(1'b0);

      $fwrite(header_fd, "%02h %02h %02h %0d\n",
              s0 ^ s1, s0, s1, cycle_idx);

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

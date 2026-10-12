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
  // LFSR seed as a parameter so long gate-level runs can be split into
  // chunks whose LFSR streams continue exactly (warmup-overlap merge).
  parameter [31:0] LFSR_SEED = 32'hCAFEFACE;

  reg clk;
  reg rst_n;
  reg valid_in;
  reg [7:0] x0_in, x1_in;
  reg [7:0] r0_in, r1_in, r2_in, r3_in, r4_in, r5_in, r6_in;
  wire valid_out;
  wire [7:0] y0_out, y1_out;

  masked_sbox_first_order dut (
      .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
      .x0_in(x0_in), .x1_in(x1_in),
      .r0_in(r0_in), .r1_in(r1_in), .r2_in(r2_in),
      .r3_in(r3_in), .r4_in(r4_in), .r5_in(r5_in),
      .r6_in(r6_in),
      .valid_out(valid_out),
      .y0_out(y0_out), .y1_out(y1_out)
  );

  reg [31:0] lfsr;
  // NOTE (rerun fix): the original version advanced the LFSR only ONE
  // shift per byte, so consecutive "random" bytes were a sliding window
  // sharing 7 of 8 bits (measured I(s0;s1)=6.999 bits).  That stimulus
  // degeneracy produced phantom share-MI at the output registers.  We now
  // advance 8 shifts per byte (same seeds, still fully deterministic).
  function [7:0] next_random;
    input dummy;
    integer sh;
    begin
      for (sh = 0; sh < 8; sh = sh + 1)
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
  // We sample the 34 DFF Q wires (17-bit valid_pipe + y0_out + y1_out
  // + valid_out) at every posedge clk, compute
  // hd[i] = sum over wires of (current[i] XOR prev[i]), and write
  // "cycle_index hd_value" to the power file.
  // ------------------------------------------------------------------
  reg [33:0] prev_dff;
  reg [33:0] curr_dff;
  integer cycle_idx;
  integer hd;
  integer kk;

  initial begin
    prev_dff = 34'b0;
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
    curr_dff[10] = dut.valid_pipe[10];
    curr_dff[11] = dut.valid_pipe[11];
    curr_dff[12] = dut.valid_pipe[12];
    curr_dff[13] = dut.valid_pipe[13];
    curr_dff[14] = dut.valid_pipe[14];
    curr_dff[15] = dut.valid_pipe[15];
    curr_dff[16] = dut.valid_pipe[16];
    curr_dff[17] = dut.y0_out[0];
    curr_dff[18] = dut.y0_out[1];
    curr_dff[19] = dut.y0_out[2];
    curr_dff[20] = dut.y0_out[3];
    curr_dff[21] = dut.y0_out[4];
    curr_dff[22] = dut.y0_out[5];
    curr_dff[23] = dut.y0_out[6];
    curr_dff[24] = dut.y0_out[7];
    curr_dff[25] = dut.y1_out[0];
    curr_dff[26] = dut.y1_out[1];
    curr_dff[27] = dut.y1_out[2];
    curr_dff[28] = dut.y1_out[3];
    curr_dff[29] = dut.y1_out[4];
    curr_dff[30] = dut.y1_out[5];
    curr_dff[31] = dut.y1_out[6];
    curr_dff[32] = dut.y1_out[7];
    curr_dff[33] = dut.valid_out;
    // Hamming distance
    hd = 0;
    for (kk = 0; kk < 34; kk = kk + 1)
      hd = hd + (curr_dff[kk] ^ prev_dff[kk]);
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
    r4_in = 0; r5_in = 0; r6_in = 0;
    lfsr = LFSR_SEED;

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
      r6_in  = next_random(1'b0);

      $fwrite(header_fd, "%02h %02h %02h %0d\n",
              s0 ^ s1, s0, s1, cycle_idx);

      @(negedge clk);
      valid_in = 1'b1;
      @(negedge clk);
      valid_in = 1'b0;
      // 17-cycle S-box latency + margin (let the pipeline clear)
      repeat (22) @(posedge clk);
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

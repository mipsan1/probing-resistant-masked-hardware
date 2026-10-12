// =====================================================================
// tb_power_sim_unmasked.v
// POSITIVE CONTROL testbench: drives the deliberately UNPROTECTED
// unmasked_sbox with the same stimulus structure, the same HD metric
// (fixed parenthesised formula), and the same monitor methodology
// (posedge sampling of the monitored DFFs) as tb_power_sim.v.
//
// Monitored DFFs (19): valid_pipe[0..9], y_out[0..7], valid_out.
//
// Output files:
//   /tmp/uc_power.txt        - one row per posedge: cycle_index hd
//   /tmp/uc_power_header.txt - one row per input triple
//                              "# secret s0 s1 first_cycle_of_this_triple"
//   /tmp/uc_trace.txt        - one 19-char binary row per posedge
//                              (same layout as tb_probe_sim trace files)
// =====================================================================

`timescale 1ns/1ps

module tb_power_sim_unmasked;

  parameter N_TRIPLES = 10000;

  reg clk;
  reg rst_n;
  reg valid_in;
  reg [7:0] x_in;
  wire valid_out;
  wire [7:0] y_out;

  unmasked_sbox dut (
      .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
      .x_in(x_in),
      .valid_out(valid_out),
      .y_out(y_out)
  );

  reg [31:0] lfsr;
  // NOTE (rerun fix): advance 8 shifts per byte (was 1) so consecutive
  // bytes are not a 7/8-overlapping sliding window; same seed, still
  // deterministic.  Mirrors the fix in tb_probe_sim.v / tb_power_sim.v.
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
  integer trace_fd;

  reg [7:0] s0, s1;
  integer t;

  // ------------------------------------------------------------------
  // Per-cycle switching activity (Hamming distance model)
  // Sampled at posedge, exactly as in tb_power_sim.v.
  // ------------------------------------------------------------------
  reg [18:0] prev_dff;
  reg [18:0] curr_dff;
  integer cycle_idx;
  integer hd;
  integer kk;

  // Monitored DFF signals, explicit per-bit order (char k of the trace
  // row = wire k): [0..9]=valid_pipe[0..9], [10..17]=y_out[0..7],
  // [18]=valid_out.  At a posedge these read pre-update values,
  // identically in both blocks below (no inter-block race).
  wire [18:0] mon;
  assign mon[0]  = dut.valid_pipe[0];
  assign mon[1]  = dut.valid_pipe[1];
  assign mon[2]  = dut.valid_pipe[2];
  assign mon[3]  = dut.valid_pipe[3];
  assign mon[4]  = dut.valid_pipe[4];
  assign mon[5]  = dut.valid_pipe[5];
  assign mon[6]  = dut.valid_pipe[6];
  assign mon[7]  = dut.valid_pipe[7];
  assign mon[8]  = dut.valid_pipe[8];
  assign mon[9]  = dut.valid_pipe[9];
  assign mon[10] = dut.y_out[0];
  assign mon[11] = dut.y_out[1];
  assign mon[12] = dut.y_out[2];
  assign mon[13] = dut.y_out[3];
  assign mon[14] = dut.y_out[4];
  assign mon[15] = dut.y_out[5];
  assign mon[16] = dut.y_out[6];
  assign mon[17] = dut.y_out[7];
  assign mon[18] = dut.valid_out;

  initial begin
    prev_dff = 19'b0;
    cycle_idx = 0;
  end

  always @(posedge clk) begin
    curr_dff = mon;
    // Hamming distance (fixed formula with explicit parentheses)
    hd = 0;
    for (kk = 0; kk < 19; kk = kk + 1)
      hd = hd + (curr_dff[kk] ^ prev_dff[kk]);
    $fwrite(power_fd, "%0d %0d\n", cycle_idx, hd);
    cycle_idx = cycle_idx + 1;
    prev_dff <= curr_dff;
  end

  // ------------------------------------------------------------------
  // Bit-trace dump: one 19-char binary row per posedge, aligned 1:1
  // with the power file rows (same cycle indexing).
  // ------------------------------------------------------------------
  always @(posedge clk) begin
    if (trace_fd != 0) begin
      for (kk = 0; kk < 19; kk = kk + 1)
        $fwrite(trace_fd, "%c", mon[kk] === 1'b1 ? "1" : "0");
      $fwrite(trace_fd, "\n");
    end
  end

  // ------------------------------------------------------------------
  // Stimulus (identical structure to tb_power_sim.v: inputs are applied
  // before the first negedge and held for the whole triple period)
  // ------------------------------------------------------------------
  initial begin
    clk = 0;
    rst_n = 0;
    valid_in = 0;
    x_in = 0;
    lfsr = 32'hCAFEFACE;

    power_fd  = $fopen("/tmp/uc_power.txt", "w");
    header_fd = $fopen("/tmp/uc_power_header.txt", "w");
    trace_fd  = $fopen("/tmp/uc_trace.txt", "w");
    if (power_fd == 0 || header_fd == 0 || trace_fd == 0) begin
      $display("ERROR: cannot open output files");
      $finish;
    end
    $fwrite(header_fd, "# secret s0 s1 first_cycle_of_this_triple\n");

    #20 rst_n = 1;

    for (t = 0; t < N_TRIPLES; t = t + 1) begin
      s0 = next_random(1'b0);
      s1 = next_random(1'b0);
      x_in = s0 ^ s1;

      $fwrite(header_fd, "%02h %02h %02h %0d\n",
              s0 ^ s1, s0, s1, cycle_idx);

      @(negedge clk);
      valid_in = 1'b1;
      @(negedge clk);
      valid_in = 1'b0;
      repeat (15) @(posedge clk);
      if (t % 1000 == 0) $display("  triple %0d / %0d", t, N_TRIPLES);
    end

    $fclose(power_fd);
    $fclose(header_fd);
    $fclose(trace_fd);
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

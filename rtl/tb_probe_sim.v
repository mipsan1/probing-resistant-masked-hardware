// =====================================================================
// tb_probe_sim.v
// Drives the gate-level netlist of the first-order masked AES S-box
// with N random input triples, and dumps the value of every DFF Q
// wire (the "stable output" of each combinational stage) at every
// clock edge.
//
// Output files:
//   /tmp/fo_trace.txt   - one row per clock edge; row = "bit0 bit1 ... bitN"
//                         where each bit is the value of one DFF Q wire.
//   /tmp/fo_header.txt  - one row per input triple; row = "secret s0 s1"
//
// The wire list is hard-coded based on the Yosys synthesis output
// (see /tmp/fo_stages.txt for the source of truth). To target a
// different netlist, edit the `wire_paths` parameter.
// =====================================================================

`timescale 1ns/1ps

module tb_probe_sim;

  // Number of random triples. 10,000 samples is plenty for MI
  // estimation of single wires (d=1) and 2-wire joint
  // distributions (d=2). Larger N gives tighter MI confidence
  // intervals at the cost of CPU time.
  parameter N_TRIPLES = 10000;

  // ------------------------------------------------------------------
  // DUT interface (first-order masked S-box)
  // ------------------------------------------------------------------
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

  // DUT instance. To target the gate-level netlist, change the
  // `include` directive above and use the synthesized module name.
  // The hierarchical reference below (e.g. `dut.valid_pipe[0]`) works
  // for both RTL and synthesized modules as long as the wire names
  // match.
  masked_sbox_first_order dut (
      .clk(clk),
      .rst_n(rst_n),
      .valid_in(valid_in),
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

  // ------------------------------------------------------------------
  // LFSR for reproducible random stimulus
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
  // Trace file handles
  // ------------------------------------------------------------------
  integer trace_fd;
  integer header_fd;

  // ------------------------------------------------------------------
  // Main stimulus
  // ------------------------------------------------------------------
  reg [7:0] s0, s1;
  integer t;

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
    lfsr = 32'hCAFEBABE;

    trace_fd = $fopen("/tmp/fo_trace.txt", "w");
    header_fd = $fopen("/tmp/fo_header.txt", "w");
    if (trace_fd == 0 || header_fd == 0) begin
      $display("ERROR: cannot open trace/header file");
      $finish;
    end

    $fwrite(header_fd, "# Probe trace for first-order masked S-box\n");

    // Reset
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

      $fwrite(header_fd, "%02h %02h %02h\n", s0 ^ s1, s0, s1);

      // Pulse valid_in
      @(negedge clk);
      valid_in = 1'b1;
      @(negedge clk);
      valid_in = 1'b0;
      // Wait for the pipeline to clear (10 cycles) plus some margin
      repeat (15) @(posedge clk);
    end

    $fclose(trace_fd);
    $fclose(header_fd);
    $display("Done. %0d triples dumped.", N_TRIPLES);
    $finish;
  end

  // Clock
  always #5 clk = ~clk;

  // Watchdog
  initial begin
    #(N_TRIPLES * 200 + 100000);
    $display("TIMEOUT");
    $fatal;
  end

  // ------------------------------------------------------------------
  // DFF trace dump
  //
  // We sample the value of every DFF Q wire (the "stable output" of
  // each combinational stage) at every clock edge and write a row of
  // 0/1 characters to the trace file. The wire list is hard-coded
  // based on the Yosys synthesis output (see /tmp/fo_stages.txt).
  //
  // In this design the DFF Q wires are:
  //   valid_pipe[0..9]   (10 register bits, the valid shift register)
  //   y0_out[0..7]        (output share 0)
  //   y1_out[0..7]        (output share 1)
  //   valid_out           (output valid)
  // = 27 bits per cycle, 10,000 triples * 15 cycles/triple = 150,000 rows.
  // ------------------------------------------------------------------
  integer kk;
  reg [8*1-1:0] ch;

  always @(posedge clk) begin
    for (kk = 0; kk < 27; kk = kk + 1) begin
      case (kk)
        0: ch = dut.valid_pipe[0] ? "1" : "0";
        1: ch = dut.valid_pipe[1] ? "1" : "0";
        2: ch = dut.valid_pipe[2] ? "1" : "0";
        3: ch = dut.valid_pipe[3] ? "1" : "0";
        4: ch = dut.valid_pipe[4] ? "1" : "0";
        5: ch = dut.valid_pipe[5] ? "1" : "0";
        6: ch = dut.valid_pipe[6] ? "1" : "0";
        7: ch = dut.valid_pipe[7] ? "1" : "0";
        8: ch = dut.valid_pipe[8] ? "1" : "0";
        9: ch = dut.valid_pipe[9] ? "1" : "0";
        10: ch = dut.y0_out[0] ? "1" : "0";
        11: ch = dut.y0_out[1] ? "1" : "0";
        12: ch = dut.y0_out[2] ? "1" : "0";
        13: ch = dut.y0_out[3] ? "1" : "0";
        14: ch = dut.y0_out[4] ? "1" : "0";
        15: ch = dut.y0_out[5] ? "1" : "0";
        16: ch = dut.y0_out[6] ? "1" : "0";
        17: ch = dut.y0_out[7] ? "1" : "0";
        18: ch = dut.y1_out[0] ? "1" : "0";
        19: ch = dut.y1_out[1] ? "1" : "0";
        20: ch = dut.y1_out[2] ? "1" : "0";
        21: ch = dut.y1_out[3] ? "1" : "0";
        22: ch = dut.y1_out[4] ? "1" : "0";
        23: ch = dut.y1_out[5] ? "1" : "0";
        24: ch = dut.y1_out[6] ? "1" : "0";
        25: ch = dut.y1_out[7] ? "1" : "0";
        26: ch = dut.valid_out ? "1" : "0";
      endcase
      $fwrite(trace_fd, "%c", ch);
    end
    $fwrite(trace_fd, "\n");
  end

endmodule

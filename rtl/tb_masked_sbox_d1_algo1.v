// Minimal self-checking TB for the Algorithm-1 (register-barrier) masked S-box.
`timescale 1ns/1ps
module tb_masked_sbox_d1_algo1;
  reg clk = 0;
  always #5 clk = ~clk;

  reg rst_n, valid_in;
  reg [7:0] x0_in, x1_in;
  reg [7:0] r_in [0:6];
  wire valid_out;
  wire [7:0] y0_out, y1_out;

  masked_sbox_first_order dut (
    .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
    .x0_in(x0_in), .x1_in(x1_in),
    .r0_in(r_in[0]), .r1_in(r_in[1]), .r2_in(r_in[2]),
    .r3_in(r_in[3]), .r4_in(r_in[4]), .r5_in(r_in[5]),
    .r6_in(r_in[6]),
    .valid_out(valid_out), .y0_out(y0_out), .y1_out(y1_out)
  );

  function [7:0] sbox_ref(input [7:0] x);
    case (x)
      8'h00: sbox_ref=8'h63; 8'h01: sbox_ref=8'h7c; 8'h53: sbox_ref=8'hed;
      8'hff: sbox_ref=8'h16; 8'ha5: sbox_ref=8'h06; 8'h7e: sbox_ref=8'hf3;
      8'hc3: sbox_ref=8'h2e; 8'h80: sbox_ref=8'hcd;
      default: sbox_ref=8'hxx;
    endcase
  endfunction

  reg [31:0] lfsr = 32'hdeadbeef;
  function [7:0] rnd(input integer d);
    begin
      lfsr = {lfsr[30:0], lfsr[31]^lfsr[21]^lfsr[1]^lfsr[0]};
      rnd = lfsr[7:0];
    end
  endfunction

  integer fails = 0, checks = 0, k, j;
  reg [7:0] vectors [0:7];

  task run_one(input [7:0] x);
    reg [7:0] m;
    integer c;
    begin
      m = rnd(0);
      for (j = 0; j < 7; j = j + 1) r_in[j] = rnd(0);
      @(negedge clk);
      x0_in = x ^ m; x1_in = m; valid_in = 1'b1;
      @(negedge clk);
      valid_in = 1'b0;
      // wait for valid_out with timeout
      c = 0;
      while (!valid_out && c < 30) begin @(negedge clk); c = c + 1; end
      if (!valid_out) begin
        $display("FAIL x=%02h: valid_out timeout", x); fails = fails + 1;
      end else if ((y0_out ^ y1_out) !== sbox_ref(x)) begin
        $display("FAIL x=%02h: got %02h expected %02h", x, y0_out^y1_out, sbox_ref(x));
        fails = fails + 1;
      end else begin
        checks = checks + 1;
        $display("PASS x=%02h -> %02h", x, y0_out^y1_out);
      end
      @(negedge clk);
    end
  endtask

  initial begin
    vectors[0]=8'h00; vectors[1]=8'h01; vectors[2]=8'h53; vectors[3]=8'hff;
    vectors[4]=8'ha5; vectors[5]=8'h7e; vectors[6]=8'hc3; vectors[7]=8'h80;
    rst_n = 0; valid_in = 0; x0_in = 0; x1_in = 0;
    for (k = 0; k < 7; k = k + 1) r_in[k] = 0;
    repeat (3) @(negedge clk);
    rst_n = 1;
    repeat (2) @(negedge clk);
    for (k = 0; k < 8; k = k + 1) run_one(vectors[k]);
    if (fails == 0) $display("ALL %0d CHECKS PASSED", checks);
    else $display("FAILURES: %0d", fails);
    $finish;
  end
endmodule

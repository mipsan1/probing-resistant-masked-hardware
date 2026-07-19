// =====================================================================
// tb_masked_aes_round1.v
// =====================================================================
// Self-checking testbench for masked_aes_round1_first_order.
//
// DUT contract: y = MixColumns(ShiftRows(SubBytes(x))) XOR rk, where
// x = x0_in ^ x1_in is the plaintext and rk = rk0_in ^ rk1_in is an
// EXTERNALLY supplied 128-bit round key (no initial AddRoundKey, no
// key schedule on chip).  The gold generator sim/gen_round1_vectors.py
// implements exactly this contract with the reference's ShiftRows
// convention (out[r][c] = in[r][(c - r) mod 4]).
//
// Strategy: the generator writes 100 random (plaintext, rk) pairs
// plus the corresponding 112 mask bytes per vector and the expected
// round-1 outputs to hex files, then this testbench:
//
//   1. reads the triples from hex files (one per vector),
//   2. drives the DUT with valid_in + the 112 mask bytes + 4 share
//      buses (plaintext, round key) for one cycle,
//   3. waits 20 cycles after valid_in (19-cycle round latency + 1
//      cycle so the output-register NBA update settles),
//   4. checks y0_out ^ y1_out == expected.
//
// The run script lives in syn/run_round1_sim.sh; the generator is
// sim/gen_round1_vectors.py.  Files:
//
//   sim/round1_pt.txt        -- one 128-bit plaintext per line
//   sim/round1_keys.txt      -- one 128-bit external round key per line
//   sim/round1_gold.txt      -- one 128-bit expected output per line
//   sim/round1_mask_<idx>.txt  -- 112 hex bytes, one per line
//
// The 128-bit files are stored byte-reversed so that $readmemh lands
// state byte k at bus bits [8k+7:8k] (the DUT's packing); see
// sim/gen_round1_vectors.py.
//
// Usage:
//   bash syn/run_round1_sim.sh        (from the workspace root)
// =====================================================================

`ifndef TB_MASKED_AES_ROUND1_V
`define TB_MASKED_AES_ROUND1_V

`timescale 1ns/1ps

module tb_masked_aes_round1;

    integer N_VECTORS = 100;
    integer LATENCY   = 20;   // 19-cycle round latency + 1 cycle so the
                              // output-register NBA update settles before
                              // the blocking sample below.

    reg clk;
    reg rst_n;
    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    // DUT inputs
    reg               valid_in;
    reg  [127:0]      x0_in, x1_in, rk0_in, rk1_in;
    reg  [7:0]        r_in [0:111];

    // DUT outputs
    wire              valid_out;
    wire [127:0]      y0_out, y1_out;

    // Generate DUT instance with port-by-port named binding for
    // the 112 mask bytes.  Done via generate-for to keep the
    // module body short.
    genvar k;
    generate
        for (k = 0; k < 112; k = k + 1) begin : GEN_PORT
            // No-op: ports are bound by name in the named-port
            // instantiation below.
        end
    endgenerate

    masked_aes_round1_first_order u_dut (
        .clk      (clk),
        .rst_n    (rst_n),
        .valid_in (valid_in),
        .x0_in    (x0_in),
        .x1_in    (x1_in),
        .rk0_in   (rk0_in),
        .rk1_in   (rk1_in),
        .r000_in (r_in[  0]), .r001_in (r_in[  1]), .r002_in (r_in[  2]), .r003_in (r_in[  3]),
        .r004_in (r_in[  4]), .r005_in (r_in[  5]), .r006_in (r_in[  6]), .r007_in (r_in[  7]),
        .r008_in (r_in[  8]), .r009_in (r_in[  9]), .r010_in (r_in[ 10]), .r011_in (r_in[ 11]),
        .r012_in (r_in[ 12]), .r013_in (r_in[ 13]), .r014_in (r_in[ 14]), .r015_in (r_in[ 15]),
        .r016_in (r_in[ 16]), .r017_in (r_in[ 17]), .r018_in (r_in[ 18]), .r019_in (r_in[ 19]),
        .r020_in (r_in[ 20]), .r021_in (r_in[ 21]), .r022_in (r_in[ 22]), .r023_in (r_in[ 23]),
        .r024_in (r_in[ 24]), .r025_in (r_in[ 25]), .r026_in (r_in[ 26]), .r027_in (r_in[ 27]),
        .r028_in (r_in[ 28]), .r029_in (r_in[ 29]), .r030_in (r_in[ 30]), .r031_in (r_in[ 31]),
        .r032_in (r_in[ 32]), .r033_in (r_in[ 33]), .r034_in (r_in[ 34]), .r035_in (r_in[ 35]),
        .r036_in (r_in[ 36]), .r037_in (r_in[ 37]), .r038_in (r_in[ 38]), .r039_in (r_in[ 39]),
        .r040_in (r_in[ 40]), .r041_in (r_in[ 41]), .r042_in (r_in[ 42]), .r043_in (r_in[ 43]),
        .r044_in (r_in[ 44]), .r045_in (r_in[ 45]), .r046_in (r_in[ 46]), .r047_in (r_in[ 47]),
        .r048_in (r_in[ 48]), .r049_in (r_in[ 49]), .r050_in (r_in[ 50]), .r051_in (r_in[ 51]),
        .r052_in (r_in[ 52]), .r053_in (r_in[ 53]), .r054_in (r_in[ 54]), .r055_in (r_in[ 55]),
        .r056_in (r_in[ 56]), .r057_in (r_in[ 57]), .r058_in (r_in[ 58]), .r059_in (r_in[ 59]),
        .r060_in (r_in[ 60]), .r061_in (r_in[ 61]), .r062_in (r_in[ 62]), .r063_in (r_in[ 63]),
        .r064_in (r_in[ 64]), .r065_in (r_in[ 65]), .r066_in (r_in[ 66]), .r067_in (r_in[ 67]),
        .r068_in (r_in[ 68]), .r069_in (r_in[ 69]), .r070_in (r_in[ 70]), .r071_in (r_in[ 71]),
        .r072_in (r_in[ 72]), .r073_in (r_in[ 73]), .r074_in (r_in[ 74]), .r075_in (r_in[ 75]),
        .r076_in (r_in[ 76]), .r077_in (r_in[ 77]), .r078_in (r_in[ 78]), .r079_in (r_in[ 79]),
        .r080_in (r_in[ 80]), .r081_in (r_in[ 81]), .r082_in (r_in[ 82]), .r083_in (r_in[ 83]),
        .r084_in (r_in[ 84]), .r085_in (r_in[ 85]), .r086_in (r_in[ 86]), .r087_in (r_in[ 87]),
        .r088_in (r_in[ 88]), .r089_in (r_in[ 89]), .r090_in (r_in[ 90]), .r091_in (r_in[ 91]),
        .r092_in (r_in[ 92]), .r093_in (r_in[ 93]), .r094_in (r_in[ 94]), .r095_in (r_in[ 95]),
        .r096_in (r_in[ 96]), .r097_in (r_in[ 97]), .r098_in (r_in[ 98]), .r099_in (r_in[ 99]),
        .r100_in (r_in[100]), .r101_in (r_in[101]), .r102_in (r_in[102]), .r103_in (r_in[103]),
        .r104_in (r_in[104]), .r105_in (r_in[105]), .r106_in (r_in[106]), .r107_in (r_in[107]),
        .r108_in (r_in[108]), .r109_in (r_in[109]), .r110_in (r_in[110]), .r111_in (r_in[111]),
        .valid_out(valid_out),
        .y0_out   (y0_out),
        .y1_out   (y1_out)
    );

    // ------------------------------------------------------------------
    // Vector files: one 128-bit hex word per line.
    // ------------------------------------------------------------------
    reg [127:0] exp_pt    [0:99];
    reg [127:0] exp_key   [0:99];
    reg [127:0] exp_gold  [0:99];

    initial begin
        $readmemh("sim/round1_pt.txt",   exp_pt);
        $readmemh("sim/round1_keys.txt", exp_key);
        $readmemh("sim/round1_gold.txt", exp_gold);
    end

    // ------------------------------------------------------------------
    // Mask file reader — 112 bytes per vector, one per line, hex.
    // We open the file for each vector and read all 112 bytes into
    // r_in[].  File names are sim/round1_mask_<idx>.txt.
    // ------------------------------------------------------------------
    integer   mfd;
    integer   mi;
    reg [8*64] mask_fname;

    task read_mask_file;
        input integer idx;
        begin
            // iverilog $sformat works for sprintf-style formatting
            $sformat(mask_fname, "sim/round1_mask_%0d.txt", idx);
            mfd = $fopen(mask_fname, "r");
            if (mfd == 0) begin
                $display("ERROR: cannot open %0s", mask_fname);
                $fatal;
            end
            for (mi = 0; mi < 112; mi = mi + 1) begin
                if ($fscanf(mfd, "%h", r_in[mi]) != 1) begin
                    $display("ERROR: short read at %0s line %0d",
                             mask_fname, mi);
                    $fatal;
                end
            end
            $fclose(mfd);
        end
    endtask

    // ------------------------------------------------------------------
    // Main stimulus
    // ------------------------------------------------------------------
    integer pass, fail;
    integer n;
    reg [127:0] actual;
    reg [127:0] x0_d, x1_d, rk0_d, rk1_d;
    reg [127:0] x0_rand, rk0_rand;
    integer     b;

    // LFSR (32-bit, x^32 + x^22 + x^2 + x + 1) — declared at module
    // top-level so that the initial block below can use it.
    reg [31:0] lfsr;
    function [7:0] next_byte;
        input dummy;
        begin
            lfsr = {lfsr[30:0],
                    lfsr[31] ^ lfsr[21] ^ lfsr[1] ^ lfsr[0]};
            next_byte = lfsr[7:0];
        end
    endfunction

    task automatic build_shares;
        input  [127:0] pt;
        input  [127:0] k;
        input  [127:0] x0_r;
        input  [127:0] rk0_r;
        output [127:0] xx0;
        output [127:0] xx1;
        output [127:0] kk0;
        output [127:0] kk1;
        begin
            xx0 = x0_r;
            xx1 = pt ^ x0_r;
            kk0 = rk0_r;
            kk1 = k  ^ rk0_r;
        end
    endtask

    initial begin
        // LFSR for random shares
        lfsr = 32'h12345678;
        pass = 0;
        fail = 0;
        valid_in = 1'b0;
        x0_in = 128'h0;  x1_in  = 128'h0;
        rk0_in = 128'h0; rk1_in = 128'h0;
        for (b = 0; b < 112; b = b + 1) r_in[b] = 8'h0;

        rst_n = 1'b0;
        repeat (4) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);

        for (n = 0; n < 100; n = n + 1) begin : VEC_LOOP
            // Build random shares for the n-th test vector.
            // The generator writes round1_pt.txt with the
            // SAME (pt, rk) sequence that it uses
            // for round1_mask_<n>.txt.
            for (b = 0; b < 16; b = b + 1) begin
                x0_rand[8*b +: 8] = next_byte(0);
                rk0_rand[8*b +: 8] = next_byte(0);
            end
            if (n < 2) $display("DBG vec %0d: x0_rand=%h x1_d=%h", n, x0_rand, x0_rand ^ exp_pt[n]);
            build_shares(exp_pt[n], exp_key[n], x0_rand, rk0_rand,
                         x0_d, x1_d, rk0_d, rk1_d);
            x0_in  = x0_d;  x1_in  = x1_d;
            rk0_in = rk0_d; rk1_in = rk1_d;
            read_mask_file(n);

            @(posedge clk);
            valid_in = 1'b1;
            @(posedge clk);
            valid_in = 1'b0;

            // Wait LATENCY cycles (literal to keep iverilog happy)
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);

            actual = y0_out ^ y1_out;
            if (actual != exp_gold[n]) begin
                $display("FAIL vec %0d: actual=%h expected=%h (pt=%h key=%h)",
                         n, actual, exp_gold[n], exp_pt[n], exp_key[n]);
                fail = fail + 1;
            end else begin
                pass = pass + 1;
            end
        end

        $display("========================================");
        $display("Round-1 functional: pass=%0d fail=%0d", pass, fail);
        $display("========================================");
        if (fail != 0) $fatal;
        $finish;
    end

    // LFSR is declared at module top (above) for clarity.
endmodule

`endif

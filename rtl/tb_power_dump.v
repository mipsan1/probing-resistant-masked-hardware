// =====================================================================
// tb_power_dump.v
// =====================================================================
// Self-checking testbench that dumps per-cycle output bits to a file
// for full-chip TVLA / MI analysis.  Uses $readmemh (much simpler
// than the inline $fscanf approach).
//
// Power model: at every posedge clk, emit two lines of 128 ASCII
// '0'/'1' characters -- y0_out and y1_out of the masked AES round 1.
// The HD model treats this 256-bit vector as the "power sample".
//
// Header file format (one line per triple, written by
// sim/gen_power_dump.py):
//
//   sim/power_secret.txt   - 32-hex secret bytes, one per line, N lines
//   sim/power_s0.txt       - 32-hex s0 (share-0), one per line
//   sim/power_s1.txt       - 32-hex s1 (share-1)
//   sim/power_rk0.txt      - 32-hex rk0 (round key share-0)
//   sim/power_rk1.txt      - 32-hex rk1 (round key share-1)
//   sim/power_masks.txt    - 96 mask bytes per vector
//                            (each line is 2 hex chars = 1 byte; 96
//                            bytes per vector, N vectors)
//
// Output:
//   sim/power_dump.txt   - one row per posedge clk after reset,
//                          each row = "y0_out_bits  y1_out_bits"
//                          (256 ASCII '0'/'1' chars + space + 256 chars)
//
// Usage:
//   cd sim && bash run_power_dump.sh
// =====================================================================

`ifndef TB_POWER_DUMP_V
`define TB_POWER_DUMP_V

`timescale 1ns/1ps

module tb_power_dump;

    integer N_VECTORS = 100;   // override via $value$plusargs at runtime

    reg clk;
    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    reg               rst_n;
    reg               valid_in;
    reg  [127:0]      x0_in, x1_in, rk0_in, rk1_in;
    reg  [7:0]        r_in [0:95];
    wire              valid_out;
    wire [127:0]      y0_out, y1_out;

    // DUT instance
    masked_aes_round1_first_order u_dut (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
        .x0_in(x0_in), .x1_in(x1_in), .rk0_in(rk0_in), .rk1_in(rk1_in),
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
        .valid_out(valid_out), .y0_out(y0_out), .y1_out(y1_out)
    );

    // ----------------------------------------------------------------
    // Header arrays loaded via $readmemh
    // ----------------------------------------------------------------
    reg [127:0] h_secret [0:9999];
    reg [127:0] h_s0     [0:9999];
    reg [127:0] h_s1     [0:9999];
    reg [127:0] h_rk0    [0:9999];
    reg [127:0] h_rk1    [0:9999];
    reg [7:0]   h_masks  [0:959999];   // 10000 * 96

    initial begin
        if (!$value$plusargs("N=%d", N_VECTORS)) begin
            N_VECTORS = 100;
        end
        $readmemh("sim/power_secret.txt", h_secret);
        $readmemh("sim/power_s0.txt",     h_s0);
        $readmemh("sim/power_s1.txt",     h_s1);
        $readmemh("sim/power_rk0.txt",    h_rk0);
        $readmemh("sim/power_rk1.txt",    h_rk1);
        $readmemh("sim/power_masks.txt",  h_masks);
    end

    // ----------------------------------------------------------------
    // Power dump: one line per posedge clk
    // ----------------------------------------------------------------
    integer pfd;
    reg dump_active;
    integer cycle_count;

    always @(posedge clk) begin
        if (dump_active) begin
            $fwrite(pfd, "%b %b\n", y0_out, y1_out);
            cycle_count = cycle_count + 1;
        end
    end

    // ----------------------------------------------------------------
    // Main
    // ----------------------------------------------------------------
    integer n, b;
    initial begin
        #1;   // wait for $readmemh to settle
        pfd = $fopen("sim/power_dump.txt", "w");
        if (pfd == 0) begin
            $display("ERROR: cannot open sim/power_dump.txt");
            $fatal;
        end
        cycle_count = 0;
        valid_in = 1'b0;
        x0_in    = 128'h0; x1_in    = 128'h0;
        rk0_in   = 128'h0; rk1_in   = 128'h0;
        for (b = 0; b < 96; b = b + 1) r_in[b] = 8'h0;
        rst_n    = 1'b0;
        repeat (4) @(posedge clk);
        rst_n    = 1'b1;
        @(posedge clk);
        dump_active = 1'b1;

        for (n = 0; n < N_VECTORS; n = n + 1) begin : VEC_LOOP
            x0_in  = h_s0[n];
            x1_in  = h_s1[n];
            rk0_in = h_rk0[n];
            rk1_in = h_rk1[n];
            for (b = 0; b < 96; b = b + 1)
                r_in[b] = h_masks[n*96 + b];
            @(posedge clk);
            valid_in = 1'b1;
            @(posedge clk);
            valid_in = 1'b0;
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
        end
        dump_active = 1'b0;
        $fclose(pfd);
        $display("Dumped %0d cycles", cycle_count);
        $finish;
    end

endmodule

`endif

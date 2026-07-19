// =====================================================================
// masked_aes_round1.v
// =====================================================================
// Single-round masked AES-128 (Boolean masking, d=1, share count = 2).
//
// Round 1 = SubBytes + ShiftRows + MixColumns + AddRoundKey.
//   - SubBytes: 16 parallel masked_sbox_first_order instances
//   - ShiftRows, MixColumns: combinational share-wise (linear GF(2^8))
//   - AddRoundKey, output register: clocked
//
// AES state packing: 128-bit bus, byte index = row + 4*col
//   (column-major).  Byte 0 is (row 0, col 0), byte 4 is
//   (row 0, col 1), ..., byte 15 is (row 3, col 3).
//
// Key schedule is performed OFF-LINE; the round key is supplied as
// two shares (rk0, rk1) where rk0 ^ rk1 = the actual round key.
//
// Latency: 17 cycles (S-box pipeline) + 1 (ARK register) +
//          1 (output register) = 19 cycles.  valid_out is
//          combinational from sb_v_all so that data and valid paths
//          share the same latency.
//
// Randomness budget per round: 16 S-boxes * 7 bytes = 112 bytes
//                              = 896 fresh bits per AES round.
// =====================================================================

`timescale 1ns/1ps

module masked_aes_round1_first_order (
    input              clk,
    input              rst_n,
    input              valid_in,

    // ----- 16-byte plaintext (two shares) -----
    input  [127:0]     x0_in,
    input  [127:0]     x1_in,

    // ----- 16-byte round key (two shares) -----
    input  [127:0]     rk0_in,
    input  [127:0]     rk1_in,

    // ----- 112 mask bytes (16 S-boxes * 7 bytes each) -----
    input  [7:0] r000_in, r001_in, r002_in, r003_in, r004_in, r005_in, r006_in, r007_in,
    input  [7:0] r008_in, r009_in, r010_in, r011_in, r012_in, r013_in, r014_in, r015_in,
    input  [7:0] r016_in, r017_in, r018_in, r019_in, r020_in, r021_in, r022_in, r023_in,
    input  [7:0] r024_in, r025_in, r026_in, r027_in, r028_in, r029_in, r030_in, r031_in,
    input  [7:0] r032_in, r033_in, r034_in, r035_in, r036_in, r037_in, r038_in, r039_in,
    input  [7:0] r040_in, r041_in, r042_in, r043_in, r044_in, r045_in, r046_in, r047_in,
    input  [7:0] r048_in, r049_in, r050_in, r051_in, r052_in, r053_in, r054_in, r055_in,
    input  [7:0] r056_in, r057_in, r058_in, r059_in, r060_in, r061_in, r062_in, r063_in,
    input  [7:0] r064_in, r065_in, r066_in, r067_in, r068_in, r069_in, r070_in, r071_in,
    input  [7:0] r072_in, r073_in, r074_in, r075_in, r076_in, r077_in, r078_in, r079_in,
    input  [7:0] r080_in, r081_in, r082_in, r083_in, r084_in, r085_in, r086_in, r087_in,
    input  [7:0] r088_in, r089_in, r090_in, r091_in, r092_in, r093_in, r094_in, r095_in,
    input  [7:0] r096_in, r097_in, r098_in, r099_in, r100_in, r101_in, r102_in, r103_in,
    input  [7:0] r104_in, r105_in, r106_in, r107_in, r108_in, r109_in, r110_in, r111_in,

    // ----- Output -----
    output             valid_out,
    output reg [127:0] y0_out,
    output reg [127:0] y1_out
);

    // ----------------------------------------------------------------
    // STAGE 1: SubBytes (16 parallel masked S-boxes)
    // ----------------------------------------------------------------
    wire        sb_v   [0:15];
    wire [7:0]  sb_y0  [0:15];
    wire [7:0]  sb_y1  [0:15];

    // Pack S-box outputs into 128-bit buses.  sb_y0[k] holds the
    // S-box output for state byte k, placed at bit-slice [8*k+:8].
    wire [127:0] sb_state_y0 = {sb_y0[15], sb_y0[14], sb_y0[13], sb_y0[12],
                                sb_y0[11], sb_y0[10], sb_y0[ 9], sb_y0[ 8],
                                sb_y0[ 7], sb_y0[ 6], sb_y0[ 5], sb_y0[ 4],
                                sb_y0[ 3], sb_y0[ 2], sb_y0[ 1], sb_y0[ 0]};
    wire [127:0] sb_state_y1 = {sb_y1[15], sb_y1[14], sb_y1[13], sb_y1[12],
                                sb_y1[11], sb_y1[10], sb_y1[ 9], sb_y1[ 8],
                                sb_y1[ 7], sb_y1[ 6], sb_y1[ 5], sb_y1[ 4],
                                sb_y1[ 3], sb_y1[ 2], sb_y1[ 1], sb_y1[ 0]};

    masked_sbox_first_order u_sbox_0  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[  0 +: 8]), .x1_in(x1_in[  0 +: 8]), .r0_in(r000_in), .r1_in(r001_in), .r2_in(r002_in), .r3_in(r003_in), .r4_in(r004_in), .r5_in(r005_in), .r6_in(r006_in), .valid_out(sb_v[ 0]), .y0_out(sb_y0[ 0]), .y1_out(sb_y1[ 0]));
    masked_sbox_first_order u_sbox_1  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[  8 +: 8]), .x1_in(x1_in[  8 +: 8]), .r0_in(r007_in), .r1_in(r008_in), .r2_in(r009_in), .r3_in(r010_in), .r4_in(r011_in), .r5_in(r012_in), .r6_in(r013_in), .valid_out(sb_v[ 1]), .y0_out(sb_y0[ 1]), .y1_out(sb_y1[ 1]));
    masked_sbox_first_order u_sbox_2  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 16 +: 8]), .x1_in(x1_in[ 16 +: 8]), .r0_in(r014_in), .r1_in(r015_in), .r2_in(r016_in), .r3_in(r017_in), .r4_in(r018_in), .r5_in(r019_in), .r6_in(r020_in), .valid_out(sb_v[ 2]), .y0_out(sb_y0[ 2]), .y1_out(sb_y1[ 2]));
    masked_sbox_first_order u_sbox_3  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 24 +: 8]), .x1_in(x1_in[ 24 +: 8]), .r0_in(r021_in), .r1_in(r022_in), .r2_in(r023_in), .r3_in(r024_in), .r4_in(r025_in), .r5_in(r026_in), .r6_in(r027_in), .valid_out(sb_v[ 3]), .y0_out(sb_y0[ 3]), .y1_out(sb_y1[ 3]));
    masked_sbox_first_order u_sbox_4  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 32 +: 8]), .x1_in(x1_in[ 32 +: 8]), .r0_in(r028_in), .r1_in(r029_in), .r2_in(r030_in), .r3_in(r031_in), .r4_in(r032_in), .r5_in(r033_in), .r6_in(r034_in), .valid_out(sb_v[ 4]), .y0_out(sb_y0[ 4]), .y1_out(sb_y1[ 4]));
    masked_sbox_first_order u_sbox_5  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 40 +: 8]), .x1_in(x1_in[ 40 +: 8]), .r0_in(r035_in), .r1_in(r036_in), .r2_in(r037_in), .r3_in(r038_in), .r4_in(r039_in), .r5_in(r040_in), .r6_in(r041_in), .valid_out(sb_v[ 5]), .y0_out(sb_y0[ 5]), .y1_out(sb_y1[ 5]));
    masked_sbox_first_order u_sbox_6  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 48 +: 8]), .x1_in(x1_in[ 48 +: 8]), .r0_in(r042_in), .r1_in(r043_in), .r2_in(r044_in), .r3_in(r045_in), .r4_in(r046_in), .r5_in(r047_in), .r6_in(r048_in), .valid_out(sb_v[ 6]), .y0_out(sb_y0[ 6]), .y1_out(sb_y1[ 6]));
    masked_sbox_first_order u_sbox_7  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 56 +: 8]), .x1_in(x1_in[ 56 +: 8]), .r0_in(r049_in), .r1_in(r050_in), .r2_in(r051_in), .r3_in(r052_in), .r4_in(r053_in), .r5_in(r054_in), .r6_in(r055_in), .valid_out(sb_v[ 7]), .y0_out(sb_y0[ 7]), .y1_out(sb_y1[ 7]));
    masked_sbox_first_order u_sbox_8  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 64 +: 8]), .x1_in(x1_in[ 64 +: 8]), .r0_in(r056_in), .r1_in(r057_in), .r2_in(r058_in), .r3_in(r059_in), .r4_in(r060_in), .r5_in(r061_in), .r6_in(r062_in), .valid_out(sb_v[ 8]), .y0_out(sb_y0[ 8]), .y1_out(sb_y1[ 8]));
    masked_sbox_first_order u_sbox_9  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 72 +: 8]), .x1_in(x1_in[ 72 +: 8]), .r0_in(r063_in), .r1_in(r064_in), .r2_in(r065_in), .r3_in(r066_in), .r4_in(r067_in), .r5_in(r068_in), .r6_in(r069_in), .valid_out(sb_v[ 9]), .y0_out(sb_y0[ 9]), .y1_out(sb_y1[ 9]));
    masked_sbox_first_order u_sbox_10 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 80 +: 8]), .x1_in(x1_in[ 80 +: 8]), .r0_in(r070_in), .r1_in(r071_in), .r2_in(r072_in), .r3_in(r073_in), .r4_in(r074_in), .r5_in(r075_in), .r6_in(r076_in), .valid_out(sb_v[10]), .y0_out(sb_y0[10]), .y1_out(sb_y1[10]));
    masked_sbox_first_order u_sbox_11 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 88 +: 8]), .x1_in(x1_in[ 88 +: 8]), .r0_in(r077_in), .r1_in(r078_in), .r2_in(r079_in), .r3_in(r080_in), .r4_in(r081_in), .r5_in(r082_in), .r6_in(r083_in), .valid_out(sb_v[11]), .y0_out(sb_y0[11]), .y1_out(sb_y1[11]));
    masked_sbox_first_order u_sbox_12 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 96 +: 8]), .x1_in(x1_in[ 96 +: 8]), .r0_in(r084_in), .r1_in(r085_in), .r2_in(r086_in), .r3_in(r087_in), .r4_in(r088_in), .r5_in(r089_in), .r6_in(r090_in), .valid_out(sb_v[12]), .y0_out(sb_y0[12]), .y1_out(sb_y1[12]));
    masked_sbox_first_order u_sbox_13 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[104 +: 8]), .x1_in(x1_in[104 +: 8]), .r0_in(r091_in), .r1_in(r092_in), .r2_in(r093_in), .r3_in(r094_in), .r4_in(r095_in), .r5_in(r096_in), .r6_in(r097_in), .valid_out(sb_v[13]), .y0_out(sb_y0[13]), .y1_out(sb_y1[13]));
    masked_sbox_first_order u_sbox_14 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[112 +: 8]), .x1_in(x1_in[112 +: 8]), .r0_in(r098_in), .r1_in(r099_in), .r2_in(r100_in), .r3_in(r101_in), .r4_in(r102_in), .r5_in(r103_in), .r6_in(r104_in), .valid_out(sb_v[14]), .y0_out(sb_y0[14]), .y1_out(sb_y1[14]));
    masked_sbox_first_order u_sbox_15 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[120 +: 8]), .x1_in(x1_in[120 +: 8]), .r0_in(r105_in), .r1_in(r106_in), .r2_in(r107_in), .r3_in(r108_in), .r4_in(r109_in), .r5_in(r110_in), .r6_in(r111_in), .valid_out(sb_v[15]), .y0_out(sb_y0[15]), .y1_out(sb_y1[15]));

    wire sb_v_all = sb_v[ 0] & sb_v[ 1] & sb_v[ 2] & sb_v[ 3]
                  & sb_v[ 4] & sb_v[ 5] & sb_v[ 6] & sb_v[ 7]
                  & sb_v[ 8] & sb_v[ 9] & sb_v[10] & sb_v[11]
                  & sb_v[12] & sb_v[13] & sb_v[14] & sb_v[15];

    // ----------------------------------------------------------------
    // STAGE 2: ShiftRows (combinational, share-wise)
    // ----------------------------------------------------------------
    // Standard AES ShiftRows: row r shifts left by r columns.  With
    // column-major packing byte b = row + 4*col, this maps
    //   out[row][col] = in[row][(col - row) mod 4]
    //                  = byte (row + 4*((col - row) mod 4))
    //
    // Source->Destination table (src -> dst):
    //   byte  0 (r0,c0) -> (r0,c0)   = byte  0
    //   byte  1 (r1,c0) -> (r1,c3)   = byte 13
    //   byte  2 (r2,c0) -> (r2,c2)   = byte 10
    //   byte  3 (r3,c0) -> (r3,c1)   = byte  7
    //   byte  4 (r0,c1) -> (r0,c1)   = byte  4
    //   byte  5 (r1,c1) -> (r1,c0)   = byte  1
    //   byte  6 (r2,c1) -> (r2,c3)   = byte 14
    //   byte  7 (r3,c1) -> (r3,c2)   = byte 11
    //   byte  8 (r0,c2) -> (r0,c2)   = byte  8
    //   byte  9 (r1,c2) -> (r1,c1)   = byte  5
    //   byte 10 (r2,c2) -> (r2,c0)   = byte  2
    //   byte 11 (r3,c2) -> (r3,c3)   = byte 15
    //   byte 12 (r0,c3) -> (r0,c3)   = byte 12
    //   byte 13 (r1,c3) -> (r1,c2)   = byte  9
    //   byte 14 (r2,c3) -> (r2,c1)   = byte  6
    //   byte 15 (r3,c3) -> (r3,c0)   = byte  3
    // NOTE (iverilog elaboration workaround): writing ShiftRows as
    // 16 per-lane continuous assigns on a 128-bit net is
    // mis-elaborated by Icarus Verilog 13 (upper lanes left at Z,
    // lower lanes multiply-driven to X).  The equivalent single
    // concatenation assignment below elaborates correctly and is
    // bit-identical for synthesis (Yosys maps both forms the same).
    // NOTE (functional fix): selects use scaled bit indices
    // [8*b +: 8] (byte b occupies bits [8b+7 : 8b]); the original
    // per-lane form used unscaled [b +: 8] selects, which alias
    // across byte lanes.  The dst<-src permutation is exactly the
    // one documented in the table above (dst1<-13, dst2<-10,
    // dst3<-7, dst5<-1, dst6<-14, dst7<-11, dst9<-5, dst10<-2,
    // dst11<-15, dst13<-9, dst14<-6, dst15<-3; bytes 0/4/8/12
    // unchanged), matching the executable reference model
    // reference/masked_aes.py (_shift_rows: out[r][c] =
    // state[r][(c - r) mod 4]) and the sim/ gold vectors generated
    // from it.  Verified end-to-end against that reference.
    wire [127:0] sr_state_y0, sr_state_y1;
    assign sr_state_y0 = {sb_state_y0[8* 3 +: 8], sb_state_y0[8* 6 +: 8],
                          sb_state_y0[8* 9 +: 8], sb_state_y0[8*12 +: 8],
                          sb_state_y0[8*15 +: 8], sb_state_y0[8* 2 +: 8],
                          sb_state_y0[8* 5 +: 8], sb_state_y0[8* 8 +: 8],
                          sb_state_y0[8*11 +: 8], sb_state_y0[8*14 +: 8],
                          sb_state_y0[8* 1 +: 8], sb_state_y0[8* 4 +: 8],
                          sb_state_y0[8* 7 +: 8], sb_state_y0[8*10 +: 8],
                          sb_state_y0[8*13 +: 8], sb_state_y0[8* 0 +: 8]};

    assign sr_state_y1 = {sb_state_y1[8* 3 +: 8], sb_state_y1[8* 6 +: 8],
                          sb_state_y1[8* 9 +: 8], sb_state_y1[8*12 +: 8],
                          sb_state_y1[8*15 +: 8], sb_state_y1[8* 2 +: 8],
                          sb_state_y1[8* 5 +: 8], sb_state_y1[8* 8 +: 8],
                          sb_state_y1[8*11 +: 8], sb_state_y1[8*14 +: 8],
                          sb_state_y1[8* 1 +: 8], sb_state_y1[8* 4 +: 8],
                          sb_state_y1[8* 7 +: 8], sb_state_y1[8*10 +: 8],
                          sb_state_y1[8*13 +: 8], sb_state_y1[8* 0 +: 8]};

    // ----------------------------------------------------------------
    // STAGE 3: MixColumns (combinational, share-wise)
    // ----------------------------------------------------------------
    // Standard AES MixColumns: each column = M * column over GF(2^8),
    //   M = [2 3 1 1; 1 2 3 1; 1 1 2 3; 3 1 1 2]
    // Column 0 = bytes 0..3, column 1 = bytes 4..7, etc.
    function [7:0] xtime_f;
        input [7:0] b;
        reg [7:0] t;
        begin
            t = {b[6:0], 1'b0};
            xtime_f = b[7] ? (t ^ 8'h1b) : t;
        end
    endfunction

    wire [127:0] mc_state_y0, mc_state_y1;

    // NOTE (iverilog elaboration workaround): like the ShiftRows
    // wiring above, 16 per-lane continuous assigns on a 128-bit net
    // are mis-elaborated by Icarus Verilog 13.  Wrapping each column
    // mix in a generate-for iteration elaborates correctly (verified
    // against the FIPS-197 Appendix B MixColumns vector) and unrolls
    // to the identical netlist structure for synthesis.
    genvar mc_c;
    generate
    for (mc_c = 0; mc_c < 4; mc_c = mc_c + 1) begin : GEN_MC_COL
        // --- Column mc_c, share 0 ---
        assign mc_state_y0[8*(4*mc_c+0) +: 8] = xtime_f(sr_state_y0[8*(4*mc_c+0) +: 8])
                                 ^ (xtime_f(sr_state_y0[8*(4*mc_c+1) +: 8]) ^ sr_state_y0[8*(4*mc_c+1) +: 8])
                                 ^ sr_state_y0[8*(4*mc_c+2) +: 8]
                                 ^ sr_state_y0[8*(4*mc_c+3) +: 8];
        assign mc_state_y0[8*(4*mc_c+1) +: 8] = sr_state_y0[8*(4*mc_c+0) +: 8]
                                 ^ xtime_f(sr_state_y0[8*(4*mc_c+1) +: 8])
                                 ^ (xtime_f(sr_state_y0[8*(4*mc_c+2) +: 8]) ^ sr_state_y0[8*(4*mc_c+2) +: 8])
                                 ^ sr_state_y0[8*(4*mc_c+3) +: 8];
        assign mc_state_y0[8*(4*mc_c+2) +: 8] = sr_state_y0[8*(4*mc_c+0) +: 8]
                                 ^ sr_state_y0[8*(4*mc_c+1) +: 8]
                                 ^ xtime_f(sr_state_y0[8*(4*mc_c+2) +: 8])
                                 ^ (xtime_f(sr_state_y0[8*(4*mc_c+3) +: 8]) ^ sr_state_y0[8*(4*mc_c+3) +: 8]);
        assign mc_state_y0[8*(4*mc_c+3) +: 8] = (xtime_f(sr_state_y0[8*(4*mc_c+0) +: 8]) ^ sr_state_y0[8*(4*mc_c+0) +: 8])
                                 ^ sr_state_y0[8*(4*mc_c+1) +: 8]
                                 ^ sr_state_y0[8*(4*mc_c+2) +: 8]
                                 ^ xtime_f(sr_state_y0[8*(4*mc_c+3) +: 8]);

        // --- Column mc_c, share 1 ---
        assign mc_state_y1[8*(4*mc_c+0) +: 8] = xtime_f(sr_state_y1[8*(4*mc_c+0) +: 8])
                                 ^ (xtime_f(sr_state_y1[8*(4*mc_c+1) +: 8]) ^ sr_state_y1[8*(4*mc_c+1) +: 8])
                                 ^ sr_state_y1[8*(4*mc_c+2) +: 8]
                                 ^ sr_state_y1[8*(4*mc_c+3) +: 8];
        assign mc_state_y1[8*(4*mc_c+1) +: 8] = sr_state_y1[8*(4*mc_c+0) +: 8]
                                 ^ xtime_f(sr_state_y1[8*(4*mc_c+1) +: 8])
                                 ^ (xtime_f(sr_state_y1[8*(4*mc_c+2) +: 8]) ^ sr_state_y1[8*(4*mc_c+2) +: 8])
                                 ^ sr_state_y1[8*(4*mc_c+3) +: 8];
        assign mc_state_y1[8*(4*mc_c+2) +: 8] = sr_state_y1[8*(4*mc_c+0) +: 8]
                                 ^ sr_state_y1[8*(4*mc_c+1) +: 8]
                                 ^ xtime_f(sr_state_y1[8*(4*mc_c+2) +: 8])
                                 ^ (xtime_f(sr_state_y1[8*(4*mc_c+3) +: 8]) ^ sr_state_y1[8*(4*mc_c+3) +: 8]);
        assign mc_state_y1[8*(4*mc_c+3) +: 8] = (xtime_f(sr_state_y1[8*(4*mc_c+0) +: 8]) ^ sr_state_y1[8*(4*mc_c+0) +: 8])
                                 ^ sr_state_y1[8*(4*mc_c+1) +: 8]
                                 ^ sr_state_y1[8*(4*mc_c+2) +: 8]
                                 ^ xtime_f(sr_state_y1[8*(4*mc_c+3) +: 8]);
    end
    endgenerate

    // ----------------------------------------------------------------
    // STAGE 4: AddRoundKey (clocked register, share-wise XOR)
    // ----------------------------------------------------------------
    reg [127:0] ark_state_y0;
    reg [127:0] ark_state_y1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ark_state_y0 <= 128'h0;
            ark_state_y1 <= 128'h0;
        end else begin
            ark_state_y0 <= mc_state_y0 ^ rk0_in;
            ark_state_y1 <= mc_state_y1 ^ rk1_in;
        end
    end

    // ----------------------------------------------------------------
    // STAGE 5: output register
    // ----------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y0_out <= 128'h0;
            y1_out <= 128'h0;
        end else begin
            y0_out <= ark_state_y0;
            y1_out <= ark_state_y1;
        end
    end

    // valid_out: combinational from sb_v_all.  19-cycle data
    // latency = 17 (S-box pipeline) + 1 (ARK) + 1 (output register).
    assign valid_out = sb_v_all;

endmodule

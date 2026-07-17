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
// Latency: 10 cycles (S-box pipeline) + 1 (ARK register) +
//          1 (output register) = 12 cycles.  valid_out is
//          combinational from sb_v_all so that data and valid paths
//          share the same latency.
//
// Randomness budget per round: 16 S-boxes * 28 bytes = 448 bytes
//                              = 3584 fresh bits per AES round.
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

    // ----- 448 mask bytes (16 S-boxes * 28 bytes each) -----
    input  [7:0] r000_in, r001_in, r002_in, r003_in, r004_in, r005_in, r006_in, r007_in,
    input  [7:0] r008_in, r009_in, r010_in, r011_in, r012_in, r013_in, r014_in, r015_in,
    input  [7:0] r016_in, r017_in, r018_in, r019_in, r020_in, r021_in, r022_in, r023_in,
    input  [7:0] r024_in, r025_in, r026_in, r027_in,
    input  [7:0] r028_in, r029_in, r030_in, r031_in, r032_in, r033_in, r034_in, r035_in,
    input  [7:0] r036_in, r037_in, r038_in, r039_in, r040_in, r041_in, r042_in, r043_in,
    input  [7:0] r044_in, r045_in, r046_in, r047_in, r048_in, r049_in, r050_in, r051_in,
    input  [7:0] r052_in, r053_in, r054_in, r055_in,
    input  [7:0] r056_in, r057_in, r058_in, r059_in, r060_in, r061_in, r062_in, r063_in,
    input  [7:0] r064_in, r065_in, r066_in, r067_in, r068_in, r069_in, r070_in, r071_in,
    input  [7:0] r072_in, r073_in, r074_in, r075_in, r076_in, r077_in, r078_in, r079_in,
    input  [7:0] r080_in, r081_in, r082_in, r083_in,
    input  [7:0] r084_in, r085_in, r086_in, r087_in, r088_in, r089_in, r090_in, r091_in,
    input  [7:0] r092_in, r093_in, r094_in, r095_in, r096_in, r097_in, r098_in, r099_in,
    input  [7:0] r100_in, r101_in, r102_in, r103_in, r104_in, r105_in, r106_in, r107_in,
    input  [7:0] r108_in, r109_in, r110_in, r111_in,
    input  [7:0] r112_in, r113_in, r114_in, r115_in, r116_in, r117_in, r118_in, r119_in,
    input  [7:0] r120_in, r121_in, r122_in, r123_in, r124_in, r125_in, r126_in, r127_in,
    input  [7:0] r128_in, r129_in, r130_in, r131_in, r132_in, r133_in, r134_in, r135_in,
    input  [7:0] r136_in, r137_in, r138_in, r139_in,
    input  [7:0] r140_in, r141_in, r142_in, r143_in, r144_in, r145_in, r146_in, r147_in,
    input  [7:0] r148_in, r149_in, r150_in, r151_in, r152_in, r153_in, r154_in, r155_in,
    input  [7:0] r156_in, r157_in, r158_in, r159_in, r160_in, r161_in, r162_in, r163_in,
    input  [7:0] r164_in, r165_in, r166_in, r167_in,
    input  [7:0] r168_in, r169_in, r170_in, r171_in, r172_in, r173_in, r174_in, r175_in,
    input  [7:0] r176_in, r177_in, r178_in, r179_in, r180_in, r181_in, r182_in, r183_in,
    input  [7:0] r184_in, r185_in, r186_in, r187_in, r188_in, r189_in, r190_in, r191_in,
    input  [7:0] r192_in, r193_in, r194_in, r195_in,
    input  [7:0] r196_in, r197_in, r198_in, r199_in, r200_in, r201_in, r202_in, r203_in,
    input  [7:0] r204_in, r205_in, r206_in, r207_in, r208_in, r209_in, r210_in, r211_in,
    input  [7:0] r212_in, r213_in, r214_in, r215_in, r216_in, r217_in, r218_in, r219_in,
    input  [7:0] r220_in, r221_in, r222_in, r223_in,
    input  [7:0] r224_in, r225_in, r226_in, r227_in, r228_in, r229_in, r230_in, r231_in,
    input  [7:0] r232_in, r233_in, r234_in, r235_in, r236_in, r237_in, r238_in, r239_in,
    input  [7:0] r240_in, r241_in, r242_in, r243_in, r244_in, r245_in, r246_in, r247_in,
    input  [7:0] r248_in, r249_in, r250_in, r251_in,
    input  [7:0] r252_in, r253_in, r254_in, r255_in, r256_in, r257_in, r258_in, r259_in,
    input  [7:0] r260_in, r261_in, r262_in, r263_in, r264_in, r265_in, r266_in, r267_in,
    input  [7:0] r268_in, r269_in, r270_in, r271_in, r272_in, r273_in, r274_in, r275_in,
    input  [7:0] r276_in, r277_in, r278_in, r279_in,
    input  [7:0] r280_in, r281_in, r282_in, r283_in, r284_in, r285_in, r286_in, r287_in,
    input  [7:0] r288_in, r289_in, r290_in, r291_in, r292_in, r293_in, r294_in, r295_in,
    input  [7:0] r296_in, r297_in, r298_in, r299_in, r300_in, r301_in, r302_in, r303_in,
    input  [7:0] r304_in, r305_in, r306_in, r307_in,
    input  [7:0] r308_in, r309_in, r310_in, r311_in, r312_in, r313_in, r314_in, r315_in,
    input  [7:0] r316_in, r317_in, r318_in, r319_in, r320_in, r321_in, r322_in, r323_in,
    input  [7:0] r324_in, r325_in, r326_in, r327_in, r328_in, r329_in, r330_in, r331_in,
    input  [7:0] r332_in, r333_in, r334_in, r335_in,
    input  [7:0] r336_in, r337_in, r338_in, r339_in, r340_in, r341_in, r342_in, r343_in,
    input  [7:0] r344_in, r345_in, r346_in, r347_in, r348_in, r349_in, r350_in, r351_in,
    input  [7:0] r352_in, r353_in, r354_in, r355_in, r356_in, r357_in, r358_in, r359_in,
    input  [7:0] r360_in, r361_in, r362_in, r363_in,
    input  [7:0] r364_in, r365_in, r366_in, r367_in, r368_in, r369_in, r370_in, r371_in,
    input  [7:0] r372_in, r373_in, r374_in, r375_in, r376_in, r377_in, r378_in, r379_in,
    input  [7:0] r380_in, r381_in, r382_in, r383_in, r384_in, r385_in, r386_in, r387_in,
    input  [7:0] r388_in, r389_in, r390_in, r391_in,
    input  [7:0] r392_in, r393_in, r394_in, r395_in, r396_in, r397_in, r398_in, r399_in,
    input  [7:0] r400_in, r401_in, r402_in, r403_in, r404_in, r405_in, r406_in, r407_in,
    input  [7:0] r408_in, r409_in, r410_in, r411_in, r412_in, r413_in, r414_in, r415_in,
    input  [7:0] r416_in, r417_in, r418_in, r419_in,
    input  [7:0] r420_in, r421_in, r422_in, r423_in, r424_in, r425_in, r426_in, r427_in,
    input  [7:0] r428_in, r429_in, r430_in, r431_in, r432_in, r433_in, r434_in, r435_in,
    input  [7:0] r436_in, r437_in, r438_in, r439_in, r440_in, r441_in, r442_in, r443_in,
    input  [7:0] r444_in, r445_in, r446_in, r447_in,

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

    masked_sbox_first_order u_sbox_0  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[  0 +: 8]), .x1_in(x1_in[  0 +: 8]), .r0_in(r000_in), .r1_in(r001_in), .r2_in(r002_in), .r3_in(r003_in), .r4_in(r004_in), .r5_in(r005_in), .r6_in(r006_in), .r7_in(r007_in), .r8_in(r008_in), .r9_in(r009_in), .r10_in(r010_in), .r11_in(r011_in), .r12_in(r012_in), .r13_in(r013_in), .r14_in(r014_in), .r15_in(r015_in), .r16_in(r016_in), .r17_in(r017_in), .r18_in(r018_in), .r19_in(r019_in), .r20_in(r020_in), .r21_in(r021_in), .r22_in(r022_in), .r23_in(r023_in), .r24_in(r024_in), .r25_in(r025_in), .r26_in(r026_in), .r27_in(r027_in), .valid_out(sb_v[ 0]), .y0_out(sb_y0[ 0]), .y1_out(sb_y1[ 0]));
    masked_sbox_first_order u_sbox_1  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[  8 +: 8]), .x1_in(x1_in[  8 +: 8]), .r0_in(r028_in), .r1_in(r029_in), .r2_in(r030_in), .r3_in(r031_in), .r4_in(r032_in), .r5_in(r033_in), .r6_in(r034_in), .r7_in(r035_in), .r8_in(r036_in), .r9_in(r037_in), .r10_in(r038_in), .r11_in(r039_in), .r12_in(r040_in), .r13_in(r041_in), .r14_in(r042_in), .r15_in(r043_in), .r16_in(r044_in), .r17_in(r045_in), .r18_in(r046_in), .r19_in(r047_in), .r20_in(r048_in), .r21_in(r049_in), .r22_in(r050_in), .r23_in(r051_in), .r24_in(r052_in), .r25_in(r053_in), .r26_in(r054_in), .r27_in(r055_in), .valid_out(sb_v[ 1]), .y0_out(sb_y0[ 1]), .y1_out(sb_y1[ 1]));
    masked_sbox_first_order u_sbox_2  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 16 +: 8]), .x1_in(x1_in[ 16 +: 8]), .r0_in(r056_in), .r1_in(r057_in), .r2_in(r058_in), .r3_in(r059_in), .r4_in(r060_in), .r5_in(r061_in), .r6_in(r062_in), .r7_in(r063_in), .r8_in(r064_in), .r9_in(r065_in), .r10_in(r066_in), .r11_in(r067_in), .r12_in(r068_in), .r13_in(r069_in), .r14_in(r070_in), .r15_in(r071_in), .r16_in(r072_in), .r17_in(r073_in), .r18_in(r074_in), .r19_in(r075_in), .r20_in(r076_in), .r21_in(r077_in), .r22_in(r078_in), .r23_in(r079_in), .r24_in(r080_in), .r25_in(r081_in), .r26_in(r082_in), .r27_in(r083_in), .valid_out(sb_v[ 2]), .y0_out(sb_y0[ 2]), .y1_out(sb_y1[ 2]));
    masked_sbox_first_order u_sbox_3  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 24 +: 8]), .x1_in(x1_in[ 24 +: 8]), .r0_in(r084_in), .r1_in(r085_in), .r2_in(r086_in), .r3_in(r087_in), .r4_in(r088_in), .r5_in(r089_in), .r6_in(r090_in), .r7_in(r091_in), .r8_in(r092_in), .r9_in(r093_in), .r10_in(r094_in), .r11_in(r095_in), .r12_in(r096_in), .r13_in(r097_in), .r14_in(r098_in), .r15_in(r099_in), .r16_in(r100_in), .r17_in(r101_in), .r18_in(r102_in), .r19_in(r103_in), .r20_in(r104_in), .r21_in(r105_in), .r22_in(r106_in), .r23_in(r107_in), .r24_in(r108_in), .r25_in(r109_in), .r26_in(r110_in), .r27_in(r111_in), .valid_out(sb_v[ 3]), .y0_out(sb_y0[ 3]), .y1_out(sb_y1[ 3]));
    masked_sbox_first_order u_sbox_4  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 32 +: 8]), .x1_in(x1_in[ 32 +: 8]), .r0_in(r112_in), .r1_in(r113_in), .r2_in(r114_in), .r3_in(r115_in), .r4_in(r116_in), .r5_in(r117_in), .r6_in(r118_in), .r7_in(r119_in), .r8_in(r120_in), .r9_in(r121_in), .r10_in(r122_in), .r11_in(r123_in), .r12_in(r124_in), .r13_in(r125_in), .r14_in(r126_in), .r15_in(r127_in), .r16_in(r128_in), .r17_in(r129_in), .r18_in(r130_in), .r19_in(r131_in), .r20_in(r132_in), .r21_in(r133_in), .r22_in(r134_in), .r23_in(r135_in), .r24_in(r136_in), .r25_in(r137_in), .r26_in(r138_in), .r27_in(r139_in), .valid_out(sb_v[ 4]), .y0_out(sb_y0[ 4]), .y1_out(sb_y1[ 4]));
    masked_sbox_first_order u_sbox_5  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 40 +: 8]), .x1_in(x1_in[ 40 +: 8]), .r0_in(r140_in), .r1_in(r141_in), .r2_in(r142_in), .r3_in(r143_in), .r4_in(r144_in), .r5_in(r145_in), .r6_in(r146_in), .r7_in(r147_in), .r8_in(r148_in), .r9_in(r149_in), .r10_in(r150_in), .r11_in(r151_in), .r12_in(r152_in), .r13_in(r153_in), .r14_in(r154_in), .r15_in(r155_in), .r16_in(r156_in), .r17_in(r157_in), .r18_in(r158_in), .r19_in(r159_in), .r20_in(r160_in), .r21_in(r161_in), .r22_in(r162_in), .r23_in(r163_in), .r24_in(r164_in), .r25_in(r165_in), .r26_in(r166_in), .r27_in(r167_in), .valid_out(sb_v[ 5]), .y0_out(sb_y0[ 5]), .y1_out(sb_y1[ 5]));
    masked_sbox_first_order u_sbox_6  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 48 +: 8]), .x1_in(x1_in[ 48 +: 8]), .r0_in(r168_in), .r1_in(r169_in), .r2_in(r170_in), .r3_in(r171_in), .r4_in(r172_in), .r5_in(r173_in), .r6_in(r174_in), .r7_in(r175_in), .r8_in(r176_in), .r9_in(r177_in), .r10_in(r178_in), .r11_in(r179_in), .r12_in(r180_in), .r13_in(r181_in), .r14_in(r182_in), .r15_in(r183_in), .r16_in(r184_in), .r17_in(r185_in), .r18_in(r186_in), .r19_in(r187_in), .r20_in(r188_in), .r21_in(r189_in), .r22_in(r190_in), .r23_in(r191_in), .r24_in(r192_in), .r25_in(r193_in), .r26_in(r194_in), .r27_in(r195_in), .valid_out(sb_v[ 6]), .y0_out(sb_y0[ 6]), .y1_out(sb_y1[ 6]));
    masked_sbox_first_order u_sbox_7  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 56 +: 8]), .x1_in(x1_in[ 56 +: 8]), .r0_in(r196_in), .r1_in(r197_in), .r2_in(r198_in), .r3_in(r199_in), .r4_in(r200_in), .r5_in(r201_in), .r6_in(r202_in), .r7_in(r203_in), .r8_in(r204_in), .r9_in(r205_in), .r10_in(r206_in), .r11_in(r207_in), .r12_in(r208_in), .r13_in(r209_in), .r14_in(r210_in), .r15_in(r211_in), .r16_in(r212_in), .r17_in(r213_in), .r18_in(r214_in), .r19_in(r215_in), .r20_in(r216_in), .r21_in(r217_in), .r22_in(r218_in), .r23_in(r219_in), .r24_in(r220_in), .r25_in(r221_in), .r26_in(r222_in), .r27_in(r223_in), .valid_out(sb_v[ 7]), .y0_out(sb_y0[ 7]), .y1_out(sb_y1[ 7]));
    masked_sbox_first_order u_sbox_8  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 64 +: 8]), .x1_in(x1_in[ 64 +: 8]), .r0_in(r224_in), .r1_in(r225_in), .r2_in(r226_in), .r3_in(r227_in), .r4_in(r228_in), .r5_in(r229_in), .r6_in(r230_in), .r7_in(r231_in), .r8_in(r232_in), .r9_in(r233_in), .r10_in(r234_in), .r11_in(r235_in), .r12_in(r236_in), .r13_in(r237_in), .r14_in(r238_in), .r15_in(r239_in), .r16_in(r240_in), .r17_in(r241_in), .r18_in(r242_in), .r19_in(r243_in), .r20_in(r244_in), .r21_in(r245_in), .r22_in(r246_in), .r23_in(r247_in), .r24_in(r248_in), .r25_in(r249_in), .r26_in(r250_in), .r27_in(r251_in), .valid_out(sb_v[ 8]), .y0_out(sb_y0[ 8]), .y1_out(sb_y1[ 8]));
    masked_sbox_first_order u_sbox_9  (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 72 +: 8]), .x1_in(x1_in[ 72 +: 8]), .r0_in(r252_in), .r1_in(r253_in), .r2_in(r254_in), .r3_in(r255_in), .r4_in(r256_in), .r5_in(r257_in), .r6_in(r258_in), .r7_in(r259_in), .r8_in(r260_in), .r9_in(r261_in), .r10_in(r262_in), .r11_in(r263_in), .r12_in(r264_in), .r13_in(r265_in), .r14_in(r266_in), .r15_in(r267_in), .r16_in(r268_in), .r17_in(r269_in), .r18_in(r270_in), .r19_in(r271_in), .r20_in(r272_in), .r21_in(r273_in), .r22_in(r274_in), .r23_in(r275_in), .r24_in(r276_in), .r25_in(r277_in), .r26_in(r278_in), .r27_in(r279_in), .valid_out(sb_v[ 9]), .y0_out(sb_y0[ 9]), .y1_out(sb_y1[ 9]));
    masked_sbox_first_order u_sbox_10 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 80 +: 8]), .x1_in(x1_in[ 80 +: 8]), .r0_in(r280_in), .r1_in(r281_in), .r2_in(r282_in), .r3_in(r283_in), .r4_in(r284_in), .r5_in(r285_in), .r6_in(r286_in), .r7_in(r287_in), .r8_in(r288_in), .r9_in(r289_in), .r10_in(r290_in), .r11_in(r291_in), .r12_in(r292_in), .r13_in(r293_in), .r14_in(r294_in), .r15_in(r295_in), .r16_in(r296_in), .r17_in(r297_in), .r18_in(r298_in), .r19_in(r299_in), .r20_in(r300_in), .r21_in(r301_in), .r22_in(r302_in), .r23_in(r303_in), .r24_in(r304_in), .r25_in(r305_in), .r26_in(r306_in), .r27_in(r307_in), .valid_out(sb_v[10]), .y0_out(sb_y0[10]), .y1_out(sb_y1[10]));
    masked_sbox_first_order u_sbox_11 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 88 +: 8]), .x1_in(x1_in[ 88 +: 8]), .r0_in(r308_in), .r1_in(r309_in), .r2_in(r310_in), .r3_in(r311_in), .r4_in(r312_in), .r5_in(r313_in), .r6_in(r314_in), .r7_in(r315_in), .r8_in(r316_in), .r9_in(r317_in), .r10_in(r318_in), .r11_in(r319_in), .r12_in(r320_in), .r13_in(r321_in), .r14_in(r322_in), .r15_in(r323_in), .r16_in(r324_in), .r17_in(r325_in), .r18_in(r326_in), .r19_in(r327_in), .r20_in(r328_in), .r21_in(r329_in), .r22_in(r330_in), .r23_in(r331_in), .r24_in(r332_in), .r25_in(r333_in), .r26_in(r334_in), .r27_in(r335_in), .valid_out(sb_v[11]), .y0_out(sb_y0[11]), .y1_out(sb_y1[11]));
    masked_sbox_first_order u_sbox_12 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[ 96 +: 8]), .x1_in(x1_in[ 96 +: 8]), .r0_in(r336_in), .r1_in(r337_in), .r2_in(r338_in), .r3_in(r339_in), .r4_in(r340_in), .r5_in(r341_in), .r6_in(r342_in), .r7_in(r343_in), .r8_in(r344_in), .r9_in(r345_in), .r10_in(r346_in), .r11_in(r347_in), .r12_in(r348_in), .r13_in(r349_in), .r14_in(r350_in), .r15_in(r351_in), .r16_in(r352_in), .r17_in(r353_in), .r18_in(r354_in), .r19_in(r355_in), .r20_in(r356_in), .r21_in(r357_in), .r22_in(r358_in), .r23_in(r359_in), .r24_in(r360_in), .r25_in(r361_in), .r26_in(r362_in), .r27_in(r363_in), .valid_out(sb_v[12]), .y0_out(sb_y0[12]), .y1_out(sb_y1[12]));
    masked_sbox_first_order u_sbox_13 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[104 +: 8]), .x1_in(x1_in[104 +: 8]), .r0_in(r364_in), .r1_in(r365_in), .r2_in(r366_in), .r3_in(r367_in), .r4_in(r368_in), .r5_in(r369_in), .r6_in(r370_in), .r7_in(r371_in), .r8_in(r372_in), .r9_in(r373_in), .r10_in(r374_in), .r11_in(r375_in), .r12_in(r376_in), .r13_in(r377_in), .r14_in(r378_in), .r15_in(r379_in), .r16_in(r380_in), .r17_in(r381_in), .r18_in(r382_in), .r19_in(r383_in), .r20_in(r384_in), .r21_in(r385_in), .r22_in(r386_in), .r23_in(r387_in), .r24_in(r388_in), .r25_in(r389_in), .r26_in(r390_in), .r27_in(r391_in), .valid_out(sb_v[13]), .y0_out(sb_y0[13]), .y1_out(sb_y1[13]));
    masked_sbox_first_order u_sbox_14 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[112 +: 8]), .x1_in(x1_in[112 +: 8]), .r0_in(r392_in), .r1_in(r393_in), .r2_in(r394_in), .r3_in(r395_in), .r4_in(r396_in), .r5_in(r397_in), .r6_in(r398_in), .r7_in(r399_in), .r8_in(r400_in), .r9_in(r401_in), .r10_in(r402_in), .r11_in(r403_in), .r12_in(r404_in), .r13_in(r405_in), .r14_in(r406_in), .r15_in(r407_in), .r16_in(r408_in), .r17_in(r409_in), .r18_in(r410_in), .r19_in(r411_in), .r20_in(r412_in), .r21_in(r413_in), .r22_in(r414_in), .r23_in(r415_in), .r24_in(r416_in), .r25_in(r417_in), .r26_in(r418_in), .r27_in(r419_in), .valid_out(sb_v[14]), .y0_out(sb_y0[14]), .y1_out(sb_y1[14]));
    masked_sbox_first_order u_sbox_15 (.clk(clk), .rst_n(rst_n), .valid_in(valid_in), .x0_in(x0_in[120 +: 8]), .x1_in(x1_in[120 +: 8]), .r0_in(r420_in), .r1_in(r421_in), .r2_in(r422_in), .r3_in(r423_in), .r4_in(r424_in), .r5_in(r425_in), .r6_in(r426_in), .r7_in(r427_in), .r8_in(r428_in), .r9_in(r429_in), .r10_in(r430_in), .r11_in(r431_in), .r12_in(r432_in), .r13_in(r433_in), .r14_in(r434_in), .r15_in(r435_in), .r16_in(r436_in), .r17_in(r437_in), .r18_in(r438_in), .r19_in(r439_in), .r20_in(r440_in), .r21_in(r441_in), .r22_in(r442_in), .r23_in(r443_in), .r24_in(r444_in), .r25_in(r445_in), .r26_in(r446_in), .r27_in(r447_in), .valid_out(sb_v[15]), .y0_out(sb_y0[15]), .y1_out(sb_y1[15]));

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
    wire [127:0] sr_state_y0, sr_state_y1;
    assign sr_state_y0[  0 +: 8] = sb_state_y0[  0 +: 8];
    assign sr_state_y0[  1 +: 8] = sb_state_y0[ 13 +: 8];
    assign sr_state_y0[  2 +: 8] = sb_state_y0[ 10 +: 8];
    assign sr_state_y0[  3 +: 8] = sb_state_y0[  7 +: 8];
    assign sr_state_y0[  4 +: 8] = sb_state_y0[  4 +: 8];
    assign sr_state_y0[  5 +: 8] = sb_state_y0[  1 +: 8];
    assign sr_state_y0[  6 +: 8] = sb_state_y0[ 14 +: 8];
    assign sr_state_y0[  7 +: 8] = sb_state_y0[ 11 +: 8];
    assign sr_state_y0[  8 +: 8] = sb_state_y0[  8 +: 8];
    assign sr_state_y0[  9 +: 8] = sb_state_y0[  5 +: 8];
    assign sr_state_y0[ 10 +: 8] = sb_state_y0[  2 +: 8];
    assign sr_state_y0[ 11 +: 8] = sb_state_y0[ 15 +: 8];
    assign sr_state_y0[ 12 +: 8] = sb_state_y0[ 12 +: 8];
    assign sr_state_y0[ 13 +: 8] = sb_state_y0[  9 +: 8];
    assign sr_state_y0[ 14 +: 8] = sb_state_y0[  6 +: 8];
    assign sr_state_y0[ 15 +: 8] = sb_state_y0[  3 +: 8];

    assign sr_state_y1[  0 +: 8] = sb_state_y1[  0 +: 8];
    assign sr_state_y1[  1 +: 8] = sb_state_y1[ 13 +: 8];
    assign sr_state_y1[  2 +: 8] = sb_state_y1[ 10 +: 8];
    assign sr_state_y1[  3 +: 8] = sb_state_y1[  7 +: 8];
    assign sr_state_y1[  4 +: 8] = sb_state_y1[  4 +: 8];
    assign sr_state_y1[  5 +: 8] = sb_state_y1[  1 +: 8];
    assign sr_state_y1[  6 +: 8] = sb_state_y1[ 14 +: 8];
    assign sr_state_y1[  7 +: 8] = sb_state_y1[ 11 +: 8];
    assign sr_state_y1[  8 +: 8] = sb_state_y1[  8 +: 8];
    assign sr_state_y1[  9 +: 8] = sb_state_y1[  5 +: 8];
    assign sr_state_y1[ 10 +: 8] = sb_state_y1[  2 +: 8];
    assign sr_state_y1[ 11 +: 8] = sb_state_y1[ 15 +: 8];
    assign sr_state_y1[ 12 +: 8] = sb_state_y1[ 12 +: 8];
    assign sr_state_y1[ 13 +: 8] = sb_state_y1[  9 +: 8];
    assign sr_state_y1[ 14 +: 8] = sb_state_y1[  6 +: 8];
    assign sr_state_y1[ 15 +: 8] = sb_state_y1[  3 +: 8];

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

    // --- Column 0 (bytes 0..3) ---
    assign mc_state_y0[ 0 +: 8] = xtime_f(sr_state_y0[ 0 +: 8])
                                 ^ (xtime_f(sr_state_y0[ 1 +: 8]) ^ sr_state_y0[ 1 +: 8])
                                 ^ sr_state_y0[ 2 +: 8]
                                 ^ sr_state_y0[ 3 +: 8];
    assign mc_state_y0[ 1 +: 8] = sr_state_y0[ 0 +: 8]
                                 ^ xtime_f(sr_state_y0[ 1 +: 8])
                                 ^ (xtime_f(sr_state_y0[ 2 +: 8]) ^ sr_state_y0[ 2 +: 8])
                                 ^ sr_state_y0[ 3 +: 8];
    assign mc_state_y0[ 2 +: 8] = sr_state_y0[ 0 +: 8]
                                 ^ sr_state_y0[ 1 +: 8]
                                 ^ xtime_f(sr_state_y0[ 2 +: 8])
                                 ^ (xtime_f(sr_state_y0[ 3 +: 8]) ^ sr_state_y0[ 3 +: 8]);
    assign mc_state_y0[ 3 +: 8] = (xtime_f(sr_state_y0[ 0 +: 8]) ^ sr_state_y0[ 0 +: 8])
                                 ^ sr_state_y0[ 1 +: 8]
                                 ^ sr_state_y0[ 2 +: 8]
                                 ^ xtime_f(sr_state_y0[ 3 +: 8]);

    // --- Column 1 (bytes 4..7) ---
    assign mc_state_y0[ 4 +: 8] = xtime_f(sr_state_y0[ 4 +: 8])
                                 ^ (xtime_f(sr_state_y0[ 5 +: 8]) ^ sr_state_y0[ 5 +: 8])
                                 ^ sr_state_y0[ 6 +: 8]
                                 ^ sr_state_y0[ 7 +: 8];
    assign mc_state_y0[ 5 +: 8] = sr_state_y0[ 4 +: 8]
                                 ^ xtime_f(sr_state_y0[ 5 +: 8])
                                 ^ (xtime_f(sr_state_y0[ 6 +: 8]) ^ sr_state_y0[ 6 +: 8])
                                 ^ sr_state_y0[ 7 +: 8];
    assign mc_state_y0[ 6 +: 8] = sr_state_y0[ 4 +: 8]
                                 ^ sr_state_y0[ 5 +: 8]
                                 ^ xtime_f(sr_state_y0[ 6 +: 8])
                                 ^ (xtime_f(sr_state_y0[ 7 +: 8]) ^ sr_state_y0[ 7 +: 8]);
    assign mc_state_y0[ 7 +: 8] = (xtime_f(sr_state_y0[ 4 +: 8]) ^ sr_state_y0[ 4 +: 8])
                                 ^ sr_state_y0[ 5 +: 8]
                                 ^ sr_state_y0[ 6 +: 8]
                                 ^ xtime_f(sr_state_y0[ 7 +: 8]);

    // --- Column 2 (bytes 8..11) ---
    assign mc_state_y0[ 8 +: 8] = xtime_f(sr_state_y0[ 8 +: 8])
                                 ^ (xtime_f(sr_state_y0[ 9 +: 8]) ^ sr_state_y0[ 9 +: 8])
                                 ^ sr_state_y0[10 +: 8]
                                 ^ sr_state_y0[11 +: 8];
    assign mc_state_y0[ 9 +: 8] = sr_state_y0[ 8 +: 8]
                                 ^ xtime_f(sr_state_y0[ 9 +: 8])
                                 ^ (xtime_f(sr_state_y0[10 +: 8]) ^ sr_state_y0[10 +: 8])
                                 ^ sr_state_y0[11 +: 8];
    assign mc_state_y0[10 +: 8] = sr_state_y0[ 8 +: 8]
                                 ^ sr_state_y0[ 9 +: 8]
                                 ^ xtime_f(sr_state_y0[10 +: 8])
                                 ^ (xtime_f(sr_state_y0[11 +: 8]) ^ sr_state_y0[11 +: 8]);
    assign mc_state_y0[11 +: 8] = (xtime_f(sr_state_y0[ 8 +: 8]) ^ sr_state_y0[ 8 +: 8])
                                 ^ sr_state_y0[ 9 +: 8]
                                 ^ sr_state_y0[10 +: 8]
                                 ^ xtime_f(sr_state_y0[11 +: 8]);

    // --- Column 3 (bytes 12..15) ---
    assign mc_state_y0[12 +: 8] = xtime_f(sr_state_y0[12 +: 8])
                                 ^ (xtime_f(sr_state_y0[13 +: 8]) ^ sr_state_y0[13 +: 8])
                                 ^ sr_state_y0[14 +: 8]
                                 ^ sr_state_y0[15 +: 8];
    assign mc_state_y0[13 +: 8] = sr_state_y0[12 +: 8]
                                 ^ xtime_f(sr_state_y0[13 +: 8])
                                 ^ (xtime_f(sr_state_y0[14 +: 8]) ^ sr_state_y0[14 +: 8])
                                 ^ sr_state_y0[15 +: 8];
    assign mc_state_y0[14 +: 8] = sr_state_y0[12 +: 8]
                                 ^ sr_state_y0[13 +: 8]
                                 ^ xtime_f(sr_state_y0[14 +: 8])
                                 ^ (xtime_f(sr_state_y0[15 +: 8]) ^ sr_state_y0[15 +: 8]);
    assign mc_state_y0[15 +: 8] = (xtime_f(sr_state_y0[12 +: 8]) ^ sr_state_y0[12 +: 8])
                                 ^ sr_state_y0[13 +: 8]
                                 ^ sr_state_y0[14 +: 8]
                                 ^ xtime_f(sr_state_y0[15 +: 8]);

    // --- Share 1 (same column mixes) ---
    assign mc_state_y1[ 0 +: 8] = xtime_f(sr_state_y1[ 0 +: 8])
                                 ^ (xtime_f(sr_state_y1[ 1 +: 8]) ^ sr_state_y1[ 1 +: 8])
                                 ^ sr_state_y1[ 2 +: 8]
                                 ^ sr_state_y1[ 3 +: 8];
    assign mc_state_y1[ 1 +: 8] = sr_state_y1[ 0 +: 8]
                                 ^ xtime_f(sr_state_y1[ 1 +: 8])
                                 ^ (xtime_f(sr_state_y1[ 2 +: 8]) ^ sr_state_y1[ 2 +: 8])
                                 ^ sr_state_y1[ 3 +: 8];
    assign mc_state_y1[ 2 +: 8] = sr_state_y1[ 0 +: 8]
                                 ^ sr_state_y1[ 1 +: 8]
                                 ^ xtime_f(sr_state_y1[ 2 +: 8])
                                 ^ (xtime_f(sr_state_y1[ 3 +: 8]) ^ sr_state_y1[ 3 +: 8]);
    assign mc_state_y1[ 3 +: 8] = (xtime_f(sr_state_y1[ 0 +: 8]) ^ sr_state_y1[ 0 +: 8])
                                 ^ sr_state_y1[ 1 +: 8]
                                 ^ sr_state_y1[ 2 +: 8]
                                 ^ xtime_f(sr_state_y1[ 3 +: 8]);

    assign mc_state_y1[ 4 +: 8] = xtime_f(sr_state_y1[ 4 +: 8])
                                 ^ (xtime_f(sr_state_y1[ 5 +: 8]) ^ sr_state_y1[ 5 +: 8])
                                 ^ sr_state_y1[ 6 +: 8]
                                 ^ sr_state_y1[ 7 +: 8];
    assign mc_state_y1[ 5 +: 8] = sr_state_y1[ 4 +: 8]
                                 ^ xtime_f(sr_state_y1[ 5 +: 8])
                                 ^ (xtime_f(sr_state_y1[ 6 +: 8]) ^ sr_state_y1[ 6 +: 8])
                                 ^ sr_state_y1[ 7 +: 8];
    assign mc_state_y1[ 6 +: 8] = sr_state_y1[ 4 +: 8]
                                 ^ sr_state_y1[ 5 +: 8]
                                 ^ xtime_f(sr_state_y1[ 6 +: 8])
                                 ^ (xtime_f(sr_state_y1[ 7 +: 8]) ^ sr_state_y1[ 7 +: 8]);
    assign mc_state_y1[ 7 +: 8] = (xtime_f(sr_state_y1[ 4 +: 8]) ^ sr_state_y1[ 4 +: 8])
                                 ^ sr_state_y1[ 5 +: 8]
                                 ^ sr_state_y1[ 6 +: 8]
                                 ^ xtime_f(sr_state_y1[ 7 +: 8]);

    assign mc_state_y1[ 8 +: 8] = xtime_f(sr_state_y1[ 8 +: 8])
                                 ^ (xtime_f(sr_state_y1[ 9 +: 8]) ^ sr_state_y1[ 9 +: 8])
                                 ^ sr_state_y1[10 +: 8]
                                 ^ sr_state_y1[11 +: 8];
    assign mc_state_y1[ 9 +: 8] = sr_state_y1[ 8 +: 8]
                                 ^ xtime_f(sr_state_y1[ 9 +: 8])
                                 ^ (xtime_f(sr_state_y1[10 +: 8]) ^ sr_state_y1[10 +: 8])
                                 ^ sr_state_y1[11 +: 8];
    assign mc_state_y1[10 +: 8] = sr_state_y1[ 8 +: 8]
                                 ^ sr_state_y1[ 9 +: 8]
                                 ^ xtime_f(sr_state_y1[10 +: 8])
                                 ^ (xtime_f(sr_state_y1[11 +: 8]) ^ sr_state_y1[11 +: 8]);
    assign mc_state_y1[11 +: 8] = (xtime_f(sr_state_y1[ 8 +: 8]) ^ sr_state_y1[ 8 +: 8])
                                 ^ sr_state_y1[ 9 +: 8]
                                 ^ sr_state_y1[10 +: 8]
                                 ^ xtime_f(sr_state_y1[11 +: 8]);

    assign mc_state_y1[12 +: 8] = xtime_f(sr_state_y1[12 +: 8])
                                 ^ (xtime_f(sr_state_y1[13 +: 8]) ^ sr_state_y1[13 +: 8])
                                 ^ sr_state_y1[14 +: 8]
                                 ^ sr_state_y1[15 +: 8];
    assign mc_state_y1[13 +: 8] = sr_state_y1[12 +: 8]
                                 ^ xtime_f(sr_state_y1[13 +: 8])
                                 ^ (xtime_f(sr_state_y1[14 +: 8]) ^ sr_state_y1[14 +: 8])
                                 ^ sr_state_y1[15 +: 8];
    assign mc_state_y1[14 +: 8] = sr_state_y1[12 +: 8]
                                 ^ sr_state_y1[13 +: 8]
                                 ^ xtime_f(sr_state_y1[14 +: 8])
                                 ^ (xtime_f(sr_state_y1[15 +: 8]) ^ sr_state_y1[15 +: 8]);
    assign mc_state_y1[15 +: 8] = (xtime_f(sr_state_y1[12 +: 8]) ^ sr_state_y1[12 +: 8])
                                 ^ sr_state_y1[13 +: 8]
                                 ^ sr_state_y1[14 +: 8]
                                 ^ xtime_f(sr_state_y1[15 +: 8]);

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

    // valid_out: combinational from sb_v_all.  12-cycle data
    // latency = 10 (S-box pipeline) + 1 (ARK) + 1 (output register).
    assign valid_out = sb_v_all;

endmodule

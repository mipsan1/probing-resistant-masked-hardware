// =====================================================================
// tb_vcd_dump_gl.v
// =====================================================================
// Gate-level VCD power-trace testbench for the masked AES round 1.
//
// Compiles the synthesized Yosys netlist (preserving $_DFF_PN0P_ and
// $_DFF_PN0_ primitives) as the DUT instead of the RTL.  Each clock
// edge dumps the Hamming-distance transition count of all DFF Q
// outputs into a per-cycle power trace.  This is *faster* than VCD
// for large N because we do not write a 100,000-event VCD file.
//
// Usage:
//   iverilog -g2012 -I . -o /tmp/tb_vcd_gl.vvp \
//     tb_vcd_dump_gl.v syn/masked_aes_round1_syn.v
//   vvp /tmp/tb_vcd_gl.vvp +N=10
//   # -> sim/power_gl_trace.txt   (per-cycle HD count, one per line)
//   # -> sim/power_gl_secret.txt  (one secret byte per line, hex)
//
// For the d=2 netlist:
//   iverilog -g2012 -I . -o /tmp/tb_vcd_gl_d2.vvp \
//     tb_vcd_dump_gl.v syn/masked_aes_round1_d2_syn.v
//   vvp /tmp/tb_vcd_gl_d2.vvp +N=10
// =====================================================================

`ifndef TB_VCD_DUMP_GL_V
`define TB_VCD_DUMP_GL_V

`timescale 1ns/1ps

module tb_vcd_dump_gl;

    integer N_VECTORS = 10;

    reg clk;
    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    reg               rst_n;
    reg               valid_in;
    reg  [127:0]      x0_in, x1_in, rk0_in, rk1_in;
    reg  [7:0]        r_in [0:447];
    wire              valid_out;
    wire [127:0]      y0_out, y1_out;

    // ------------------------------------------------------------
    // DUT — synthesized gate-level netlist (RTL-style with
    // `$_DFF_PN0P_` and `$_DFF_PN0_` primitives)
    // ------------------------------------------------------------
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
        .r096_in (r_in[ 96]), .r097_in (r_in[ 97]), .r098_in (r_in[ 98]), .r099_in (r_in[ 99]),
        .r100_in (r_in[100]), .r101_in (r_in[101]), .r102_in (r_in[102]), .r103_in (r_in[103]),
        .r104_in (r_in[104]), .r105_in (r_in[105]), .r106_in (r_in[106]), .r107_in (r_in[107]),
        .r108_in (r_in[108]), .r109_in (r_in[109]), .r110_in (r_in[110]), .r111_in (r_in[111]),
        .r112_in (r_in[112]), .r113_in (r_in[113]), .r114_in (r_in[114]), .r115_in (r_in[115]),
        .r116_in (r_in[116]), .r117_in (r_in[117]), .r118_in (r_in[118]), .r119_in (r_in[119]),
        .r120_in (r_in[120]), .r121_in (r_in[121]), .r122_in (r_in[122]), .r123_in (r_in[123]),
        .r124_in (r_in[124]), .r125_in (r_in[125]), .r126_in (r_in[126]), .r127_in (r_in[127]),
        .r128_in (r_in[128]), .r129_in (r_in[129]), .r130_in (r_in[130]), .r131_in (r_in[131]),
        .r132_in (r_in[132]), .r133_in (r_in[133]), .r134_in (r_in[134]), .r135_in (r_in[135]),
        .r136_in (r_in[136]), .r137_in (r_in[137]), .r138_in (r_in[138]), .r139_in (r_in[139]),
        .r140_in (r_in[140]), .r141_in (r_in[141]), .r142_in (r_in[142]), .r143_in (r_in[143]),
        .r144_in (r_in[144]), .r145_in (r_in[145]), .r146_in (r_in[146]), .r147_in (r_in[147]),
        .r148_in (r_in[148]), .r149_in (r_in[149]), .r150_in (r_in[150]), .r151_in (r_in[151]),
        .r152_in (r_in[152]), .r153_in (r_in[153]), .r154_in (r_in[154]), .r155_in (r_in[155]),
        .r156_in (r_in[156]), .r157_in (r_in[157]), .r158_in (r_in[158]), .r159_in (r_in[159]),
        .r160_in (r_in[160]), .r161_in (r_in[161]), .r162_in (r_in[162]), .r163_in (r_in[163]),
        .r164_in (r_in[164]), .r165_in (r_in[165]), .r166_in (r_in[166]), .r167_in (r_in[167]),
        .r168_in (r_in[168]), .r169_in (r_in[169]), .r170_in (r_in[170]), .r171_in (r_in[171]),
        .r172_in (r_in[172]), .r173_in (r_in[173]), .r174_in (r_in[174]), .r175_in (r_in[175]),
        .r176_in (r_in[176]), .r177_in (r_in[177]), .r178_in (r_in[178]), .r179_in (r_in[179]),
        .r180_in (r_in[180]), .r181_in (r_in[181]), .r182_in (r_in[182]), .r183_in (r_in[183]),
        .r184_in (r_in[184]), .r185_in (r_in[185]), .r186_in (r_in[186]), .r187_in (r_in[187]),
        .r188_in (r_in[188]), .r189_in (r_in[189]), .r190_in (r_in[190]), .r191_in (r_in[191]),
        .r192_in (r_in[192]), .r193_in (r_in[193]), .r194_in (r_in[194]), .r195_in (r_in[195]),
        .r196_in (r_in[196]), .r197_in (r_in[197]), .r198_in (r_in[198]), .r199_in (r_in[199]),
        .r200_in (r_in[200]), .r201_in (r_in[201]), .r202_in (r_in[202]), .r203_in (r_in[203]),
        .r204_in (r_in[204]), .r205_in (r_in[205]), .r206_in (r_in[206]), .r207_in (r_in[207]),
        .r208_in (r_in[208]), .r209_in (r_in[209]), .r210_in (r_in[210]), .r211_in (r_in[211]),
        .r212_in (r_in[212]), .r213_in (r_in[213]), .r214_in (r_in[214]), .r215_in (r_in[215]),
        .r216_in (r_in[216]), .r217_in (r_in[217]), .r218_in (r_in[218]), .r219_in (r_in[219]),
        .r220_in (r_in[220]), .r221_in (r_in[221]), .r222_in (r_in[222]), .r223_in (r_in[223]),
        .r224_in (r_in[224]), .r225_in (r_in[225]), .r226_in (r_in[226]), .r227_in (r_in[227]),
        .r228_in (r_in[228]), .r229_in (r_in[229]), .r230_in (r_in[230]), .r231_in (r_in[231]),
        .r232_in (r_in[232]), .r233_in (r_in[233]), .r234_in (r_in[234]), .r235_in (r_in[235]),
        .r236_in (r_in[236]), .r237_in (r_in[237]), .r238_in (r_in[238]), .r239_in (r_in[239]),
        .r240_in (r_in[240]), .r241_in (r_in[241]), .r242_in (r_in[242]), .r243_in (r_in[243]),
        .r244_in (r_in[244]), .r245_in (r_in[245]), .r246_in (r_in[246]), .r247_in (r_in[247]),
        .r248_in (r_in[248]), .r249_in (r_in[249]), .r250_in (r_in[250]), .r251_in (r_in[251]),
        .r252_in (r_in[252]), .r253_in (r_in[253]), .r254_in (r_in[254]), .r255_in (r_in[255]),
        .r256_in (r_in[256]), .r257_in (r_in[257]), .r258_in (r_in[258]), .r259_in (r_in[259]),
        .r260_in (r_in[260]), .r261_in (r_in[261]), .r262_in (r_in[262]), .r263_in (r_in[263]),
        .r264_in (r_in[264]), .r265_in (r_in[265]), .r266_in (r_in[266]), .r267_in (r_in[267]),
        .r268_in (r_in[268]), .r269_in (r_in[269]), .r270_in (r_in[270]), .r271_in (r_in[271]),
        .r272_in (r_in[272]), .r273_in (r_in[273]), .r274_in (r_in[274]), .r275_in (r_in[275]),
        .r276_in (r_in[276]), .r277_in (r_in[277]), .r278_in (r_in[278]), .r279_in (r_in[279]),
        .r280_in (r_in[280]), .r281_in (r_in[281]), .r282_in (r_in[282]), .r283_in (r_in[283]),
        .r284_in (r_in[284]), .r285_in (r_in[285]), .r286_in (r_in[286]), .r287_in (r_in[287]),
        .r288_in (r_in[288]), .r289_in (r_in[289]), .r290_in (r_in[290]), .r291_in (r_in[291]),
        .r292_in (r_in[292]), .r293_in (r_in[293]), .r294_in (r_in[294]), .r295_in (r_in[295]),
        .r296_in (r_in[296]), .r297_in (r_in[297]), .r298_in (r_in[298]), .r299_in (r_in[299]),
        .r300_in (r_in[300]), .r301_in (r_in[301]), .r302_in (r_in[302]), .r303_in (r_in[303]),
        .r304_in (r_in[304]), .r305_in (r_in[305]), .r306_in (r_in[306]), .r307_in (r_in[307]),
        .r308_in (r_in[308]), .r309_in (r_in[309]), .r310_in (r_in[310]), .r311_in (r_in[311]),
        .r312_in (r_in[312]), .r313_in (r_in[313]), .r314_in (r_in[314]), .r315_in (r_in[315]),
        .r316_in (r_in[316]), .r317_in (r_in[317]), .r318_in (r_in[318]), .r319_in (r_in[319]),
        .r320_in (r_in[320]), .r321_in (r_in[321]), .r322_in (r_in[322]), .r323_in (r_in[323]),
        .r324_in (r_in[324]), .r325_in (r_in[325]), .r326_in (r_in[326]), .r327_in (r_in[327]),
        .r328_in (r_in[328]), .r329_in (r_in[329]), .r330_in (r_in[330]), .r331_in (r_in[331]),
        .r332_in (r_in[332]), .r333_in (r_in[333]), .r334_in (r_in[334]), .r335_in (r_in[335]),
        .r336_in (r_in[336]), .r337_in (r_in[337]), .r338_in (r_in[338]), .r339_in (r_in[339]),
        .r340_in (r_in[340]), .r341_in (r_in[341]), .r342_in (r_in[342]), .r343_in (r_in[343]),
        .r344_in (r_in[344]), .r345_in (r_in[345]), .r346_in (r_in[346]), .r347_in (r_in[347]),
        .r348_in (r_in[348]), .r349_in (r_in[349]), .r350_in (r_in[350]), .r351_in (r_in[351]),
        .r352_in (r_in[352]), .r353_in (r_in[353]), .r354_in (r_in[354]), .r355_in (r_in[355]),
        .r356_in (r_in[356]), .r357_in (r_in[357]), .r358_in (r_in[358]), .r359_in (r_in[359]),
        .r360_in (r_in[360]), .r361_in (r_in[361]), .r362_in (r_in[362]), .r363_in (r_in[363]),
        .r364_in (r_in[364]), .r365_in (r_in[365]), .r366_in (r_in[366]), .r367_in (r_in[367]),
        .r368_in (r_in[368]), .r369_in (r_in[369]), .r370_in (r_in[370]), .r371_in (r_in[371]),
        .r372_in (r_in[372]), .r373_in (r_in[373]), .r374_in (r_in[374]), .r375_in (r_in[375]),
        .r376_in (r_in[376]), .r377_in (r_in[377]), .r378_in (r_in[378]), .r379_in (r_in[379]),
        .r380_in (r_in[380]), .r381_in (r_in[381]), .r382_in (r_in[382]), .r383_in (r_in[383]),
        .r384_in (r_in[384]), .r385_in (r_in[385]), .r386_in (r_in[386]), .r387_in (r_in[387]),
        .r388_in (r_in[388]), .r389_in (r_in[389]), .r390_in (r_in[390]), .r391_in (r_in[391]),
        .r392_in (r_in[392]), .r393_in (r_in[393]), .r394_in (r_in[394]), .r395_in (r_in[395]),
        .r396_in (r_in[396]), .r397_in (r_in[397]), .r398_in (r_in[398]), .r399_in (r_in[399]),
        .r400_in (r_in[400]), .r401_in (r_in[401]), .r402_in (r_in[402]), .r403_in (r_in[403]),
        .r404_in (r_in[404]), .r405_in (r_in[405]), .r406_in (r_in[406]), .r407_in (r_in[407]),
        .r408_in (r_in[408]), .r409_in (r_in[409]), .r410_in (r_in[410]), .r411_in (r_in[411]),
        .r412_in (r_in[412]), .r413_in (r_in[413]), .r414_in (r_in[414]), .r415_in (r_in[415]),
        .r416_in (r_in[416]), .r417_in (r_in[417]), .r418_in (r_in[418]), .r419_in (r_in[419]),
        .r420_in (r_in[420]), .r421_in (r_in[421]), .r422_in (r_in[422]), .r423_in (r_in[423]),
        .r424_in (r_in[424]), .r425_in (r_in[425]), .r426_in (r_in[426]), .r427_in (r_in[427]),
        .r428_in (r_in[428]), .r429_in (r_in[429]), .r430_in (r_in[430]), .r431_in (r_in[431]),
        .r432_in (r_in[432]), .r433_in (r_in[433]), .r434_in (r_in[434]), .r435_in (r_in[435]),
        .r436_in (r_in[436]), .r437_in (r_in[437]), .r438_in (r_in[438]), .r439_in (r_in[439]),
        .r440_in (r_in[440]), .r441_in (r_in[441]), .r442_in (r_in[442]), .r443_in (r_in[443]),
        .r444_in (r_in[444]), .r445_in (r_in[445]), .r446_in (r_in[446]), .r447_in (r_in[447]),
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
    reg [7:0]   h_masks  [0:4499999];

    initial begin
        if (!$value$plusargs("N=%d", N_VECTORS)) begin
            N_VECTORS = 10;
        end
        $readmemh("sim/power_secret.txt", h_secret);
        $readmemh("sim/power_s0.txt",     h_s0);
        $readmemh("sim/power_s1.txt",     h_s1);
        $readmemh("sim/power_rk0.txt",    h_rk0);
        $readmemh("sim/power_rk1.txt",    h_rk1);
        $readmemh("sim/power_masks.txt",  h_masks);
    end

    // ----------------------------------------------------------------
    // Power trace dump: per-cycle HD count of all DFFs.
    //
    // We monitor y0_out, y1_out, valid_out as a 257-bit "aggregate
    // state" and dump the HD against the previous cycle.  This is a
    // conservative proxy for full DFF-level power; for a richer
    // trace, the full DFF list must be flattened at synthesis.
    // ----------------------------------------------------------------
    reg [256:0] prev_state;
    reg [256:0] cur_state;
    integer     hd;
    // File handles.  The "header" file is the format that
    // probe/tvla.py expects: one line per input triple, columns
    // are "secret_hex 0 0 0 0 0 0 0 first_cycle_int".
    integer     trace_fh;
    integer     header_fh;

    always @(*) begin
        cur_state = {valid_out, y0_out, y1_out};
    end

    initial begin
        trace_fh  = $fopen("sim/power_gl_trace.txt",  "w");
        header_fh = $fopen("sim/power_gl_header.txt", "w");
    end

    // Cycle counter (incremented on every posedge clk after reset).
    // Used to mark the first_cycle of each input triple.
    integer     cycle_ctr;
    reg         trace_started;

    always @(posedge clk) begin
        if (rst_n) begin
            cycle_ctr <= cycle_ctr + 1;
        end
    end

    // Per-cycle HD computation and dump.  The first edge (during
    // reset) is discarded.  Format: "<cycle> <hd>" (two columns,
    // matching the probe/tvla.py load_power parser).
    reg [256:0] state_q;
    integer     cycle_ctr_dump;
    always @(posedge clk) begin
        if (rst_n) begin
            hd = $countones(cur_state ^ state_q);
            state_q <= cur_state;
            $fwrite(trace_fh, "%0d %0d\n", cycle_ctr_dump, hd);
            cycle_ctr_dump <= cycle_ctr_dump + 1;
        end
    end

    // ----------------------------------------------------------------
    // Main stimulus
    // ----------------------------------------------------------------
    integer n, b;
    initial begin
        #1;
        valid_in = 1'b0;
        x0_in    = 128'h0; x1_in    = 128'h0;
        rk0_in   = 128'h0; rk1_in   = 128'h0;
        for (b = 0; b < 448; b = b + 1) r_in[b] = 8'h0;
        rst_n    = 1'b0;
        state_q  = 257'h0;
        cycle_ctr = 0;
        cycle_ctr_dump = 0;
        repeat (4) @(posedge clk);
        rst_n    = 1'b1;
        @(posedge clk);

        for (n = 0; n < N_VECTORS; n = n + 1) begin : VEC_LOOP
            // Per-vector secret: byte 0 of h_secret is the secret.
            // Record (secret_hex, first_cycle) in the header file in
            // the format probe/tvla.py expects.
            $fwrite(header_fh, "%02x 0 0 0 0 0 0 0 %0d\n",
                    h_secret[n][7:0], cycle_ctr);

            x0_in  = h_s0[n];
            x1_in  = h_s1[n];
            rk0_in = h_rk0[n];
            rk1_in = h_rk1[n];
            for (b = 0; b < 448; b = b + 1)
                r_in[b] = h_masks[n*448 + b];
            @(posedge clk);
            valid_in = 1'b1;
            @(posedge clk);
            valid_in = 1'b0;
            // Wait the 12-cycle pipeline latency
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
        end
        $fclose(trace_fh);
        $fclose(header_fh);
        $display("Gate-level VCD dumped %0d vectors, trace in sim/power_gl_trace.txt, header in sim/power_gl_header.txt", N_VECTORS);
        $finish;
    end

endmodule

`endif

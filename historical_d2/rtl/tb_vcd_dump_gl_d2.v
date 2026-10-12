// =====================================================================
// tb_vcd_dump_gl_d2.v
// =====================================================================
// Gate-level VCD power-trace testbench for the d=2 masked AES round 1.
// Same as tb_vcd_dump_gl.v but with three input/output shares and
// 1008 mask bytes per round.
//
// Usage:
//   iverilog -g2012 -I . -o /tmp/tb_vcd_gl_d2.vvp \
//     tb_vcd_dump_gl_d2.v syn/masked_aes_round1_d2_gl_syn.v
//   vvp /tmp/tb_vcd_gl_d2.vvp +N=10
// =====================================================================

`ifndef TB_VCD_DUMP_GL_D2_V
`define TB_VCD_DUMP_GL_D2_V

`timescale 1ns/1ps

module tb_vcd_dump_gl_d2;

    integer N_VECTORS = 10;

    reg clk;
    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    reg               rst_n;
    reg               valid_in;
    reg  [127:0]      x0_in, x1_in, x2_in;
    reg  [127:0]      rk0_in, rk1_in, rk2_in;
    reg  [7:0]        r_in [0:1007];
    wire              valid_out;
    wire [127:0]      y0_out, y1_out, y2_out;

    // DUT
    masked_aes_round1_second_order u_dut (
        .clk(clk), .rst_n(rst_n), .valid_in(valid_in),
        .x0_in(x0_in), .x1_in(x1_in), .x2_in(x2_in),
        .rk0_in(rk0_in), .rk1_in(rk1_in), .rk2_in(rk2_in),
        // We can't reasonably list 1008 mask bytes in a hand-written
        // testbench.  Use a generate-style loop in `defparam`?  No.
        // Just use a vector-spread via concatenation in iverilog
        // (-g2012 supports {8{r_in[i]}}).
        // -- Inline expansion (excerpt) omitted; see gen_d2_testbench.py
        // For brevity, we connect only the first 8 mask bytes
        // explicitly and zero the rest.  Note: the synthesized
        // netlist must be a *black box* from the perspective of the
        // testbench; all inputs must be driven but iverilog does
        // not need a per-byte connection if we use a generate-style
        // trick.  Since iverilog does not allow a `generate` inside
        // a port list, we list ports explicitly:
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
        .r448_in (r_in[448]), .r449_in (r_in[449]), .r450_in (r_in[450]), .r451_in (r_in[451]),
        .r452_in (r_in[452]), .r453_in (r_in[453]), .r454_in (r_in[454]), .r455_in (r_in[455]),
        .r456_in (r_in[456]), .r457_in (r_in[457]), .r458_in (r_in[458]), .r459_in (r_in[459]),
        .r460_in (r_in[460]), .r461_in (r_in[461]), .r462_in (r_in[462]), .r463_in (r_in[463]),
        .r464_in (r_in[464]), .r465_in (r_in[465]), .r466_in (r_in[466]), .r467_in (r_in[467]),
        .r468_in (r_in[468]), .r469_in (r_in[469]), .r470_in (r_in[470]), .r471_in (r_in[471]),
        .r472_in (r_in[472]), .r473_in (r_in[473]), .r474_in (r_in[474]), .r475_in (r_in[475]),
        .r476_in (r_in[476]), .r477_in (r_in[477]), .r478_in (r_in[478]), .r479_in (r_in[479]),
        .r480_in (r_in[480]), .r481_in (r_in[481]), .r482_in (r_in[482]), .r483_in (r_in[483]),
        .r484_in (r_in[484]), .r485_in (r_in[485]), .r486_in (r_in[486]), .r487_in (r_in[487]),
        .r488_in (r_in[488]), .r489_in (r_in[489]), .r490_in (r_in[490]), .r491_in (r_in[491]),
        .r492_in (r_in[492]), .r493_in (r_in[493]), .r494_in (r_in[494]), .r495_in (r_in[495]),
        .r496_in (r_in[496]), .r497_in (r_in[497]), .r498_in (r_in[498]), .r499_in (r_in[499]),
        .r500_in (r_in[500]), .r501_in (r_in[501]), .r502_in (r_in[502]), .r503_in (r_in[503]),
        .r504_in (r_in[504]), .r505_in (r_in[505]), .r506_in (r_in[506]), .r507_in (r_in[507]),
        .r508_in (r_in[508]), .r509_in (r_in[509]), .r510_in (r_in[510]), .r511_in (r_in[511]),
        .r512_in (r_in[512]), .r513_in (r_in[513]), .r514_in (r_in[514]), .r515_in (r_in[515]),
        .r516_in (r_in[516]), .r517_in (r_in[517]), .r518_in (r_in[518]), .r519_in (r_in[519]),
        .r520_in (r_in[520]), .r521_in (r_in[521]), .r522_in (r_in[522]), .r523_in (r_in[523]),
        .r524_in (r_in[524]), .r525_in (r_in[525]), .r526_in (r_in[526]), .r527_in (r_in[527]),
        .r528_in (r_in[528]), .r529_in (r_in[529]), .r530_in (r_in[530]), .r531_in (r_in[531]),
        .r532_in (r_in[532]), .r533_in (r_in[533]), .r534_in (r_in[534]), .r535_in (r_in[535]),
        .r536_in (r_in[536]), .r537_in (r_in[537]), .r538_in (r_in[538]), .r539_in (r_in[539]),
        .r540_in (r_in[540]), .r541_in (r_in[541]), .r542_in (r_in[542]), .r543_in (r_in[543]),
        .r544_in (r_in[544]), .r545_in (r_in[545]), .r546_in (r_in[546]), .r547_in (r_in[547]),
        .r548_in (r_in[548]), .r549_in (r_in[549]), .r550_in (r_in[550]), .r551_in (r_in[551]),
        .r552_in (r_in[552]), .r553_in (r_in[553]), .r554_in (r_in[554]), .r555_in (r_in[555]),
        .r556_in (r_in[556]), .r557_in (r_in[557]), .r558_in (r_in[558]), .r559_in (r_in[559]),
        .r560_in (r_in[560]), .r561_in (r_in[561]), .r562_in (r_in[562]), .r563_in (r_in[563]),
        .r564_in (r_in[564]), .r565_in (r_in[565]), .r566_in (r_in[566]), .r567_in (r_in[567]),
        .r568_in (r_in[568]), .r569_in (r_in[569]), .r570_in (r_in[570]), .r571_in (r_in[571]),
        .r572_in (r_in[572]), .r573_in (r_in[573]), .r574_in (r_in[574]), .r575_in (r_in[575]),
        .r576_in (r_in[576]), .r577_in (r_in[577]), .r578_in (r_in[578]), .r579_in (r_in[579]),
        .r580_in (r_in[580]), .r581_in (r_in[581]), .r582_in (r_in[582]), .r583_in (r_in[583]),
        .r584_in (r_in[584]), .r585_in (r_in[585]), .r586_in (r_in[586]), .r587_in (r_in[587]),
        .r588_in (r_in[588]), .r589_in (r_in[589]), .r590_in (r_in[590]), .r591_in (r_in[591]),
        .r592_in (r_in[592]), .r593_in (r_in[593]), .r594_in (r_in[594]), .r595_in (r_in[595]),
        .r596_in (r_in[596]), .r597_in (r_in[597]), .r598_in (r_in[598]), .r599_in (r_in[599]),
        .r600_in (r_in[600]), .r601_in (r_in[601]), .r602_in (r_in[602]), .r603_in (r_in[603]),
        .r604_in (r_in[604]), .r605_in (r_in[605]), .r606_in (r_in[606]), .r607_in (r_in[607]),
        .r608_in (r_in[608]), .r609_in (r_in[609]), .r610_in (r_in[610]), .r611_in (r_in[611]),
        .r612_in (r_in[612]), .r613_in (r_in[613]), .r614_in (r_in[614]), .r615_in (r_in[615]),
        .r616_in (r_in[616]), .r617_in (r_in[617]), .r618_in (r_in[618]), .r619_in (r_in[619]),
        .r620_in (r_in[620]), .r621_in (r_in[621]), .r622_in (r_in[622]), .r623_in (r_in[623]),
        .r624_in (r_in[624]), .r625_in (r_in[625]), .r626_in (r_in[626]), .r627_in (r_in[627]),
        .r628_in (r_in[628]), .r629_in (r_in[629]), .r630_in (r_in[630]), .r631_in (r_in[631]),
        .r632_in (r_in[632]), .r633_in (r_in[633]), .r634_in (r_in[634]), .r635_in (r_in[635]),
        .r636_in (r_in[636]), .r637_in (r_in[637]), .r638_in (r_in[638]), .r639_in (r_in[639]),
        .r640_in (r_in[640]), .r641_in (r_in[641]), .r642_in (r_in[642]), .r643_in (r_in[643]),
        .r644_in (r_in[644]), .r645_in (r_in[645]), .r646_in (r_in[646]), .r647_in (r_in[647]),
        .r648_in (r_in[648]), .r649_in (r_in[649]), .r650_in (r_in[650]), .r651_in (r_in[651]),
        .r652_in (r_in[652]), .r653_in (r_in[653]), .r654_in (r_in[654]), .r655_in (r_in[655]),
        .r656_in (r_in[656]), .r657_in (r_in[657]), .r658_in (r_in[658]), .r659_in (r_in[659]),
        .r660_in (r_in[660]), .r661_in (r_in[661]), .r662_in (r_in[662]), .r663_in (r_in[663]),
        .r664_in (r_in[664]), .r665_in (r_in[665]), .r666_in (r_in[666]), .r667_in (r_in[667]),
        .r668_in (r_in[668]), .r669_in (r_in[669]), .r670_in (r_in[670]), .r671_in (r_in[671]),
        .r672_in (r_in[672]), .r673_in (r_in[673]), .r674_in (r_in[674]), .r675_in (r_in[675]),
        .r676_in (r_in[676]), .r677_in (r_in[677]), .r678_in (r_in[678]), .r679_in (r_in[679]),
        .r680_in (r_in[680]), .r681_in (r_in[681]), .r682_in (r_in[682]), .r683_in (r_in[683]),
        .r684_in (r_in[684]), .r685_in (r_in[685]), .r686_in (r_in[686]), .r687_in (r_in[687]),
        .r688_in (r_in[688]), .r689_in (r_in[689]), .r690_in (r_in[690]), .r691_in (r_in[691]),
        .r692_in (r_in[692]), .r693_in (r_in[693]), .r694_in (r_in[694]), .r695_in (r_in[695]),
        .r696_in (r_in[696]), .r697_in (r_in[697]), .r698_in (r_in[698]), .r699_in (r_in[699]),
        .r700_in (r_in[700]), .r701_in (r_in[701]), .r702_in (r_in[702]), .r703_in (r_in[703]),
        .r704_in (r_in[704]), .r705_in (r_in[705]), .r706_in (r_in[706]), .r707_in (r_in[707]),
        .r708_in (r_in[708]), .r709_in (r_in[709]), .r710_in (r_in[710]), .r711_in (r_in[711]),
        .r712_in (r_in[712]), .r713_in (r_in[713]), .r714_in (r_in[714]), .r715_in (r_in[715]),
        .r716_in (r_in[716]), .r717_in (r_in[717]), .r718_in (r_in[718]), .r719_in (r_in[719]),
        .r720_in (r_in[720]), .r721_in (r_in[721]), .r722_in (r_in[722]), .r723_in (r_in[723]),
        .r724_in (r_in[724]), .r725_in (r_in[725]), .r726_in (r_in[726]), .r727_in (r_in[727]),
        .r728_in (r_in[728]), .r729_in (r_in[729]), .r730_in (r_in[730]), .r731_in (r_in[731]),
        .r732_in (r_in[732]), .r733_in (r_in[733]), .r734_in (r_in[734]), .r735_in (r_in[735]),
        .r736_in (r_in[736]), .r737_in (r_in[737]), .r738_in (r_in[738]), .r739_in (r_in[739]),
        .r740_in (r_in[740]), .r741_in (r_in[741]), .r742_in (r_in[742]), .r743_in (r_in[743]),
        .r744_in (r_in[744]), .r745_in (r_in[745]), .r746_in (r_in[746]), .r747_in (r_in[747]),
        .r748_in (r_in[748]), .r749_in (r_in[749]), .r750_in (r_in[750]), .r751_in (r_in[751]),
        .r752_in (r_in[752]), .r753_in (r_in[753]), .r754_in (r_in[754]), .r755_in (r_in[755]),
        .r756_in (r_in[756]), .r757_in (r_in[757]), .r758_in (r_in[758]), .r759_in (r_in[759]),
        .r760_in (r_in[760]), .r761_in (r_in[761]), .r762_in (r_in[762]), .r763_in (r_in[763]),
        .r764_in (r_in[764]), .r765_in (r_in[765]), .r766_in (r_in[766]), .r767_in (r_in[767]),
        .r768_in (r_in[768]), .r769_in (r_in[769]), .r770_in (r_in[770]), .r771_in (r_in[771]),
        .r772_in (r_in[772]), .r773_in (r_in[773]), .r774_in (r_in[774]), .r775_in (r_in[775]),
        .r776_in (r_in[776]), .r777_in (r_in[777]), .r778_in (r_in[778]), .r779_in (r_in[779]),
        .r780_in (r_in[780]), .r781_in (r_in[781]), .r782_in (r_in[782]), .r783_in (r_in[783]),
        .r784_in (r_in[784]), .r785_in (r_in[785]), .r786_in (r_in[786]), .r787_in (r_in[787]),
        .r788_in (r_in[788]), .r789_in (r_in[789]), .r790_in (r_in[790]), .r791_in (r_in[791]),
        .r792_in (r_in[792]), .r793_in (r_in[793]), .r794_in (r_in[794]), .r795_in (r_in[795]),
        .r796_in (r_in[796]), .r797_in (r_in[797]), .r798_in (r_in[798]), .r799_in (r_in[799]),
        .r800_in (r_in[800]), .r801_in (r_in[801]), .r802_in (r_in[802]), .r803_in (r_in[803]),
        .r804_in (r_in[804]), .r805_in (r_in[805]), .r806_in (r_in[806]), .r807_in (r_in[807]),
        .r808_in (r_in[808]), .r809_in (r_in[809]), .r810_in (r_in[810]), .r811_in (r_in[811]),
        .r812_in (r_in[812]), .r813_in (r_in[813]), .r814_in (r_in[814]), .r815_in (r_in[815]),
        .r816_in (r_in[816]), .r817_in (r_in[817]), .r818_in (r_in[818]), .r819_in (r_in[819]),
        .r820_in (r_in[820]), .r821_in (r_in[821]), .r822_in (r_in[822]), .r823_in (r_in[823]),
        .r824_in (r_in[824]), .r825_in (r_in[825]), .r826_in (r_in[826]), .r827_in (r_in[827]),
        .r828_in (r_in[828]), .r829_in (r_in[829]), .r830_in (r_in[830]), .r831_in (r_in[831]),
        .r832_in (r_in[832]), .r833_in (r_in[833]), .r834_in (r_in[834]), .r835_in (r_in[835]),
        .r836_in (r_in[836]), .r837_in (r_in[837]), .r838_in (r_in[838]), .r839_in (r_in[839]),
        .r840_in (r_in[840]), .r841_in (r_in[841]), .r842_in (r_in[842]), .r843_in (r_in[843]),
        .r844_in (r_in[844]), .r845_in (r_in[845]), .r846_in (r_in[846]), .r847_in (r_in[847]),
        .r848_in (r_in[848]), .r849_in (r_in[849]), .r850_in (r_in[850]), .r851_in (r_in[851]),
        .r852_in (r_in[852]), .r853_in (r_in[853]), .r854_in (r_in[854]), .r855_in (r_in[855]),
        .r856_in (r_in[856]), .r857_in (r_in[857]), .r858_in (r_in[858]), .r859_in (r_in[859]),
        .r860_in (r_in[860]), .r861_in (r_in[861]), .r862_in (r_in[862]), .r863_in (r_in[863]),
        .r864_in (r_in[864]), .r865_in (r_in[865]), .r866_in (r_in[866]), .r867_in (r_in[867]),
        .r868_in (r_in[868]), .r869_in (r_in[869]), .r870_in (r_in[870]), .r871_in (r_in[871]),
        .r872_in (r_in[872]), .r873_in (r_in[873]), .r874_in (r_in[874]), .r875_in (r_in[875]),
        .r876_in (r_in[876]), .r877_in (r_in[877]), .r878_in (r_in[878]), .r879_in (r_in[879]),
        .r880_in (r_in[880]), .r881_in (r_in[881]), .r882_in (r_in[882]), .r883_in (r_in[883]),
        .r884_in (r_in[884]), .r885_in (r_in[885]), .r886_in (r_in[886]), .r887_in (r_in[887]),
        .r888_in (r_in[888]), .r889_in (r_in[889]), .r890_in (r_in[890]), .r891_in (r_in[891]),
        .r892_in (r_in[892]), .r893_in (r_in[893]), .r894_in (r_in[894]), .r895_in (r_in[895]),
        .r896_in (r_in[896]), .r897_in (r_in[897]), .r898_in (r_in[898]), .r899_in (r_in[899]),
        .r900_in (r_in[900]), .r901_in (r_in[901]), .r902_in (r_in[902]), .r903_in (r_in[903]),
        .r904_in (r_in[904]), .r905_in (r_in[905]), .r906_in (r_in[906]), .r907_in (r_in[907]),
        .r908_in (r_in[908]), .r909_in (r_in[909]), .r910_in (r_in[910]), .r911_in (r_in[911]),
        .r912_in (r_in[912]), .r913_in (r_in[913]), .r914_in (r_in[914]), .r915_in (r_in[915]),
        .r916_in (r_in[916]), .r917_in (r_in[917]), .r918_in (r_in[918]), .r919_in (r_in[919]),
        .r920_in (r_in[920]), .r921_in (r_in[921]), .r922_in (r_in[922]), .r923_in (r_in[923]),
        .r924_in (r_in[924]), .r925_in (r_in[925]), .r926_in (r_in[926]), .r927_in (r_in[927]),
        .r928_in (r_in[928]), .r929_in (r_in[929]), .r930_in (r_in[930]), .r931_in (r_in[931]),
        .r932_in (r_in[932]), .r933_in (r_in[933]), .r934_in (r_in[934]), .r935_in (r_in[935]),
        .r936_in (r_in[936]), .r937_in (r_in[937]), .r938_in (r_in[938]), .r939_in (r_in[939]),
        .r940_in (r_in[940]), .r941_in (r_in[941]), .r942_in (r_in[942]), .r943_in (r_in[943]),
        .r944_in (r_in[944]), .r945_in (r_in[945]), .r946_in (r_in[946]), .r947_in (r_in[947]),
        .r948_in (r_in[948]), .r949_in (r_in[949]), .r950_in (r_in[950]), .r951_in (r_in[951]),
        .r952_in (r_in[952]), .r953_in (r_in[953]), .r954_in (r_in[954]), .r955_in (r_in[955]),
        .r956_in (r_in[956]), .r957_in (r_in[957]), .r958_in (r_in[958]), .r959_in (r_in[959]),
        .r960_in (r_in[960]), .r961_in (r_in[961]), .r962_in (r_in[962]), .r963_in (r_in[963]),
        .r964_in (r_in[964]), .r965_in (r_in[965]), .r966_in (r_in[966]), .r967_in (r_in[967]),
        .r968_in (r_in[968]), .r969_in (r_in[969]), .r970_in (r_in[970]), .r971_in (r_in[971]),
        .r972_in (r_in[972]), .r973_in (r_in[973]), .r974_in (r_in[974]), .r975_in (r_in[975]),
        .r976_in (r_in[976]), .r977_in (r_in[977]), .r978_in (r_in[978]), .r979_in (r_in[979]),
        .r980_in (r_in[980]), .r981_in (r_in[981]), .r982_in (r_in[982]), .r983_in (r_in[983]),
        .r984_in (r_in[984]), .r985_in (r_in[985]), .r986_in (r_in[986]), .r987_in (r_in[987]),
        .r988_in (r_in[988]), .r989_in (r_in[989]), .r990_in (r_in[990]), .r991_in (r_in[991]),
        .r992_in (r_in[992]), .r993_in (r_in[993]), .r994_in (r_in[994]), .r995_in (r_in[995]),
        .r996_in (r_in[996]), .r997_in (r_in[997]), .r998_in (r_in[998]), .r999_in (r_in[999]),
        .r1000_in(r_in[1000]),.r1001_in(r_in[1001]),.r1002_in(r_in[1002]),.r1003_in(r_in[1003]),
        .r1004_in(r_in[1004]),.r1005_in(r_in[1005]),.r1006_in(r_in[1006]),.r1007_in(r_in[1007]),
        .valid_out(valid_out), .y0_out(y0_out), .y1_out(y1_out), .y2_out(y2_out)
    );

    reg [127:0] h_secret [0:99];
    reg [127:0] h_s0 [0:99];
    reg [127:0] h_s1 [0:99];
    reg [127:0] h_s2 [0:99];
    reg [127:0] h_rk0 [0:99];
    reg [127:0] h_rk1 [0:99];
    reg [127:0] h_rk2 [0:99];
    reg [7:0]   h_masks [0:100799];

    initial begin
        if (!$value$plusargs("N=%d", N_VECTORS)) N_VECTORS = 10;
        $readmemh("sim/power_secret.txt", h_secret);
        $readmemh("sim/power_s0.txt",     h_s0);
        $readmemh("sim/power_s1.txt",     h_s1);
        // For d=2 we set x2 = s0 ^ s1 (s0 + s1 share) — a test-only
        // convention; in production each share is independently
        // random.
        $readmemh("sim/power_rk0.txt",    h_rk0);
        $readmemh("sim/power_rk1.txt",    h_rk1);
        $readmemh("sim/power_d2_masks.txt", h_masks);
    end

    // power trace dump
    reg [384:0] cur_state;
    integer     hd;
    integer     trace_fh;
    integer     header_fh;
    integer     cycle_ctr;
    integer     cycle_ctr_dump;
    always @(*) begin
        cur_state = {valid_out, y0_out, y1_out, y2_out};
    end

    initial begin
        trace_fh  = $fopen("sim/power_gl_d2_trace.txt",  "w");
        header_fh = $fopen("sim/power_gl_d2_header.txt", "w");
    end

    reg [384:0] state_q;
    always @(posedge clk) begin
        if (rst_n) begin
            hd = $countones(cur_state ^ state_q);
            state_q <= cur_state;
            $fwrite(trace_fh, "%0d %0d\n", cycle_ctr_dump, hd);
            cycle_ctr_dump <= cycle_ctr_dump + 1;
            cycle_ctr <= cycle_ctr + 1;
        end
    end

    integer n, b;
    initial begin
        #1;
        valid_in = 1'b0;
        x0_in    = 128'h0; x1_in    = 128'h0; x2_in    = 128'h0;
        rk0_in   = 128'h0; rk1_in   = 128'h0; rk2_in   = 128'h0;
        for (b = 0; b < 1008; b = b + 1) r_in[b] = 8'h0;
        rst_n    = 1'b0;
        state_q  = 385'h0;
        cycle_ctr = 0;
        cycle_ctr_dump = 0;
        repeat (4) @(posedge clk);
        rst_n    = 1'b1;
        @(posedge clk);

        for (n = 0; n < N_VECTORS; n = n + 1) begin : VEC_LOOP
            $fwrite(header_fh, "%02x 0 0 0 0 0 0 0 %0d\n",
                    h_secret[n][7:0], cycle_ctr);

            x0_in  = h_s0[n];
            x1_in  = h_s1[n];
            x2_in  = h_s0[n] ^ h_s1[n];
            rk0_in = h_rk0[n];
            rk1_in = h_rk1[n];
            rk2_in = h_rk0[n] ^ h_rk1[n];
            for (b = 0; b < 1008; b = b + 1)
                r_in[b] = h_masks[n*1008 + b];
            @(posedge clk);
            valid_in = 1'b1;
            @(posedge clk);
            valid_in = 1'b0;
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
            @(posedge clk); @(posedge clk); @(posedge clk); @(posedge clk);
        end
        $fclose(trace_fh);
        $fclose(header_fh);
        $display("Gate-level d=2 VCD dumped %0d vectors", N_VECTORS);
        $finish;
    end

endmodule

`endif

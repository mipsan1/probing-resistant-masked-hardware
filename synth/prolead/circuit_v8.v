module circuit(clk, sboxIn, randomIn, sboxOut);
  input clk;
  input [15:0] sboxIn;
  input [55:0] randomIn;
  output [15:0] sboxOut;

  wire [7:0] x0 = sboxIn[7:0];
  wire [7:0] x1 = sboxIn[15:8];
  wire [7:0] r0 = randomIn[ 0 +: 8];
  wire [7:0] r1 = randomIn[ 8 +: 8];
  wire [7:0] r2 = randomIn[16 +: 8];
  wire [7:0] r3 = randomIn[24 +: 8];
  wire [7:0] r4 = randomIn[32 +: 8];
  wire [7:0] r5 = randomIn[40 +: 8];
  wire [7:0] r6 = randomIn[48 +: 8];
  wire [7:0] y0, y1;
  wire v_out;

aes_affine_byte_mod u_aff_inv1 (
    .a(inv1),
    .y(aff_inv1)
  );
  gf_mul_byte_mod u_m1_p00 (
    .a(x0_s1_d1),
    .b(x0_s2r),
    .y(m1_p00)
  );
  gf_mul_byte_mod u_m1_p01 (
    .a(x0_s1_d1),
    .b(x1_s2r),
    .y(m1_p01)
  );
  gf_mul_byte_mod u_m1_p10 (
    .a(x1_s1_d1),
    .b(x0_s2r),
    .y(m1_p10)
  );
  gf_mul_byte_mod u_m1_p11 (
    .a(x1_s1_d1),
    .b(x1_s2r),
    .y(m1_p11)
  );
  gf_mul_byte_mod u_m2_p00 (
    .a(mul1_0),
    .b(x0_s3_d2),
    .y(m2_p00)
  );
  gf_mul_byte_mod u_m2_p01 (
    .a(mul1_0),
    .b(x1_s3_d2),
    .y(m2_p01)
  );
  gf_mul_byte_mod u_m2_p10 (
    .a(mul1_1),
    .b(x0_s3_d2),
    .y(m2_p10)
  );
  gf_mul_byte_mod u_m2_p11 (
    .a(mul1_1),
    .b(x1_s3_d2),
    .y(m2_p11)
  );
  gf_mul_byte_mod u_m3_p00 (
    .a(mul2_0),
    .b(x0_s4_d3),
    .y(m3_p00)
  );
  gf_mul_byte_mod u_m3_p01 (
    .a(mul2_0),
    .b(x1_s4_d3),
    .y(m3_p01)
  );
  gf_mul_byte_mod u_m3_p10 (
    .a(mul2_1),
    .b(x0_s4_d3),
    .y(m3_p10)
  );
  gf_mul_byte_mod u_m3_p11 (
    .a(mul2_1),
    .b(x1_s4_d3),
    .y(m3_p11)
  );
  gf_mul_byte_mod u_m4_p00 (
    .a(mul3_0),
    .b(x0_s5_d4),
    .y(m4_p00)
  );
  gf_mul_byte_mod u_m4_p01 (
    .a(mul3_0),
    .b(x1_s5_d4),
    .y(m4_p01)
  );
  gf_mul_byte_mod u_m4_p10 (
    .a(mul3_1),
    .b(x0_s5_d4),
    .y(m4_p10)
  );
  gf_mul_byte_mod u_m4_p11 (
    .a(mul3_1),
    .b(x1_s5_d4),
    .y(m4_p11)
  );
  gf_mul_byte_mod u_m5_p00 (
    .a(mul4_0),
    .b(x0_s6_d5),
    .y(m5_p00)
  );
  gf_mul_byte_mod u_m5_p01 (
    .a(mul4_0),
    .b(x1_s6_d5),
    .y(m5_p01)
  );
  gf_mul_byte_mod u_m5_p10 (
    .a(mul4_1),
    .b(x0_s6_d5),
    .y(m5_p10)
  );
  gf_mul_byte_mod u_m5_p11 (
    .a(mul4_1),
    .b(x1_s6_d5),
    .y(m5_p11)
  );
  gf_mul_byte_mod u_m6_p00 (
    .a(mul5_0),
    .b(x0_s7_d6),
    .y(m6_p00)
  );
  gf_mul_byte_mod u_m6_p01 (
    .a(mul5_0),
    .b(x1_s7_d6),
    .y(m6_p01)
  );
  gf_mul_byte_mod u_m6_p10 (
    .a(mul5_1),
    .b(x0_s7_d6),
    .y(m6_p10)
  );
  gf_mul_byte_mod u_m6_p11 (
    .a(mul5_1),
    .b(x1_s7_d6),
    .y(m6_p11)
  );
  gf_sq_byte_mod u_sq_x0_s0 (
    .a(x0_s0),
    .y(sq_x0_s0)
  );
  gf_sq_byte_mod u_sq_x0_s1 (
    .a(x0_s1),
    .y(sq_x0_s1)
  );
  gf_sq_byte_mod u_sq_x0_s2 (
    .a(x0_s2),
    .y(sq_x0_s2)
  );
  gf_sq_byte_mod u_sq_x0_s3 (
    .a(x0_s3),
    .y(sq_x0_s3)
  );
  gf_sq_byte_mod u_sq_x0_s4 (
    .a(x0_s4),
    .y(sq_x0_s4)
  );
  gf_sq_byte_mod u_sq_x0_s5 (
    .a(x0_s5),
    .y(sq_x0_s5)
  );
  gf_sq_byte_mod u_sq_x0_s6 (
    .a(x0_s6),
    .y(sq_x0_s6)
  );
  gf_sq_byte_mod u_sq_x1_s0 (
    .a(x1_s0),
    .y(sq_x1_s0)
  );
  gf_sq_byte_mod u_sq_x1_s1 (
    .a(x1_s1),
    .y(sq_x1_s1)
  );
  gf_sq_byte_mod u_sq_x1_s2 (
    .a(x1_s2),
    .y(sq_x1_s2)
  );
  gf_sq_byte_mod u_sq_x1_s3 (
    .a(x1_s3),
    .y(sq_x1_s3)
  );
  gf_sq_byte_mod u_sq_x1_s4 (
    .a(x1_s4),
    .y(sq_x1_s4)
  );
  gf_sq_byte_mod u_sq_x1_s5 (
    .a(x1_s5),
    .y(sq_x1_s5)
  );
  gf_sq_byte_mod u_sq_x1_s6 (
    .a(x1_s6),
    .y(sq_x1_s6)
  );
  assign v0 = valid_pipe[0];
  assign v1 = valid_pipe[1];
  assign v10 = valid_pipe[10];
  assign v11 = valid_pipe[11];
  assign v12 = valid_pipe[12];
  assign v13 = valid_pipe[13];
  assign v14 = valid_pipe[14];
  assign v15 = valid_pipe[15];
  assign v16 = valid_pipe[16];
  assign v2 = valid_pipe[2];
  assign v3 = valid_pipe[3];
  assign v4 = valid_pipe[4];
  assign v5 = valid_pipe[5];
  assign v6 = valid_pipe[6];
  assign v7 = valid_pipe[7];
  assign v8 = valid_pipe[8];
  assign v9 = valid_pipe[9];

  assign sboxOut[7:0]  = y0;
  assign sboxOut[15:8] = y1;
endmodule



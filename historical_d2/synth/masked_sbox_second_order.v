// =====================================================================
// masked_sbox_second_order.v
// Second-order (d = 2) masked AES S-box with three shares per byte.
//
// Direct 3-share extension of masked_sbox_first_order.v (Algorithm 1,
// DOM-style with register barrier).  Same Canright/Itoh-Tsujii schedule,
// same two-stage multiplier pipeline, same hard-cell discipline; only the
// share count (2 -> 3) and the cross-term randomness (1 -> 3 bytes per
// multiplication) change.
//
// Masked multiplier (per multiplication, i,j in {0,1,2}):
//   q_ii = Reg(a_i * b_i)                          (diagonal, unmasked)
//   q_01 = Reg(a_0*b_1 ^ r01)   q_10 = Reg(a_1*b_0 ^ r01)
//   q_02 = Reg(a_0*b_2 ^ r02)   q_20 = Reg(a_2*b_0 ^ r02)
//   q_12 = Reg(a_1*b_2 ^ r12)   q_21 = Reg(a_2*b_1 ^ r12)
//   c_i  = q_i0 ^ q_i1 ^ q_i2   (compression AFTER the barrier, 3-way XOR)
//
// OPERAND-INDEPENDENCE REFRESH (security-critical, same argument as d=1):
// the x^4 operand of mul1 is register-refreshed with one fresh byte r18,
// XORed into TWO of the three shares (x0_s2 ^ r18, x1_s2 ^ r18, x2_s2),
// so the refreshed sharing still XORs to x^4 and is statistically
// independent of the x^2 sharing.  Downstream multiplications need no
// extra refresh: their first operand is the previous multiplier output,
// already re-masked by that stage's fresh cross-term bytes.
//
// HARD-CELL DISCIPLINE: every GF(2^8) square / multiply / affine cloud is
// instantiated as its own keep_hierarchy module (gf_sq_byte_mod_d2 /
// gf_mul_byte_mod_d2 / aes_affine_byte_mod_d2, defined at the bottom of
// this file with a _d2 suffix so this file can be compiled alongside
// masked_sbox_first_order.v without module-name collisions).
//
// Pipeline structure (17-cycle latency, one invocation per window):
//   c0:      input register (x_s0)
//   c1..c7:  squaring chain (x^2 .. x^128), share-wise
//   c3:      mul1 operand stage: x_s1_d1 <= x_s1 ;
//            x_s2r <= {x_s2 share0 ^ r18, x_s2 share1 ^ r18, x_s2 share2}
//   Multiplications take TWO register stages (q-barrier, then compress):
//     mul1 q@c4  c@c5   (x^2 * x^4    -> x^6)
//     mul2 q@c6  c@c7   (x^6 * x^8    -> x^14)
//     mul3 q@c8  c@c9   (x^14 * x^16  -> x^30)
//     mul4 q@c10 c@c11  (x^30 * x^32  -> x^62)
//     mul5 q@c12 c@c13  (x^62 * x^64  -> x^126)
//     inv  q@c14 c@c15  (x^126 * x^128 -> x^254 = x^-1)
//   c16:     AES affine (share-wise linear + 0x63 on share 0)
//   c17:     output register (valid_out)
//
// Fresh randomness: 3 bytes per multiplication x 6 multiplications
// (r0..r17) plus 1 byte for the mul1 operand refresh (r18)
// = 19 random bytes (152 bits) per S-box invocation.
// =====================================================================

`ifndef MASKED_SBOX_SECOND_ORDER_V
`define MASKED_SBOX_SECOND_ORDER_V

`include "masked_sbox_pkg.v"

module masked_sbox_second_order (
    input              clk,
    input              rst_n,
    input              valid_in,
    input      [7:0]   x0_in,   // share 0 of input
    input      [7:0]   x1_in,   // share 1 of input
    input      [7:0]   x2_in,   // share 2 of input (x0^x1^x2 is the secret)
    // Fresh randomness: 3 bytes per multiplication (r01,r02,r12 of the
    // 3-share DOM) plus 1 byte for the mul1 operand refresh.
    input      [7:0]   r0_in,   // mul1 r_01
    input      [7:0]   r1_in,   // mul1 r_02
    input      [7:0]   r2_in,   // mul1 r_12
    input      [7:0]   r3_in,   // mul2 r_01
    input      [7:0]   r4_in,   // mul2 r_02
    input      [7:0]   r5_in,   // mul2 r_12
    input      [7:0]   r6_in,   // mul3 r_01
    input      [7:0]   r7_in,   // mul3 r_02
    input      [7:0]   r8_in,   // mul3 r_12
    input      [7:0]   r9_in,   // mul4 r_01
    input      [7:0]   r10_in,  // mul4 r_02
    input      [7:0]   r11_in,  // mul4 r_12
    input      [7:0]   r12_in,  // mul5 r_01
    input      [7:0]   r13_in,  // mul5 r_02
    input      [7:0]   r14_in,  // mul5 r_12
    input      [7:0]   r15_in,  // inv  r_01
    input      [7:0]   r16_in,  // inv  r_02
    input      [7:0]   r17_in,  // inv  r_12
    input      [7:0]   r18_in,  // mul1 operand refresh (x^4 path)
    output reg         valid_out,
    output reg [7:0]   y0_out,  // share 0 of AES S-box output
    output reg [7:0]   y1_out,  // share 1 of AES S-box output
    output reg [7:0]   y2_out   // share 2 of AES S-box output
);

  // ------------------------------------------------------------------
  // STAGE 0: input registers
  // ------------------------------------------------------------------
  reg [7:0] x0_s0, x1_s0, x2_s0;
  reg [7:0] x0_s1, x1_s1, x2_s1;  // x^2 register
  reg [7:0] x0_s2, x1_s2, x2_s2;  // x^4 register
  reg [7:0] x0_s3, x1_s3, x2_s3;  // x^8 register
  reg [7:0] x0_s4, x1_s4, x2_s4;  // x^16 register
  reg [7:0] x0_s5, x1_s5, x2_s5;  // x^32 register
  reg [7:0] x0_s6, x1_s6, x2_s6;  // x^64 register
  reg [7:0] x0_s7, x1_s7, x2_s7;  // x^128 register

  // ------------------------------------------------------------------
  // Per-stage valid shift register (17 bits), identical to d=1.
  // ------------------------------------------------------------------
  reg [16:0] valid_pipe;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 17'b0;
    end else begin
      valid_pipe <= {valid_pipe[15:0], valid_in};
    end
  end

  wire v0  = valid_pipe[0];
  wire v1  = valid_pipe[1];
  wire v2  = valid_pipe[2];
  wire v3  = valid_pipe[3];
  wire v4  = valid_pipe[4];
  wire v5  = valid_pipe[5];
  wire v6  = valid_pipe[6];
  wire v7  = valid_pipe[7];
  wire v8  = valid_pipe[8];
  wire v9  = valid_pipe[9];
  wire v10 = valid_pipe[10];
  wire v11 = valid_pipe[11];
  wire v12 = valid_pipe[12];
  wire v13 = valid_pipe[13];
  wire v14 = valid_pipe[14];
  wire v15 = valid_pipe[15];
  wire v16 = valid_pipe[16];

  // ------------------------------------------------------------------
  // STAGE 1: squaring chain, one hard cell per share per stage.
  // ------------------------------------------------------------------
  wire [7:0] sq_x0_s0, sq_x1_s0, sq_x2_s0;
  gf_sq_byte_mod_d2 u_sq_x0_s0 (.a(x0_s0), .y(sq_x0_s0));
  gf_sq_byte_mod_d2 u_sq_x1_s0 (.a(x1_s0), .y(sq_x1_s0));
  gf_sq_byte_mod_d2 u_sq_x2_s0 (.a(x2_s0), .y(sq_x2_s0));

  wire [7:0] sq_x0_s1, sq_x1_s1, sq_x2_s1;
  gf_sq_byte_mod_d2 u_sq_x0_s1 (.a(x0_s1), .y(sq_x0_s1));
  gf_sq_byte_mod_d2 u_sq_x1_s1 (.a(x1_s1), .y(sq_x1_s1));
  gf_sq_byte_mod_d2 u_sq_x2_s1 (.a(x2_s1), .y(sq_x2_s1));

  wire [7:0] sq_x0_s2, sq_x1_s2, sq_x2_s2;
  gf_sq_byte_mod_d2 u_sq_x0_s2 (.a(x0_s2), .y(sq_x0_s2));
  gf_sq_byte_mod_d2 u_sq_x1_s2 (.a(x1_s2), .y(sq_x1_s2));
  gf_sq_byte_mod_d2 u_sq_x2_s2 (.a(x2_s2), .y(sq_x2_s2));

  wire [7:0] sq_x0_s3, sq_x1_s3, sq_x2_s3;
  gf_sq_byte_mod_d2 u_sq_x0_s3 (.a(x0_s3), .y(sq_x0_s3));
  gf_sq_byte_mod_d2 u_sq_x1_s3 (.a(x1_s3), .y(sq_x1_s3));
  gf_sq_byte_mod_d2 u_sq_x2_s3 (.a(x2_s3), .y(sq_x2_s3));

  wire [7:0] sq_x0_s4, sq_x1_s4, sq_x2_s4;
  gf_sq_byte_mod_d2 u_sq_x0_s4 (.a(x0_s4), .y(sq_x0_s4));
  gf_sq_byte_mod_d2 u_sq_x1_s4 (.a(x1_s4), .y(sq_x1_s4));
  gf_sq_byte_mod_d2 u_sq_x2_s4 (.a(x2_s4), .y(sq_x2_s4));

  wire [7:0] sq_x0_s5, sq_x1_s5, sq_x2_s5;
  gf_sq_byte_mod_d2 u_sq_x0_s5 (.a(x0_s5), .y(sq_x0_s5));
  gf_sq_byte_mod_d2 u_sq_x1_s5 (.a(x1_s5), .y(sq_x1_s5));
  gf_sq_byte_mod_d2 u_sq_x2_s5 (.a(x2_s5), .y(sq_x2_s5));

  wire [7:0] sq_x0_s6, sq_x1_s6, sq_x2_s6;
  gf_sq_byte_mod_d2 u_sq_x0_s6 (.a(x0_s6), .y(sq_x0_s6));
  gf_sq_byte_mod_d2 u_sq_x1_s6 (.a(x1_s6), .y(sq_x1_s6));
  gf_sq_byte_mod_d2 u_sq_x2_s6 (.a(x2_s6), .y(sq_x2_s6));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s0 <= 8'h00; x1_s0 <= 8'h00; x2_s0 <= 8'h00;
    end else if (valid_in) begin
      x0_s0 <= x0_in;
      x1_s0 <= x1_in;
      x2_s0 <= x2_in;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s1 <= 8'h00; x1_s1 <= 8'h00; x2_s1 <= 8'h00;
    end else if (v0) begin
      x0_s1 <= sq_x0_s0;
      x1_s1 <= sq_x1_s0;
      x2_s1 <= sq_x2_s0;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s2 <= 8'h00; x1_s2 <= 8'h00; x2_s2 <= 8'h00;
    end else if (v1) begin
      x0_s2 <= sq_x0_s1;
      x1_s2 <= sq_x1_s1;
      x2_s2 <= sq_x2_s1;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s3 <= 8'h00; x1_s3 <= 8'h00; x2_s3 <= 8'h00;
    end else if (v2) begin
      x0_s3 <= sq_x0_s2;
      x1_s3 <= sq_x1_s2;
      x2_s3 <= sq_x2_s2;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s4 <= 8'h00; x1_s4 <= 8'h00; x2_s4 <= 8'h00;
    end else if (v3) begin
      x0_s4 <= sq_x0_s3;
      x1_s4 <= sq_x1_s3;
      x2_s4 <= sq_x2_s3;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s5 <= 8'h00; x1_s5 <= 8'h00; x2_s5 <= 8'h00;
    end else if (v4) begin
      x0_s5 <= sq_x0_s4;
      x1_s5 <= sq_x1_s4;
      x2_s5 <= sq_x2_s4;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s6 <= 8'h00; x1_s6 <= 8'h00; x2_s6 <= 8'h00;
    end else if (v5) begin
      x0_s6 <= sq_x0_s5;
      x1_s6 <= sq_x1_s5;
      x2_s6 <= sq_x2_s5;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s7 <= 8'h00; x1_s7 <= 8'h00; x2_s7 <= 8'h00;
    end else if (v6) begin
      x0_s7 <= sq_x0_s6;
      x1_s7 <= sq_x1_s6;
      x2_s7 <= sq_x2_s6;
    end
  end

  // After seven squarings, (x0_s7, x1_s7, x2_s7) is a sharing of x^128.

  // ------------------------------------------------------------------
  // mul1 operand stage (c3): delay the x^2 operand by one cycle and
  // REGISTER-REFRESH the x^4 operand with r18 (XORed into shares 0 and 1
  // only; the three refreshed shares still XOR to x^4).
  // ------------------------------------------------------------------
  reg [7:0] x0_s1_d1, x1_s1_d1, x2_s1_d1;   // x^2 delayed to mul1 timing
  reg [7:0] x0_s2r,   x1_s2r,   x2_s2r;     // refreshed x^4 sharing

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s1_d1 <= 8'h00; x1_s1_d1 <= 8'h00; x2_s1_d1 <= 8'h00;
    end else if (v2) begin
      x0_s1_d1 <= x0_s1;
      x1_s1_d1 <= x1_s1;
      x2_s1_d1 <= x2_s1;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s2r <= 8'h00; x1_s2r <= 8'h00; x2_s2r <= 8'h00;
    end else if (v2) begin
      x0_s2r <= x0_s2 ^ r18_in;
      x1_s2r <= x1_s2 ^ r18_in;
      x2_s2r <= x2_s2;
    end
  end

  // ------------------------------------------------------------------
  // Power-tap delay lines (3 shares each), same depths as d=1.
  // ------------------------------------------------------------------
  reg [7:0] x0_s3_d1, x1_s3_d1, x2_s3_d1, x0_s3_d2, x1_s3_d2, x2_s3_d2;
  reg [7:0] x0_s4_d1, x1_s4_d1, x2_s4_d1, x0_s4_d2, x1_s4_d2, x2_s4_d2,
            x0_s4_d3, x1_s4_d3, x2_s4_d3;
  reg [7:0] x0_s5_d1, x1_s5_d1, x2_s5_d1, x0_s5_d2, x1_s5_d2, x2_s5_d2,
            x0_s5_d3, x1_s5_d3, x2_s5_d3, x0_s5_d4, x1_s5_d4, x2_s5_d4;
  reg [7:0] x0_s6_d1, x1_s6_d1, x2_s6_d1, x0_s6_d2, x1_s6_d2, x2_s6_d2,
            x0_s6_d3, x1_s6_d3, x2_s6_d3, x0_s6_d4, x1_s6_d4, x2_s6_d4,
            x0_s6_d5, x1_s6_d5, x2_s6_d5;
  reg [7:0] x0_s7_d1, x1_s7_d1, x2_s7_d1, x0_s7_d2, x1_s7_d2, x2_s7_d2,
            x0_s7_d3, x1_s7_d3, x2_s7_d3, x0_s7_d4, x1_s7_d4, x2_s7_d4,
            x0_s7_d5, x1_s7_d5, x2_s7_d5, x0_s7_d6, x1_s7_d6, x2_s7_d6;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s3_d1 <= 8'h00; x1_s3_d1 <= 8'h00; x2_s3_d1 <= 8'h00;
      x0_s3_d2 <= 8'h00; x1_s3_d2 <= 8'h00; x2_s3_d2 <= 8'h00;
    end else begin
      if (v3) begin
        x0_s3_d1 <= x0_s3; x1_s3_d1 <= x1_s3; x2_s3_d1 <= x2_s3;
      end
      if (v4) begin
        x0_s3_d2 <= x0_s3_d1; x1_s3_d2 <= x1_s3_d1; x2_s3_d2 <= x2_s3_d1;
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s4_d1 <= 8'h00; x1_s4_d1 <= 8'h00; x2_s4_d1 <= 8'h00;
      x0_s4_d2 <= 8'h00; x1_s4_d2 <= 8'h00; x2_s4_d2 <= 8'h00;
      x0_s4_d3 <= 8'h00; x1_s4_d3 <= 8'h00; x2_s4_d3 <= 8'h00;
    end else begin
      if (v4) begin
        x0_s4_d1 <= x0_s4; x1_s4_d1 <= x1_s4; x2_s4_d1 <= x2_s4;
      end
      if (v5) begin
        x0_s4_d2 <= x0_s4_d1; x1_s4_d2 <= x1_s4_d1; x2_s4_d2 <= x2_s4_d1;
      end
      if (v6) begin
        x0_s4_d3 <= x0_s4_d2; x1_s4_d3 <= x1_s4_d2; x2_s4_d3 <= x2_s4_d2;
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s5_d1 <= 8'h00; x1_s5_d1 <= 8'h00; x2_s5_d1 <= 8'h00;
      x0_s5_d2 <= 8'h00; x1_s5_d2 <= 8'h00; x2_s5_d2 <= 8'h00;
      x0_s5_d3 <= 8'h00; x1_s5_d3 <= 8'h00; x2_s5_d3 <= 8'h00;
      x0_s5_d4 <= 8'h00; x1_s5_d4 <= 8'h00; x2_s5_d4 <= 8'h00;
    end else begin
      if (v5) begin
        x0_s5_d1 <= x0_s5; x1_s5_d1 <= x1_s5; x2_s5_d1 <= x2_s5;
      end
      if (v6) begin
        x0_s5_d2 <= x0_s5_d1; x1_s5_d2 <= x1_s5_d1; x2_s5_d2 <= x2_s5_d1;
      end
      if (v7) begin
        x0_s5_d3 <= x0_s5_d2; x1_s5_d3 <= x1_s5_d2; x2_s5_d3 <= x2_s5_d2;
      end
      if (v8) begin
        x0_s5_d4 <= x0_s5_d3; x1_s5_d4 <= x1_s5_d3; x2_s5_d4 <= x2_s5_d3;
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s6_d1 <= 8'h00; x1_s6_d1 <= 8'h00; x2_s6_d1 <= 8'h00;
      x0_s6_d2 <= 8'h00; x1_s6_d2 <= 8'h00; x2_s6_d2 <= 8'h00;
      x0_s6_d3 <= 8'h00; x1_s6_d3 <= 8'h00; x2_s6_d3 <= 8'h00;
      x0_s6_d4 <= 8'h00; x1_s6_d4 <= 8'h00; x2_s6_d4 <= 8'h00;
      x0_s6_d5 <= 8'h00; x1_s6_d5 <= 8'h00; x2_s6_d5 <= 8'h00;
    end else begin
      if (v6) begin
        x0_s6_d1 <= x0_s6; x1_s6_d1 <= x1_s6; x2_s6_d1 <= x2_s6;
      end
      if (v7) begin
        x0_s6_d2 <= x0_s6_d1; x1_s6_d2 <= x1_s6_d1; x2_s6_d2 <= x2_s6_d1;
      end
      if (v8) begin
        x0_s6_d3 <= x0_s6_d2; x1_s6_d3 <= x1_s6_d2; x2_s6_d3 <= x2_s6_d2;
      end
      if (v9) begin
        x0_s6_d4 <= x0_s6_d3; x1_s6_d4 <= x1_s6_d3; x2_s6_d4 <= x2_s6_d3;
      end
      if (v10) begin
        x0_s6_d5 <= x0_s6_d4; x1_s6_d5 <= x1_s6_d4; x2_s6_d5 <= x2_s6_d4;
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s7_d1 <= 8'h00; x1_s7_d1 <= 8'h00; x2_s7_d1 <= 8'h00;
      x0_s7_d2 <= 8'h00; x1_s7_d2 <= 8'h00; x2_s7_d2 <= 8'h00;
      x0_s7_d3 <= 8'h00; x1_s7_d3 <= 8'h00; x2_s7_d3 <= 8'h00;
      x0_s7_d4 <= 8'h00; x1_s7_d4 <= 8'h00; x2_s7_d4 <= 8'h00;
      x0_s7_d5 <= 8'h00; x1_s7_d5 <= 8'h00; x2_s7_d5 <= 8'h00;
      x0_s7_d6 <= 8'h00; x1_s7_d6 <= 8'h00; x2_s7_d6 <= 8'h00;
    end else begin
      if (v7) begin
        x0_s7_d1 <= x0_s7; x1_s7_d1 <= x1_s7; x2_s7_d1 <= x2_s7;
      end
      if (v8) begin
        x0_s7_d2 <= x0_s7_d1; x1_s7_d2 <= x1_s7_d1; x2_s7_d2 <= x2_s7_d1;
      end
      if (v9) begin
        x0_s7_d3 <= x0_s7_d2; x1_s7_d3 <= x1_s7_d2; x2_s7_d3 <= x2_s7_d2;
      end
      if (v10) begin
        x0_s7_d4 <= x0_s7_d3; x1_s7_d4 <= x1_s7_d3; x2_s7_d4 <= x2_s7_d3;
      end
      if (v11) begin
        x0_s7_d5 <= x0_s7_d4; x1_s7_d5 <= x1_s7_d4; x2_s7_d5 <= x2_s7_d4;
      end
      if (v12) begin
        x0_s7_d6 <= x0_s7_d5; x1_s7_d6 <= x1_s7_d5; x2_s7_d6 <= x2_s7_d5;
      end
    end
  end

  // ------------------------------------------------------------------
  // STAGE 2..15: six masked multiplications (3-share DOM, Algorithm 1)
  // with the register barrier.  Every domain product is its own hard
  // cell (gf_mul_byte_mod_d2).
  // ------------------------------------------------------------------

  // ---- mul1: (x^2) * (x^4 refreshed) -> x^6
  //      a = x_s1_d1, b = x_s2r, masks r0/r1/r2 ----------------------
  wire [7:0] m1_p00, m1_p01, m1_p02, m1_p10, m1_p11, m1_p12,
             m1_p20, m1_p21, m1_p22;
  gf_mul_byte_mod_d2 u_m1_p00 (.a(x0_s1_d1), .b(x0_s2r), .y(m1_p00));
  gf_mul_byte_mod_d2 u_m1_p01 (.a(x0_s1_d1), .b(x1_s2r), .y(m1_p01));
  gf_mul_byte_mod_d2 u_m1_p02 (.a(x0_s1_d1), .b(x2_s2r), .y(m1_p02));
  gf_mul_byte_mod_d2 u_m1_p10 (.a(x1_s1_d1), .b(x0_s2r), .y(m1_p10));
  gf_mul_byte_mod_d2 u_m1_p11 (.a(x1_s1_d1), .b(x1_s2r), .y(m1_p11));
  gf_mul_byte_mod_d2 u_m1_p12 (.a(x1_s1_d1), .b(x2_s2r), .y(m1_p12));
  gf_mul_byte_mod_d2 u_m1_p20 (.a(x2_s1_d1), .b(x0_s2r), .y(m1_p20));
  gf_mul_byte_mod_d2 u_m1_p21 (.a(x2_s1_d1), .b(x1_s2r), .y(m1_p21));
  gf_mul_byte_mod_d2 u_m1_p22 (.a(x2_s1_d1), .b(x2_s2r), .y(m1_p22));

  reg [7:0] mul1_q00, mul1_q01, mul1_q02, mul1_q10, mul1_q11, mul1_q12,
            mul1_q20, mul1_q21, mul1_q22;
  reg [7:0] mul1_0, mul1_1, mul1_2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul1_q00 <= 8'h00; mul1_q01 <= 8'h00; mul1_q02 <= 8'h00;
      mul1_q10 <= 8'h00; mul1_q11 <= 8'h00; mul1_q12 <= 8'h00;
      mul1_q20 <= 8'h00; mul1_q21 <= 8'h00; mul1_q22 <= 8'h00;
    end else if (v3) begin
      mul1_q00 <= m1_p00;
      mul1_q01 <= m1_p01 ^ r0_in;
      mul1_q02 <= m1_p02 ^ r1_in;
      mul1_q10 <= m1_p10 ^ r0_in;
      mul1_q11 <= m1_p11;
      mul1_q12 <= m1_p12 ^ r2_in;
      mul1_q20 <= m1_p20 ^ r1_in;
      mul1_q21 <= m1_p21 ^ r2_in;
      mul1_q22 <= m1_p22;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul1_0 <= 8'h00; mul1_1 <= 8'h00; mul1_2 <= 8'h00;
    end else if (v4) begin
      mul1_0 <= mul1_q00 ^ mul1_q01 ^ mul1_q02;
      mul1_1 <= mul1_q10 ^ mul1_q11 ^ mul1_q12;
      mul1_2 <= mul1_q20 ^ mul1_q21 ^ mul1_q22;
    end
  end

  // ---- mul2: (x^6) * (x^8) -> x^14 (a = mul1, b = x_s3_d2, r3/r4/r5)
  wire [7:0] m2_p00, m2_p01, m2_p02, m2_p10, m2_p11, m2_p12,
             m2_p20, m2_p21, m2_p22;
  gf_mul_byte_mod_d2 u_m2_p00 (.a(mul1_0), .b(x0_s3_d2), .y(m2_p00));
  gf_mul_byte_mod_d2 u_m2_p01 (.a(mul1_0), .b(x1_s3_d2), .y(m2_p01));
  gf_mul_byte_mod_d2 u_m2_p02 (.a(mul1_0), .b(x2_s3_d2), .y(m2_p02));
  gf_mul_byte_mod_d2 u_m2_p10 (.a(mul1_1), .b(x0_s3_d2), .y(m2_p10));
  gf_mul_byte_mod_d2 u_m2_p11 (.a(mul1_1), .b(x1_s3_d2), .y(m2_p11));
  gf_mul_byte_mod_d2 u_m2_p12 (.a(mul1_1), .b(x2_s3_d2), .y(m2_p12));
  gf_mul_byte_mod_d2 u_m2_p20 (.a(mul1_2), .b(x0_s3_d2), .y(m2_p20));
  gf_mul_byte_mod_d2 u_m2_p21 (.a(mul1_2), .b(x1_s3_d2), .y(m2_p21));
  gf_mul_byte_mod_d2 u_m2_p22 (.a(mul1_2), .b(x2_s3_d2), .y(m2_p22));

  reg [7:0] mul2_q00, mul2_q01, mul2_q02, mul2_q10, mul2_q11, mul2_q12,
            mul2_q20, mul2_q21, mul2_q22;
  reg [7:0] mul2_0, mul2_1, mul2_2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul2_q00 <= 8'h00; mul2_q01 <= 8'h00; mul2_q02 <= 8'h00;
      mul2_q10 <= 8'h00; mul2_q11 <= 8'h00; mul2_q12 <= 8'h00;
      mul2_q20 <= 8'h00; mul2_q21 <= 8'h00; mul2_q22 <= 8'h00;
    end else if (v5) begin
      mul2_q00 <= m2_p00;
      mul2_q01 <= m2_p01 ^ r3_in;
      mul2_q02 <= m2_p02 ^ r4_in;
      mul2_q10 <= m2_p10 ^ r3_in;
      mul2_q11 <= m2_p11;
      mul2_q12 <= m2_p12 ^ r5_in;
      mul2_q20 <= m2_p20 ^ r4_in;
      mul2_q21 <= m2_p21 ^ r5_in;
      mul2_q22 <= m2_p22;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul2_0 <= 8'h00; mul2_1 <= 8'h00; mul2_2 <= 8'h00;
    end else if (v6) begin
      mul2_0 <= mul2_q00 ^ mul2_q01 ^ mul2_q02;
      mul2_1 <= mul2_q10 ^ mul2_q11 ^ mul2_q12;
      mul2_2 <= mul2_q20 ^ mul2_q21 ^ mul2_q22;
    end
  end

  // ---- mul3: (x^14) * (x^16) -> x^30 (a = mul2, b = x_s4_d3, r6/r7/r8)
  wire [7:0] m3_p00, m3_p01, m3_p02, m3_p10, m3_p11, m3_p12,
             m3_p20, m3_p21, m3_p22;
  gf_mul_byte_mod_d2 u_m3_p00 (.a(mul2_0), .b(x0_s4_d3), .y(m3_p00));
  gf_mul_byte_mod_d2 u_m3_p01 (.a(mul2_0), .b(x1_s4_d3), .y(m3_p01));
  gf_mul_byte_mod_d2 u_m3_p02 (.a(mul2_0), .b(x2_s4_d3), .y(m3_p02));
  gf_mul_byte_mod_d2 u_m3_p10 (.a(mul2_1), .b(x0_s4_d3), .y(m3_p10));
  gf_mul_byte_mod_d2 u_m3_p11 (.a(mul2_1), .b(x1_s4_d3), .y(m3_p11));
  gf_mul_byte_mod_d2 u_m3_p12 (.a(mul2_1), .b(x2_s4_d3), .y(m3_p12));
  gf_mul_byte_mod_d2 u_m3_p20 (.a(mul2_2), .b(x0_s4_d3), .y(m3_p20));
  gf_mul_byte_mod_d2 u_m3_p21 (.a(mul2_2), .b(x1_s4_d3), .y(m3_p21));
  gf_mul_byte_mod_d2 u_m3_p22 (.a(mul2_2), .b(x2_s4_d3), .y(m3_p22));

  reg [7:0] mul3_q00, mul3_q01, mul3_q02, mul3_q10, mul3_q11, mul3_q12,
            mul3_q20, mul3_q21, mul3_q22;
  reg [7:0] mul3_0, mul3_1, mul3_2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul3_q00 <= 8'h00; mul3_q01 <= 8'h00; mul3_q02 <= 8'h00;
      mul3_q10 <= 8'h00; mul3_q11 <= 8'h00; mul3_q12 <= 8'h00;
      mul3_q20 <= 8'h00; mul3_q21 <= 8'h00; mul3_q22 <= 8'h00;
    end else if (v7) begin
      mul3_q00 <= m3_p00;
      mul3_q01 <= m3_p01 ^ r6_in;
      mul3_q02 <= m3_p02 ^ r7_in;
      mul3_q10 <= m3_p10 ^ r6_in;
      mul3_q11 <= m3_p11;
      mul3_q12 <= m3_p12 ^ r8_in;
      mul3_q20 <= m3_p20 ^ r7_in;
      mul3_q21 <= m3_p21 ^ r8_in;
      mul3_q22 <= m3_p22;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul3_0 <= 8'h00; mul3_1 <= 8'h00; mul3_2 <= 8'h00;
    end else if (v8) begin
      mul3_0 <= mul3_q00 ^ mul3_q01 ^ mul3_q02;
      mul3_1 <= mul3_q10 ^ mul3_q11 ^ mul3_q12;
      mul3_2 <= mul3_q20 ^ mul3_q21 ^ mul3_q22;
    end
  end

  // ---- mul4: (x^30) * (x^32) -> x^62 (a = mul3, b = x_s5_d4, r9/r10/r11)
  wire [7:0] m4_p00, m4_p01, m4_p02, m4_p10, m4_p11, m4_p12,
             m4_p20, m4_p21, m4_p22;
  gf_mul_byte_mod_d2 u_m4_p00 (.a(mul3_0), .b(x0_s5_d4), .y(m4_p00));
  gf_mul_byte_mod_d2 u_m4_p01 (.a(mul3_0), .b(x1_s5_d4), .y(m4_p01));
  gf_mul_byte_mod_d2 u_m4_p02 (.a(mul3_0), .b(x2_s5_d4), .y(m4_p02));
  gf_mul_byte_mod_d2 u_m4_p10 (.a(mul3_1), .b(x0_s5_d4), .y(m4_p10));
  gf_mul_byte_mod_d2 u_m4_p11 (.a(mul3_1), .b(x1_s5_d4), .y(m4_p11));
  gf_mul_byte_mod_d2 u_m4_p12 (.a(mul3_1), .b(x2_s5_d4), .y(m4_p12));
  gf_mul_byte_mod_d2 u_m4_p20 (.a(mul3_2), .b(x0_s5_d4), .y(m4_p20));
  gf_mul_byte_mod_d2 u_m4_p21 (.a(mul3_2), .b(x1_s5_d4), .y(m4_p21));
  gf_mul_byte_mod_d2 u_m4_p22 (.a(mul3_2), .b(x2_s5_d4), .y(m4_p22));

  reg [7:0] mul4_q00, mul4_q01, mul4_q02, mul4_q10, mul4_q11, mul4_q12,
            mul4_q20, mul4_q21, mul4_q22;
  reg [7:0] mul4_0, mul4_1, mul4_2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul4_q00 <= 8'h00; mul4_q01 <= 8'h00; mul4_q02 <= 8'h00;
      mul4_q10 <= 8'h00; mul4_q11 <= 8'h00; mul4_q12 <= 8'h00;
      mul4_q20 <= 8'h00; mul4_q21 <= 8'h00; mul4_q22 <= 8'h00;
    end else if (v9) begin
      mul4_q00 <= m4_p00;
      mul4_q01 <= m4_p01 ^ r9_in;
      mul4_q02 <= m4_p02 ^ r10_in;
      mul4_q10 <= m4_p10 ^ r9_in;
      mul4_q11 <= m4_p11;
      mul4_q12 <= m4_p12 ^ r11_in;
      mul4_q20 <= m4_p20 ^ r10_in;
      mul4_q21 <= m4_p21 ^ r11_in;
      mul4_q22 <= m4_p22;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul4_0 <= 8'h00; mul4_1 <= 8'h00; mul4_2 <= 8'h00;
    end else if (v10) begin
      mul4_0 <= mul4_q00 ^ mul4_q01 ^ mul4_q02;
      mul4_1 <= mul4_q10 ^ mul4_q11 ^ mul4_q12;
      mul4_2 <= mul4_q20 ^ mul4_q21 ^ mul4_q22;
    end
  end

  // ---- mul5: (x^62) * (x^64) -> x^126 (a = mul4, b = x_s6_d5, r12/r13/r14)
  wire [7:0] m5_p00, m5_p01, m5_p02, m5_p10, m5_p11, m5_p12,
             m5_p20, m5_p21, m5_p22;
  gf_mul_byte_mod_d2 u_m5_p00 (.a(mul4_0), .b(x0_s6_d5), .y(m5_p00));
  gf_mul_byte_mod_d2 u_m5_p01 (.a(mul4_0), .b(x1_s6_d5), .y(m5_p01));
  gf_mul_byte_mod_d2 u_m5_p02 (.a(mul4_0), .b(x2_s6_d5), .y(m5_p02));
  gf_mul_byte_mod_d2 u_m5_p10 (.a(mul4_1), .b(x0_s6_d5), .y(m5_p10));
  gf_mul_byte_mod_d2 u_m5_p11 (.a(mul4_1), .b(x1_s6_d5), .y(m5_p11));
  gf_mul_byte_mod_d2 u_m5_p12 (.a(mul4_1), .b(x2_s6_d5), .y(m5_p12));
  gf_mul_byte_mod_d2 u_m5_p20 (.a(mul4_2), .b(x0_s6_d5), .y(m5_p20));
  gf_mul_byte_mod_d2 u_m5_p21 (.a(mul4_2), .b(x1_s6_d5), .y(m5_p21));
  gf_mul_byte_mod_d2 u_m5_p22 (.a(mul4_2), .b(x2_s6_d5), .y(m5_p22));

  reg [7:0] mul5_q00, mul5_q01, mul5_q02, mul5_q10, mul5_q11, mul5_q12,
            mul5_q20, mul5_q21, mul5_q22;
  reg [7:0] mul5_0, mul5_1, mul5_2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul5_q00 <= 8'h00; mul5_q01 <= 8'h00; mul5_q02 <= 8'h00;
      mul5_q10 <= 8'h00; mul5_q11 <= 8'h00; mul5_q12 <= 8'h00;
      mul5_q20 <= 8'h00; mul5_q21 <= 8'h00; mul5_q22 <= 8'h00;
    end else if (v11) begin
      mul5_q00 <= m5_p00;
      mul5_q01 <= m5_p01 ^ r12_in;
      mul5_q02 <= m5_p02 ^ r13_in;
      mul5_q10 <= m5_p10 ^ r12_in;
      mul5_q11 <= m5_p11;
      mul5_q12 <= m5_p12 ^ r14_in;
      mul5_q20 <= m5_p20 ^ r13_in;
      mul5_q21 <= m5_p21 ^ r14_in;
      mul5_q22 <= m5_p22;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul5_0 <= 8'h00; mul5_1 <= 8'h00; mul5_2 <= 8'h00;
    end else if (v12) begin
      mul5_0 <= mul5_q00 ^ mul5_q01 ^ mul5_q02;
      mul5_1 <= mul5_q10 ^ mul5_q11 ^ mul5_q12;
      mul5_2 <= mul5_q20 ^ mul5_q21 ^ mul5_q22;
    end
  end

  // ---- inv: (x^126) * (x^128) -> x^254 = x^-1
  //      a = mul5, b = x_s7_d6, masks r15/r16/r17 ---------------------
  wire [7:0] m6_p00, m6_p01, m6_p02, m6_p10, m6_p11, m6_p12,
             m6_p20, m6_p21, m6_p22;
  gf_mul_byte_mod_d2 u_m6_p00 (.a(mul5_0), .b(x0_s7_d6), .y(m6_p00));
  gf_mul_byte_mod_d2 u_m6_p01 (.a(mul5_0), .b(x1_s7_d6), .y(m6_p01));
  gf_mul_byte_mod_d2 u_m6_p02 (.a(mul5_0), .b(x2_s7_d6), .y(m6_p02));
  gf_mul_byte_mod_d2 u_m6_p10 (.a(mul5_1), .b(x0_s7_d6), .y(m6_p10));
  gf_mul_byte_mod_d2 u_m6_p11 (.a(mul5_1), .b(x1_s7_d6), .y(m6_p11));
  gf_mul_byte_mod_d2 u_m6_p12 (.a(mul5_1), .b(x2_s7_d6), .y(m6_p12));
  gf_mul_byte_mod_d2 u_m6_p20 (.a(mul5_2), .b(x0_s7_d6), .y(m6_p20));
  gf_mul_byte_mod_d2 u_m6_p21 (.a(mul5_2), .b(x1_s7_d6), .y(m6_p21));
  gf_mul_byte_mod_d2 u_m6_p22 (.a(mul5_2), .b(x2_s7_d6), .y(m6_p22));

  reg [7:0] inv_q00, inv_q01, inv_q02, inv_q10, inv_q11, inv_q12,
            inv_q20, inv_q21, inv_q22;
  reg [7:0] inv0, inv1, inv2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      inv_q00 <= 8'h00; inv_q01 <= 8'h00; inv_q02 <= 8'h00;
      inv_q10 <= 8'h00; inv_q11 <= 8'h00; inv_q12 <= 8'h00;
      inv_q20 <= 8'h00; inv_q21 <= 8'h00; inv_q22 <= 8'h00;
    end else if (v13) begin
      inv_q00 <= m6_p00;
      inv_q01 <= m6_p01 ^ r15_in;
      inv_q02 <= m6_p02 ^ r16_in;
      inv_q10 <= m6_p10 ^ r15_in;
      inv_q11 <= m6_p11;
      inv_q12 <= m6_p12 ^ r17_in;
      inv_q20 <= m6_p20 ^ r16_in;
      inv_q21 <= m6_p21 ^ r17_in;
      inv_q22 <= m6_p22;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      inv0 <= 8'h00; inv1 <= 8'h00; inv2 <= 8'h00;
    end else if (v14) begin
      inv0 <= inv_q00 ^ inv_q01 ^ inv_q02;
      inv1 <= inv_q10 ^ inv_q11 ^ inv_q12;
      inv2 <= inv_q20 ^ inv_q21 ^ inv_q22;
    end
  end

  // ------------------------------------------------------------------
  // STAGE 16: AES affine, one hard cell per share; constant 0x63 is
  // added to share 0 only.
  // ------------------------------------------------------------------
  wire [7:0] aff_inv0, aff_inv1, aff_inv2;
  aes_affine_byte_mod_d2 u_aff_inv0 (.a(inv0), .y(aff_inv0));
  aes_affine_byte_mod_d2 u_aff_inv1 (.a(inv1), .y(aff_inv1));
  aes_affine_byte_mod_d2 u_aff_inv2 (.a(inv2), .y(aff_inv2));

  reg [7:0] aff0, aff1, aff2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      aff0 <= 8'h00; aff1 <= 8'h00; aff2 <= 8'h00;
    end else if (v15) begin
      aff0 <= aff_inv0 ^ 8'h63;
      aff1 <= aff_inv1;
      aff2 <= aff_inv2;
    end
  end

  // (aff0, aff1, aff2) is a sharing of AES S-box(x).

  // ------------------------------------------------------------------
  // STAGE 17: output register.
  // ------------------------------------------------------------------
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      y0_out <= 8'h00; y1_out <= 8'h00; y2_out <= 8'h00;
      valid_out <= 1'b0;
    end else begin
      y0_out <= aff0;
      y1_out <= aff1;
      y2_out <= aff2;
      valid_out <= v16;
    end
  end

endmodule

// =====================================================================
// Hard cells (_d2 suffix to avoid collisions with the d=1 sibling when
// both files are compiled into one testbench).
// =====================================================================

(* keep_hierarchy = 1 *)
module gf_sq_byte_mod_d2 (
    input  wire [7:0] a,
    output wire [7:0] y
);
  assign y = masked_sbox_pkg::gf_sq_byte(a);
endmodule

(* keep_hierarchy = 1 *)
module gf_mul_byte_mod_d2 (
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [7:0] y
);
  assign y = masked_sbox_pkg::gf_mul_byte(a, b);
endmodule

(* keep_hierarchy = 1 *)
module aes_affine_byte_mod_d2 (
    input  wire [7:0] a,
    output wire [7:0] y
);
  assign y = masked_sbox_pkg::aes_affine_byte(a);
endmodule

`endif

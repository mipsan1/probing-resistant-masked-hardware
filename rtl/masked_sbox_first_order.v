// =====================================================================
// masked_sbox_first_order.v
// First-order (d = 1) masked AES S-box with two shares per byte.
//
// Implements the order-d masked multiplier of the manuscript's
// Algorithm 1 (DOM-style with register barrier):
//   q_00 = Reg(a_0 * b_0)
//   q_01 = Reg(a_0 * b_1 ^ r)      r = r_01 (one fresh mask per mult.)
//   q_10 = Reg(a_1 * b_0 ^ r)
//   q_11 = Reg(a_1 * b_1)
//   c_0  = q_00 ^ q_01,  c_1 = q_10 ^ q_11   (compression AFTER barrier)
//
// OPERAND-INDEPENDENCE REFRESH (security-critical):
// Algorithm 1 assumes its two multiplicand sharings are independent.
// In the Itoh-Tsujii chain the first multiplication squares x^2 and
// x^4 whose sharings are ALIGNED with x (share_i(x^(2^k)) =
// share_i(x)^(2^k), Frobenius-linearity).  Without decorrelation, a
// glitch-extended probe on a mul1 cross-term cone observes
// {share0(x^2), share1(x^4)} and recomputes
//      sq(share0(x^2)) ^ share1(x^4) = x0^4 ^ x1^4 = x^4,
// a deterministic first-order leak (confirmed by PROLEAD, -log10(p)
// = inf).  We therefore insert a REGISTERED mask refresh on the
// x^4 operand before it enters mul1:
//      x_s2r = Reg(x_s2 ^ r6)        (both shares, same fresh byte)
// which restores the DOM independent-operand precondition.  Downstream
// multiplications are safe without extra refreshes: their first operand
// is the previous multiplier's output, already re-masked by that
// stage's r_k, hence independent of the squared-chain operand.
//
// HARD-CELL DISCIPLINE (glitch-robust non-completeness under synthesis):
// every GF(2^8) square / multiply / affine cloud is instantiated as its
// own keep_hierarchy module (gf_sq_byte_mod / gf_mul_byte_mod /
// aes_affine_byte_mod, defined at the bottom of this file).  This
// prevents the technology mapper from factoring logic ACROSS domain
// boundaries (e.g. merging a_0*b and a_1*b into shared product terms),
// which would otherwise recreate a first-order glitch leak even though
// the register barrier is architecturally correct.  Yosys `abc` maps
// each hard cell independently; the final `flatten` is purely
// structural, so the non-completeness proven in the manuscript survives
// synthesis.
//
// Pipeline structure (one invocation per window; the input is applied
// at cycle 0 and held while the pipe processes it):
//   c0:      input register (x_s0)
//   c1..c7:  squaring chain (x^2 .. x^128), share-wise
//   c3:      mul1 operand stage: x_s1_d1 <= x_s1 ; x_s2r <= x_s2 ^ r6
//   Each multiplication takes TWO register stages (q-barrier, then
//   compression); power taps are delayed by matched shift registers:
//     mul1 q@c4  c@c5   (x^2 * x^4    -> x^6)
//     mul2 q@c6  c@c7   (x^6 * x^8    -> x^14)
//     mul3 q@c8  c@c9   (x^14 * x^16  -> x^30)
//     mul4 q@c10 c@c11  (x^30 * x^32  -> x^62)
//     mul5 q@c12 c@c13  (x^62 * x^64  -> x^126)
//     inv  q@c14 c@c15  (x^126 * x^128 -> x^254 = x^-1)
//   c16:     AES affine (share-wise linear + 0x63 on share 0)
//   c17:     output register (valid_out)
//
// Fresh randomness: 1 byte per multiplication (r_01 of Algorithm 1)
// plus 1 byte for the mul1 operand refresh = 7 random bytes per S-box
// invocation.
// =====================================================================

`ifndef MASKED_SBOX_FIRST_ORDER_V
`define MASKED_SBOX_FIRST_ORDER_V

`include "masked_sbox_pkg.v"

module masked_sbox_first_order (
    input              clk,
    input              rst_n,
    input              valid_in,
    input      [7:0]   x0_in,   // share 0 of input
    input      [7:0]   x1_in,   // share 1 of input (XOR with x0_in is the secret)
    // Fresh randomness: 1 byte per multiplication (Algorithm 1) plus
    // 1 byte for the mul1 operand refresh = 7 bytes per invocation.
    input      [7:0]   r0_in,   // mul1 r_01
    input      [7:0]   r1_in,   // mul2 r_01
    input      [7:0]   r2_in,   // mul3 r_01
    input      [7:0]   r3_in,   // mul4 r_01
    input      [7:0]   r4_in,   // mul5 r_01
    input      [7:0]   r5_in,   // inv  r_01
    input      [7:0]   r6_in,   // mul1 operand refresh (x^4 path)
    output reg         valid_out,
    output reg [7:0]   y0_out,  // share 0 of AES S-box output
    output reg [7:0]   y1_out   // share 1 of AES S-box output
);

  // ------------------------------------------------------------------
  // STAGE 0: input registers
  // ------------------------------------------------------------------
  reg [7:0] x0_s0, x1_s0;
  reg [7:0] x0_s1, x1_s1;  // x^2 register
  reg [7:0] x0_s2, x1_s2;  // x^4 register
  reg [7:0] x0_s3, x1_s3;  // x^8 register
  reg [7:0] x0_s4, x1_s4;  // x^16 register
  reg [7:0] x0_s5, x1_s5;  // x^32 register
  reg [7:0] x0_s6, x1_s6;  // x^64 register
  reg [7:0] x0_s7, x1_s7;  // x^128 register

  // ------------------------------------------------------------------
  // Per-stage valid registers. Shift-register of valid bits; each stage
  // is enabled by its own valid bit so registers hold stale data while
  // the pipe is empty.  Depth is 17 (one valid bit per pipeline stage:
  // input, 7 squarings, mul1 operand stage, 6 x 2 multiplier stages,
  // affine, output).
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
  // STAGE 1: squaring chain, one hard cell per share per stage so the
  // two shares' clouds can never be merged by the mapper.
  // ------------------------------------------------------------------
  wire [7:0] sq_x0_s0, sq_x1_s0;
  gf_sq_byte_mod u_sq_x0_s0 (.a(x0_s0), .y(sq_x0_s0));
  gf_sq_byte_mod u_sq_x1_s0 (.a(x1_s0), .y(sq_x1_s0));

  wire [7:0] sq_x0_s1, sq_x1_s1;
  gf_sq_byte_mod u_sq_x0_s1 (.a(x0_s1), .y(sq_x0_s1));
  gf_sq_byte_mod u_sq_x1_s1 (.a(x1_s1), .y(sq_x1_s1));

  wire [7:0] sq_x0_s2, sq_x1_s2;
  gf_sq_byte_mod u_sq_x0_s2 (.a(x0_s2), .y(sq_x0_s2));
  gf_sq_byte_mod u_sq_x1_s2 (.a(x1_s2), .y(sq_x1_s2));

  wire [7:0] sq_x0_s3, sq_x1_s3;
  gf_sq_byte_mod u_sq_x0_s3 (.a(x0_s3), .y(sq_x0_s3));
  gf_sq_byte_mod u_sq_x1_s3 (.a(x1_s3), .y(sq_x1_s3));

  wire [7:0] sq_x0_s4, sq_x1_s4;
  gf_sq_byte_mod u_sq_x0_s4 (.a(x0_s4), .y(sq_x0_s4));
  gf_sq_byte_mod u_sq_x1_s4 (.a(x1_s4), .y(sq_x1_s4));

  wire [7:0] sq_x0_s5, sq_x1_s5;
  gf_sq_byte_mod u_sq_x0_s5 (.a(x0_s5), .y(sq_x0_s5));
  gf_sq_byte_mod u_sq_x1_s5 (.a(x1_s5), .y(sq_x1_s5));

  wire [7:0] sq_x0_s6, sq_x1_s6;
  gf_sq_byte_mod u_sq_x0_s6 (.a(x0_s6), .y(sq_x0_s6));
  gf_sq_byte_mod u_sq_x1_s6 (.a(x1_s6), .y(sq_x1_s6));

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s0 <= 8'h00; x1_s0 <= 8'h00;
    end else if (valid_in) begin
      x0_s0 <= x0_in;
      x1_s0 <= x1_in;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s1 <= 8'h00; x1_s1 <= 8'h00;
    end else if (v0) begin
      x0_s1 <= sq_x0_s0;
      x1_s1 <= sq_x1_s0;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s2 <= 8'h00; x1_s2 <= 8'h00;
    end else if (v1) begin
      x0_s2 <= sq_x0_s1;
      x1_s2 <= sq_x1_s1;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s3 <= 8'h00; x1_s3 <= 8'h00;
    end else if (v2) begin
      x0_s3 <= sq_x0_s2;
      x1_s3 <= sq_x1_s2;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s4 <= 8'h00; x1_s4 <= 8'h00;
    end else if (v3) begin
      x0_s4 <= sq_x0_s3;
      x1_s4 <= sq_x1_s3;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s5 <= 8'h00; x1_s5 <= 8'h00;
    end else if (v4) begin
      x0_s5 <= sq_x0_s4;
      x1_s5 <= sq_x1_s4;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s6 <= 8'h00; x1_s6 <= 8'h00;
    end else if (v5) begin
      x0_s6 <= sq_x0_s5;
      x1_s6 <= sq_x1_s5;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s7 <= 8'h00; x1_s7 <= 8'h00;
    end else if (v6) begin
      x0_s7 <= sq_x0_s6;
      x1_s7 <= sq_x1_s6;
    end
  end

  // After seven squarings, (x0_s7, x1_s7) is a sharing of x^128.

  // ------------------------------------------------------------------
  // mul1 operand stage (c3): delay the x^2 operand by one cycle and
  // REGISTER-REFRESH the x^4 operand with r6 so that the two mul1
  // multiplicand sharings are independent (see header comment).
  // ------------------------------------------------------------------
  reg [7:0] x0_s1_d1, x1_s1_d1;      // x^2 delayed to mul1 timing
  reg [7:0] x0_s2r,   x1_s2r;        // x^4 ^ r6 (operand refresh)

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s1_d1 <= 8'h00; x1_s1_d1 <= 8'h00;
    end else if (v2) begin
      x0_s1_d1 <= x0_s1;
      x1_s1_d1 <= x1_s1;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s2r <= 8'h00; x1_s2r <= 8'h00;
    end else if (v2) begin
      x0_s2r <= x0_s2 ^ r6_in;
      x1_s2r <= x1_s2 ^ r6_in;
    end
  end

  // ------------------------------------------------------------------
  // Power-tap delay lines (see header comment for the schedule).
  // ------------------------------------------------------------------
  reg [7:0] x0_s3_d1, x1_s3_d1, x0_s3_d2, x1_s3_d2;
  reg [7:0] x0_s4_d1, x1_s4_d1, x0_s4_d2, x1_s4_d2, x0_s4_d3, x1_s4_d3;
  reg [7:0] x0_s5_d1, x1_s5_d1, x0_s5_d2, x1_s5_d2, x0_s5_d3, x1_s5_d3,
            x0_s5_d4, x1_s5_d4;
  reg [7:0] x0_s6_d1, x1_s6_d1, x0_s6_d2, x1_s6_d2, x0_s6_d3, x1_s6_d3,
            x0_s6_d4, x1_s6_d4, x0_s6_d5, x1_s6_d5;
  reg [7:0] x0_s7_d1, x1_s7_d1, x0_s7_d2, x1_s7_d2, x0_s7_d3, x1_s7_d3,
            x0_s7_d4, x1_s7_d4, x0_s7_d5, x1_s7_d5, x0_s7_d6, x1_s7_d6;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s3_d1 <= 8'h00; x1_s3_d1 <= 8'h00;
      x0_s3_d2 <= 8'h00; x1_s3_d2 <= 8'h00;
    end else begin
      if (v3) begin x0_s3_d1 <= x0_s3;    x1_s3_d1 <= x1_s3;    end
      if (v4) begin x0_s3_d2 <= x0_s3_d1; x1_s3_d2 <= x1_s3_d1; end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s4_d1 <= 8'h00; x1_s4_d1 <= 8'h00;
      x0_s4_d2 <= 8'h00; x1_s4_d2 <= 8'h00;
      x0_s4_d3 <= 8'h00; x1_s4_d3 <= 8'h00;
    end else begin
      if (v4) begin x0_s4_d1 <= x0_s4;    x1_s4_d1 <= x1_s4;    end
      if (v5) begin x0_s4_d2 <= x0_s4_d1; x1_s4_d2 <= x1_s4_d1; end
      if (v6) begin x0_s4_d3 <= x0_s4_d2; x1_s4_d3 <= x1_s4_d2; end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s5_d1 <= 8'h00; x1_s5_d1 <= 8'h00;
      x0_s5_d2 <= 8'h00; x1_s5_d2 <= 8'h00;
      x0_s5_d3 <= 8'h00; x1_s5_d3 <= 8'h00;
      x0_s5_d4 <= 8'h00; x1_s5_d4 <= 8'h00;
    end else begin
      if (v5) begin x0_s5_d1 <= x0_s5;    x1_s5_d1 <= x1_s5;    end
      if (v6) begin x0_s5_d2 <= x0_s5_d1; x1_s5_d2 <= x1_s5_d1; end
      if (v7) begin x0_s5_d3 <= x0_s5_d2; x1_s5_d3 <= x1_s5_d2; end
      if (v8) begin x0_s5_d4 <= x0_s5_d3; x1_s5_d4 <= x1_s5_d3; end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s6_d1 <= 8'h00; x1_s6_d1 <= 8'h00;
      x0_s6_d2 <= 8'h00; x1_s6_d2 <= 8'h00;
      x0_s6_d3 <= 8'h00; x1_s6_d3 <= 8'h00;
      x0_s6_d4 <= 8'h00; x1_s6_d4 <= 8'h00;
      x0_s6_d5 <= 8'h00; x1_s6_d5 <= 8'h00;
    end else begin
      if (v6)  begin x0_s6_d1 <= x0_s6;    x1_s6_d1 <= x1_s6;    end
      if (v7)  begin x0_s6_d2 <= x0_s6_d1; x1_s6_d2 <= x1_s6_d1; end
      if (v8)  begin x0_s6_d3 <= x0_s6_d2; x1_s6_d3 <= x1_s6_d2; end
      if (v9)  begin x0_s6_d4 <= x0_s6_d3; x1_s6_d4 <= x1_s6_d3; end
      if (v10) begin x0_s6_d5 <= x0_s6_d4; x1_s6_d5 <= x1_s6_d4; end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s7_d1 <= 8'h00; x1_s7_d1 <= 8'h00;
      x0_s7_d2 <= 8'h00; x1_s7_d2 <= 8'h00;
      x0_s7_d3 <= 8'h00; x1_s7_d3 <= 8'h00;
      x0_s7_d4 <= 8'h00; x1_s7_d4 <= 8'h00;
      x0_s7_d5 <= 8'h00; x1_s7_d5 <= 8'h00;
      x0_s7_d6 <= 8'h00; x1_s7_d6 <= 8'h00;
    end else begin
      if (v7)  begin x0_s7_d1 <= x0_s7;    x1_s7_d1 <= x1_s7;    end
      if (v8)  begin x0_s7_d2 <= x0_s7_d1; x1_s7_d2 <= x1_s7_d1; end
      if (v9)  begin x0_s7_d3 <= x0_s7_d2; x1_s7_d3 <= x1_s7_d2; end
      if (v10) begin x0_s7_d4 <= x0_s7_d3; x1_s7_d4 <= x1_s7_d3; end
      if (v11) begin x0_s7_d5 <= x0_s7_d4; x1_s7_d5 <= x1_s7_d4; end
      if (v12) begin x0_s7_d6 <= x0_s7_d5; x1_s7_d6 <= x1_s7_d5; end
    end
  end

  // ------------------------------------------------------------------
  // STAGE 2..15: six masked multiplications implementing Algorithm 1
  // with the register barrier.  Every domain product is its own hard
  // cell (gf_mul_byte_mod) so no two products are ever merged before
  // registration, in netlist structure as well as by construction.
  // ------------------------------------------------------------------

  // ---- mul1: (x^2) * (x^4 ^ r6) -> x^6  (a = x_s1_d1, b = x_s2r, r = r0_in)
  wire [7:0] m1_p00, m1_p01, m1_p10, m1_p11;
  gf_mul_byte_mod u_m1_p00 (.a(x0_s1_d1), .b(x0_s2r), .y(m1_p00));
  gf_mul_byte_mod u_m1_p01 (.a(x0_s1_d1), .b(x1_s2r), .y(m1_p01));
  gf_mul_byte_mod u_m1_p10 (.a(x1_s1_d1), .b(x0_s2r), .y(m1_p10));
  gf_mul_byte_mod u_m1_p11 (.a(x1_s1_d1), .b(x1_s2r), .y(m1_p11));

  reg [7:0] mul1_q00, mul1_q01, mul1_q10, mul1_q11;
  reg [7:0] mul1_0, mul1_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul1_q00 <= 8'h00; mul1_q01 <= 8'h00;
      mul1_q10 <= 8'h00; mul1_q11 <= 8'h00;
    end else if (v3) begin
      mul1_q00 <= m1_p00;
      mul1_q01 <= m1_p01 ^ r0_in;
      mul1_q10 <= m1_p10 ^ r0_in;
      mul1_q11 <= m1_p11;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul1_0 <= 8'h00; mul1_1 <= 8'h00;
    end else if (v4) begin
      mul1_0 <= mul1_q00 ^ mul1_q01;
      mul1_1 <= mul1_q10 ^ mul1_q11;
    end
  end

  // ---- mul2: (x^6) * (x^8) -> x^14 (a = mul1, b = x_s3_d2, r = r1_in)
  wire [7:0] m2_p00, m2_p01, m2_p10, m2_p11;
  gf_mul_byte_mod u_m2_p00 (.a(mul1_0), .b(x0_s3_d2), .y(m2_p00));
  gf_mul_byte_mod u_m2_p01 (.a(mul1_0), .b(x1_s3_d2), .y(m2_p01));
  gf_mul_byte_mod u_m2_p10 (.a(mul1_1), .b(x0_s3_d2), .y(m2_p10));
  gf_mul_byte_mod u_m2_p11 (.a(mul1_1), .b(x1_s3_d2), .y(m2_p11));

  reg [7:0] mul2_q00, mul2_q01, mul2_q10, mul2_q11;
  reg [7:0] mul2_0, mul2_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul2_q00 <= 8'h00; mul2_q01 <= 8'h00;
      mul2_q10 <= 8'h00; mul2_q11 <= 8'h00;
    end else if (v5) begin
      mul2_q00 <= m2_p00;
      mul2_q01 <= m2_p01 ^ r1_in;
      mul2_q10 <= m2_p10 ^ r1_in;
      mul2_q11 <= m2_p11;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul2_0 <= 8'h00; mul2_1 <= 8'h00;
    end else if (v6) begin
      mul2_0 <= mul2_q00 ^ mul2_q01;
      mul2_1 <= mul2_q10 ^ mul2_q11;
    end
  end

  // ---- mul3: (x^14) * (x^16) -> x^30 (a = mul2, b = x_s4_d3, r = r2_in)
  wire [7:0] m3_p00, m3_p01, m3_p10, m3_p11;
  gf_mul_byte_mod u_m3_p00 (.a(mul2_0), .b(x0_s4_d3), .y(m3_p00));
  gf_mul_byte_mod u_m3_p01 (.a(mul2_0), .b(x1_s4_d3), .y(m3_p01));
  gf_mul_byte_mod u_m3_p10 (.a(mul2_1), .b(x0_s4_d3), .y(m3_p10));
  gf_mul_byte_mod u_m3_p11 (.a(mul2_1), .b(x1_s4_d3), .y(m3_p11));

  reg [7:0] mul3_q00, mul3_q01, mul3_q10, mul3_q11;
  reg [7:0] mul3_0, mul3_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul3_q00 <= 8'h00; mul3_q01 <= 8'h00;
      mul3_q10 <= 8'h00; mul3_q11 <= 8'h00;
    end else if (v7) begin
      mul3_q00 <= m3_p00;
      mul3_q01 <= m3_p01 ^ r2_in;
      mul3_q10 <= m3_p10 ^ r2_in;
      mul3_q11 <= m3_p11;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul3_0 <= 8'h00; mul3_1 <= 8'h00;
    end else if (v8) begin
      mul3_0 <= mul3_q00 ^ mul3_q01;
      mul3_1 <= mul3_q10 ^ mul3_q11;
    end
  end

  // ---- mul4: (x^30) * (x^32) -> x^62 (a = mul3, b = x_s5_d4, r = r3_in)
  wire [7:0] m4_p00, m4_p01, m4_p10, m4_p11;
  gf_mul_byte_mod u_m4_p00 (.a(mul3_0), .b(x0_s5_d4), .y(m4_p00));
  gf_mul_byte_mod u_m4_p01 (.a(mul3_0), .b(x1_s5_d4), .y(m4_p01));
  gf_mul_byte_mod u_m4_p10 (.a(mul3_1), .b(x0_s5_d4), .y(m4_p10));
  gf_mul_byte_mod u_m4_p11 (.a(mul3_1), .b(x1_s5_d4), .y(m4_p11));

  reg [7:0] mul4_q00, mul4_q01, mul4_q10, mul4_q11;
  reg [7:0] mul4_0, mul4_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul4_q00 <= 8'h00; mul4_q01 <= 8'h00;
      mul4_q10 <= 8'h00; mul4_q11 <= 8'h00;
    end else if (v9) begin
      mul4_q00 <= m4_p00;
      mul4_q01 <= m4_p01 ^ r3_in;
      mul4_q10 <= m4_p10 ^ r3_in;
      mul4_q11 <= m4_p11;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul4_0 <= 8'h00; mul4_1 <= 8'h00;
    end else if (v10) begin
      mul4_0 <= mul4_q00 ^ mul4_q01;
      mul4_1 <= mul4_q10 ^ mul4_q11;
    end
  end

  // ---- mul5: (x^62) * (x^64) -> x^126 (a = mul4, b = x_s6_d5, r = r4_in)
  wire [7:0] m5_p00, m5_p01, m5_p10, m5_p11;
  gf_mul_byte_mod u_m5_p00 (.a(mul4_0), .b(x0_s6_d5), .y(m5_p00));
  gf_mul_byte_mod u_m5_p01 (.a(mul4_0), .b(x1_s6_d5), .y(m5_p01));
  gf_mul_byte_mod u_m5_p10 (.a(mul4_1), .b(x0_s6_d5), .y(m5_p10));
  gf_mul_byte_mod u_m5_p11 (.a(mul4_1), .b(x1_s6_d5), .y(m5_p11));

  reg [7:0] mul5_q00, mul5_q01, mul5_q10, mul5_q11;
  reg [7:0] mul5_0, mul5_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul5_q00 <= 8'h00; mul5_q01 <= 8'h00;
      mul5_q10 <= 8'h00; mul5_q11 <= 8'h00;
    end else if (v11) begin
      mul5_q00 <= m5_p00;
      mul5_q01 <= m5_p01 ^ r4_in;
      mul5_q10 <= m5_p10 ^ r4_in;
      mul5_q11 <= m5_p11;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul5_0 <= 8'h00; mul5_1 <= 8'h00;
    end else if (v12) begin
      mul5_0 <= mul5_q00 ^ mul5_q01;
      mul5_1 <= mul5_q10 ^ mul5_q11;
    end
  end

  // ---- inv: (x^126) * (x^128) -> x^254 = x^-1 (a = mul5, b = x_s7_d6, r = r5_in)
  wire [7:0] m6_p00, m6_p01, m6_p10, m6_p11;
  gf_mul_byte_mod u_m6_p00 (.a(mul5_0), .b(x0_s7_d6), .y(m6_p00));
  gf_mul_byte_mod u_m6_p01 (.a(mul5_0), .b(x1_s7_d6), .y(m6_p01));
  gf_mul_byte_mod u_m6_p10 (.a(mul5_1), .b(x0_s7_d6), .y(m6_p10));
  gf_mul_byte_mod u_m6_p11 (.a(mul5_1), .b(x1_s7_d6), .y(m6_p11));

  reg [7:0] inv_q00, inv_q01, inv_q10, inv_q11;
  reg [7:0] inv0, inv1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      inv_q00 <= 8'h00; inv_q01 <= 8'h00;
      inv_q10 <= 8'h00; inv_q11 <= 8'h00;
    end else if (v13) begin
      inv_q00 <= m6_p00;
      inv_q01 <= m6_p01 ^ r5_in;
      inv_q10 <= m6_p10 ^ r5_in;
      inv_q11 <= m6_p11;
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      inv0 <= 8'h00; inv1 <= 8'h00;
    end else if (v14) begin
      inv0 <= inv_q00 ^ inv_q01;
      inv1 <= inv_q10 ^ inv_q11;
    end
  end

  // ------------------------------------------------------------------
  // STAGE 16: AES affine, one hard cell per share; constant 0x63 is
  // added to the first share.
  // ------------------------------------------------------------------
  wire [7:0] aff_inv0, aff_inv1;
  aes_affine_byte_mod u_aff_inv0 (.a(inv0), .y(aff_inv0));
  aes_affine_byte_mod u_aff_inv1 (.a(inv1), .y(aff_inv1));

  reg [7:0] aff0, aff1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      aff0 <= 8'h00; aff1 <= 8'h00;
    end else if (v15) begin
      aff0 <= aff_inv0 ^ 8'h63;
      aff1 <= aff_inv1;
    end
  end

  // (aff0, aff1) is a sharing of AES S-box(x).

  // ------------------------------------------------------------------
  // STAGE 17: output register.
  // ------------------------------------------------------------------
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      y0_out <= 8'h00; y1_out <= 8'h00;
      valid_out <= 1'b0;
    end else begin
      y0_out <= aff0;
      y1_out <= aff1;
      valid_out <= v16;
    end
  end

endmodule

// =====================================================================
// Hard cells: each GF cloud as its own hierarchy-preserving module so
// technology mapping can never share logic across security domains.
// =====================================================================

(* keep_hierarchy = 1 *)
module gf_sq_byte_mod (
    input  wire [7:0] a,
    output wire [7:0] y
);
  assign y = masked_sbox_pkg::gf_sq_byte(a);
endmodule

(* keep_hierarchy = 1 *)
module gf_mul_byte_mod (
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [7:0] y
);
  assign y = masked_sbox_pkg::gf_mul_byte(a, b);
endmodule

(* keep_hierarchy = 1 *)
module aes_affine_byte_mod (
    input  wire [7:0] a,
    output wire [7:0] y
);
  assign y = masked_sbox_pkg::aes_affine_byte(a);
endmodule

`endif

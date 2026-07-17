// =====================================================================
// masked_sbox_first_order.v
// First-order (d = 1) masked AES S-box with two shares per byte.
//
// Pipeline structure (matches the reference/gf_mul_secure multiplier):
//   STAGE 0: input register
//   STAGE 1: squaring chain (x -> x^2 -> x^4 -> x^8 -> x^16 -> x^32
//             -> x^64 -> x^128) — each squaring is share-wise
//   STAGE 2..8: 7 masked multiplications to combine the seven needed
//             powers (x^2, x^4, ..., x^128) into x^254 = x^-1
//   STAGE 9: AES affine (share-wise linear + constant on one share)
//   STAGE 10: output register
//
// Each masked multiplication is the Andreasen gadget:
//
//   For k in 0..d:        (k = 0, 1)
//     p_k = a_k * b       (clear multiplications, both shares of b)
//     p_k = refresh(p_k)
//   out = sum_k p_k       (XOR share-wise)
//
// where b is the (d+1)-sharing of the second operand, and
// refresh is the ISW'03 d-probing-secure refresh.  For d = 1
// each refresh uses 2 random bytes; 2 partial products x 2 bytes
// = 4 bytes per multiplication.  Total: 7 * 4 = 28 random bytes
// per S-box invocation.  Each multiplication also requires
// 4 clear gf_mul_byte calls (one per (a_k, b_j) pair).
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
    // Fresh randomness: 4 bytes per multiplication, 7 multiplications
    // = 28 bytes total per S-box invocation.  Each group of 4 bytes
    // is the (m_0, m_1, m_2, m_3) for the ISW refresh of the two
    // partial products in one multiplication stage.
    input      [7:0]   r0_in,   // stage 1 m_0
    input      [7:0]   r1_in,   // stage 1 m_1
    input      [7:0]   r2_in,   // stage 1 m_2
    input      [7:0]   r3_in,   // stage 1 m_3
    input      [7:0]   r4_in,   // stage 2 m_0
    input      [7:0]   r5_in,   // stage 2 m_1
    input      [7:0]   r6_in,   // stage 2 m_2
    input      [7:0]   r7_in,   // stage 2 m_3
    input      [7:0]   r8_in,   // stage 3 m_0
    input      [7:0]   r9_in,   // stage 3 m_1
    input      [7:0]   r10_in,  // stage 3 m_2
    input      [7:0]   r11_in,  // stage 3 m_3
    input      [7:0]   r12_in,  // stage 4 m_0
    input      [7:0]   r13_in,  // stage 4 m_1
    input      [7:0]   r14_in,  // stage 4 m_2
    input      [7:0]   r15_in,  // stage 4 m_3
    input      [7:0]   r16_in,  // stage 5 m_0
    input      [7:0]   r17_in,  // stage 5 m_1
    input      [7:0]   r18_in,  // stage 5 m_2
    input      [7:0]   r19_in,  // stage 5 m_3
    input      [7:0]   r20_in,  // stage 6 m_0
    input      [7:0]   r21_in,  // stage 6 m_1
    input      [7:0]   r22_in,  // stage 6 m_2
    input      [7:0]   r23_in,  // stage 6 m_3
    input      [7:0]   r24_in,  // stage 7 m_0
    input      [7:0]   r25_in,  // stage 7 m_1
    input      [7:0]   r26_in,  // stage 7 m_2
    input      [7:0]   r27_in,  // stage 7 m_3
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
  // Per-stage valid registers. We use a shift-register of valid
  // signals: each cycle, each stage's valid is replaced by the
  // previous stage's valid. Reset zeros the whole chain. This avoids
  // the bug of valid staying high forever when stage logic is gated
  // by an `if (valid)` that has no `else`.
  //
  // Pipeline depth = 10 cycles (input, 7 squarings, 1 multiplication
  // producing inv, 1 affine, 1 output). So we keep 10 valid bits
  // and present valid_out = valid[10].
  // ------------------------------------------------------------------
  reg [9:0] valid_pipe;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 10'b0;
    end else begin
      valid_pipe <= {valid_pipe[8:0], valid_in};
    end
  end

  wire v0 = valid_pipe[0];  // x0_s0/x1_s0 valid
  wire v1 = valid_pipe[1];  // x0_s1/x1_s1 valid
  wire v2 = valid_pipe[2];  // x0_s2/x1_s2 valid
  wire v3 = valid_pipe[3];  // x0_s3/x1_s3 valid
  wire v4 = valid_pipe[4];  // x0_s4/x1_s4 valid
  wire v5 = valid_pipe[5];  // x0_s5/x1_s5 valid
  wire v6 = valid_pipe[6];  // x0_s6/x1_s6 valid
  wire v7 = valid_pipe[7];  // x0_s7/x1_s7 valid
  wire v8 = valid_pipe[8];  // inv0/inv1 valid
  wire v9 = valid_pipe[9];  // aff0/aff1 valid (output)

  // ------------------------------------------------------------------
  // STAGE 0: input register
  // ------------------------------------------------------------------
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s0 <= 8'h00; x1_s0 <= 8'h00;
    end else if (valid_in) begin
      x0_s0 <= x0_in;
      x1_s0 <= x1_in;
    end
  end

  // ------------------------------------------------------------------
  // STAGE 1: squaring chain. Squaring in GF(2^8) is the Frobenius
  // map x -> x^2, which is linear over GF(2). Therefore (s_0^2,
  // s_1^2) is a valid (d+1)-sharing of x^2 — share-wise squaring
  // commutes with the sharing. Each squaring is a combinational
  // cloud; the register between squarings is a *free* register
  // barrier (no refresh needed) because squaring is linear.
  //
  // We gate the next-stage enable with the *current* stage's valid
  // bit so that stale data is not squaring/refreshed when the pipe
  // is empty.
  // ------------------------------------------------------------------
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s1 <= 8'h00; x1_s1 <= 8'h00;
    end else if (v0) begin
      x0_s1 <= masked_sbox_pkg::gf_sq_byte(x0_s0);
      x1_s1 <= masked_sbox_pkg::gf_sq_byte(x1_s0);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s2 <= 8'h00; x1_s2 <= 8'h00;
    end else if (v1) begin
      x0_s2 <= masked_sbox_pkg::gf_sq_byte(x0_s1);
      x1_s2 <= masked_sbox_pkg::gf_sq_byte(x1_s1);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s3 <= 8'h00; x1_s3 <= 8'h00;
    end else if (v2) begin
      x0_s3 <= masked_sbox_pkg::gf_sq_byte(x0_s2);
      x1_s3 <= masked_sbox_pkg::gf_sq_byte(x1_s2);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s4 <= 8'h00; x1_s4 <= 8'h00;
    end else if (v3) begin
      x0_s4 <= masked_sbox_pkg::gf_sq_byte(x0_s3);
      x1_s4 <= masked_sbox_pkg::gf_sq_byte(x1_s3);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s5 <= 8'h00; x1_s5 <= 8'h00;
    end else if (v4) begin
      x0_s5 <= masked_sbox_pkg::gf_sq_byte(x0_s4);
      x1_s5 <= masked_sbox_pkg::gf_sq_byte(x1_s4);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s6 <= 8'h00; x1_s6 <= 8'h00;
    end else if (v5) begin
      x0_s6 <= masked_sbox_pkg::gf_sq_byte(x0_s5);
      x1_s6 <= masked_sbox_pkg::gf_sq_byte(x1_s5);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s7 <= 8'h00; x1_s7 <= 8'h00;
    end else if (v6) begin
      x0_s7 <= masked_sbox_pkg::gf_sq_byte(x0_s6);
      x1_s7 <= masked_sbox_pkg::gf_sq_byte(x1_s6);
    end
  end

  // After seven squarings, (x0_s7, x1_s7) is a sharing of x^128.

  // ------------------------------------------------------------------
  // STAGE 2..8: seven masked multiplications.
  //
  // Per stage, given:
  //   a = (a_0, a_1)            (2 shares of operand A)
  //   b = (b_0, b_1)            (2 shares of operand B)
  //   masks m_0..m_3            (4 fresh random bytes)
  //
  // Compute:
  //   p0_0 = a_0 * b_0;         (clear)
  //   p0_1 = a_0 * b_1;         (clear)
  //   p1_0 = a_1 * b_0;         (clear)
  //   p1_1 = a_1 * b_1;         (clear)
  //   p0'  = refresh(p0)        using m_0, m_1
  //   p1'  = refresh(p1)        using m_2, m_3
  //   out_0 = p0'_0 ^ p1'_0
  //   out_1 = p0'_1 ^ p1'_1
  //
  // Verify the secret: out_0 ^ out_1 = (p0_0^p1_0) ^ (p0_1^p1_1)
  //   = (a_0+a_1)*b_0 ^ (a_0+a_1)*b_1 = (a_0+a_1)*(b_0+b_1) = A*B.
  // ------------------------------------------------------------------

  // STAGE 2: (x^2) * (x^4) -> x^6
  reg [7:0] mul1_0, mul1_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul1_0 <= 8'h00; mul1_1 <= 8'h00;
    end else if (v2) begin
      // 4 partial products, share-wise: p00=a0*b0, p01=a0*b1, p10=a1*b0, p11=a1*b1
      mul1_0 <= ((masked_sbox_pkg::gf_mul_byte(x0_s1, x0_s2) ^ r0_in ^ r1_in) ^
                 (masked_sbox_pkg::gf_mul_byte(x1_s1, x0_s2) ^ r2_in ^ r3_in));
      mul1_1 <= ((masked_sbox_pkg::gf_mul_byte(x0_s1, x1_s2) ^ r0_in ^ r1_in) ^
                 (masked_sbox_pkg::gf_mul_byte(x1_s1, x1_s2) ^ r2_in ^ r3_in));
    end
  end

  // STAGE 3: (x^6) * (x^8) -> x^14
  reg [7:0] mul2_0, mul2_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul2_0 <= 8'h00; mul2_1 <= 8'h00;
    end else if (v3) begin
      mul2_0 <= ((masked_sbox_pkg::gf_mul_byte(mul1_0, x0_s3) ^ r4_in ^ r5_in) ^
                 (masked_sbox_pkg::gf_mul_byte(mul1_1, x0_s3) ^ r6_in ^ r7_in));
      mul2_1 <= ((masked_sbox_pkg::gf_mul_byte(mul1_0, x1_s3) ^ r4_in ^ r5_in) ^
                 (masked_sbox_pkg::gf_mul_byte(mul1_1, x1_s3) ^ r6_in ^ r7_in));
    end
  end

  // STAGE 4: (x^14) * (x^16) -> x^30
  reg [7:0] mul3_0, mul3_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul3_0 <= 8'h00; mul3_1 <= 8'h00;
    end else if (v4) begin
      mul3_0 <= ((masked_sbox_pkg::gf_mul_byte(mul2_0, x0_s4) ^ r8_in ^ r9_in) ^
                 (masked_sbox_pkg::gf_mul_byte(mul2_1, x0_s4) ^ r10_in ^ r11_in));
      mul3_1 <= ((masked_sbox_pkg::gf_mul_byte(mul2_0, x1_s4) ^ r8_in ^ r9_in) ^
                 (masked_sbox_pkg::gf_mul_byte(mul2_1, x1_s4) ^ r10_in ^ r11_in));
    end
  end

  // STAGE 5: (x^30) * (x^32) -> x^62
  reg [7:0] mul4_0, mul4_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul4_0 <= 8'h00; mul4_1 <= 8'h00;
    end else if (v5) begin
      mul4_0 <= ((masked_sbox_pkg::gf_mul_byte(mul3_0, x0_s5) ^ r12_in ^ r13_in) ^
                 (masked_sbox_pkg::gf_mul_byte(mul3_1, x0_s5) ^ r14_in ^ r15_in));
      mul4_1 <= ((masked_sbox_pkg::gf_mul_byte(mul3_0, x1_s5) ^ r12_in ^ r13_in) ^
                 (masked_sbox_pkg::gf_mul_byte(mul3_1, x1_s5) ^ r14_in ^ r15_in));
    end
  end

  // STAGE 6: (x^62) * (x^64) -> x^126
  reg [7:0] mul5_0, mul5_1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mul5_0 <= 8'h00; mul5_1 <= 8'h00;
    end else if (v6) begin
      mul5_0 <= ((masked_sbox_pkg::gf_mul_byte(mul4_0, x0_s6) ^ r16_in ^ r17_in) ^
                 (masked_sbox_pkg::gf_mul_byte(mul4_1, x0_s6) ^ r18_in ^ r19_in));
      mul5_1 <= ((masked_sbox_pkg::gf_mul_byte(mul4_0, x1_s6) ^ r16_in ^ r17_in) ^
                 (masked_sbox_pkg::gf_mul_byte(mul4_1, x1_s6) ^ r18_in ^ r19_in));
    end
  end

  // STAGE 7: (x^126) * (x^128) -> x^254 = x^-1 in GF(2^8)
  reg [7:0] inv0, inv1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      inv0 <= 8'h00; inv1 <= 8'h00;
    end else if (v7) begin
      inv0 <= ((masked_sbox_pkg::gf_mul_byte(mul5_0, x0_s7) ^ r20_in ^ r21_in) ^
               (masked_sbox_pkg::gf_mul_byte(mul5_1, x0_s7) ^ r22_in ^ r23_in));
      inv1 <= ((masked_sbox_pkg::gf_mul_byte(mul5_0, x1_s7) ^ r20_in ^ r21_in) ^
               (masked_sbox_pkg::gf_mul_byte(mul5_1, x1_s7) ^ r22_in ^ r23_in));
    end
  end

  // ------------------------------------------------------------------
  // STAGE 8: AES affine, share-wise. The linear map is share-wise;
  // the constant 0x63 is added to the *first* share (the result of
  // affine(x^-1) = linear(x^-1) ^ 0x63, so 0x63 XORed into any single
  // share preserves the secret).
  // ------------------------------------------------------------------
  reg [7:0] aff0, aff1;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      aff0 <= 8'h00; aff1 <= 8'h00;
    end else if (v8) begin
      aff0 <= masked_sbox_pkg::aes_affine_byte(inv0) ^ 8'h63;
      aff1 <= masked_sbox_pkg::aes_affine_byte(inv1);
    end
  end

  // (aff0, aff1) is a sharing of AES S-box(x).

  // ------------------------------------------------------------------
  // STAGE 9: output register.
  // ------------------------------------------------------------------
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      y0_out <= 8'h00; y1_out <= 8'h00;
      valid_out <= 1'b0;
    end else begin
      y0_out <= aff0;
      y1_out <= aff1;
      valid_out <= v9;
    end
  end

endmodule

`endif

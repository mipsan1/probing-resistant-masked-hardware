// =====================================================================
// masked_sbox_second_order.v
// Second-order (d = 2) masked AES S-box with three shares per byte.
//
// Structure parallels masked_sbox_first_order but with three shares
// per byte. The Andreasen gadget is over three partial products:
//   for k in 0..2:
//     p_k = a_k * (b_0, b_1, b_2)  (3 clear multiplications, 3 shares)
//     p_k = refresh(p_k)            (using 3 random masks)
//   out = sum_k p_k (XOR share-wise)
//
// Each refresh is the ISW'03 §3.1 construction on three shares:
//   s0' = s0 ^ m0 ^ m2
//   s1' = s1 ^ m0 ^ m1
//   s2' = s2 ^ m1 ^ m2
// (s0' ^ s1' ^ s2' = s0 ^ s1 ^ s2 = secret).
// =====================================================================

`ifndef MASKED_SBOX_SECOND_ORDER_V
`define MASKED_SBOX_SECOND_ORDER_V

`include "masked_sbox_pkg.v"

module masked_sbox_second_order (
    input              clk,
    input              rst_n,
    input              valid_in,
    // Input shares: 3 bytes whose XOR is the secret.
    input      [7:0]   x0_in, x1_in, x2_in,
    // Fresh randomness for the 7 masked multiplications and
    // their refresh masks. For each multiplication we feed 9 bytes
    // (3 per partial-product refresh, 3 partial products). Total
    // 63 bytes. The testbench generates these from a TRNG.
    input      [7:0]   r00, r01, r02,  // mul 1: refresh of p_0 (m0, m1, m2)
    input      [7:0]   r03, r04, r05,  // mul 1: refresh of p_1
    input      [7:0]   r06, r07, r08,  // mul 1: refresh of p_2
    input      [7:0]   r09, r10, r11,  // mul 2: refresh of p_0
    input      [7:0]   r12, r13, r14,  // mul 2: refresh of p_1
    input      [7:0]   r15, r16, r17,  // mul 2: refresh of p_2
    input      [7:0]   r18, r19, r20,  // mul 3: p_0
    input      [7:0]   r21, r22, r23,  // mul 3: p_1
    input      [7:0]   r24, r25, r26,  // mul 3: p_2
    input      [7:0]   r27, r28, r29,  // mul 4: p_0
    input      [7:0]   r30, r31, r32,  // mul 4: p_1
    input      [7:0]   r33, r34, r35,  // mul 4: p_2
    input      [7:0]   r36, r37, r38,  // mul 5: p_0
    input      [7:0]   r39, r40, r41,  // mul 5: p_1
    input      [7:0]   r42, r43, r44,  // mul 5: p_2
    input      [7:0]   r45, r46, r47,  // mul 6: p_0
    input      [7:0]   r48, r49, r50,  // mul 6: p_1
    input      [7:0]   r51, r52, r53,  // mul 6: p_2
    input      [7:0]   r54, r55, r56,  // mul 7: p_0
    input      [7:0]   r57, r58, r59,  // mul 7: p_1
    input      [7:0]   r60, r61, r62,  // mul 7: p_2
    output reg         valid_out,
    output reg [7:0]   y0_out,         // share 0 of AES S-box output
    output reg [7:0]   y1_out,         // share 1
    output reg [7:0]   y2_out          // share 2
);

  // ------------------------------------------------------------------
  // STAGE 0..1: input + squaring chain (share-wise).
  // ------------------------------------------------------------------
  reg [7:0] x0_s0, x1_s0, x2_s0;
  reg [7:0] x0_s1, x1_s1, x2_s1;
  reg [7:0] x0_s2, x1_s2, x2_s2;
  reg [7:0] x0_s3, x1_s3, x2_s3;
  reg [7:0] x0_s4, x1_s4, x2_s4;
  reg [7:0] x0_s5, x1_s5, x2_s5;
  reg [7:0] x0_s6, x1_s6, x2_s6;
  reg [7:0] x0_s7, x1_s7, x2_s7;  // x^128 stage

  // Valid shift-register (10 stages: input, 7 squarings, 1 inv, 1 output)
  reg [9:0] valid_pipe;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      valid_pipe <= 10'b0;
    end else begin
      valid_pipe <= {valid_pipe[8:0], valid_in};
    end
  end

  wire v0 = valid_pipe[0];
  wire v1 = valid_pipe[1];
  wire v2 = valid_pipe[2];
  wire v3 = valid_pipe[3];
  wire v4 = valid_pipe[4];
  wire v5 = valid_pipe[5];
  wire v6 = valid_pipe[6];
  wire v7 = valid_pipe[7];
  wire v8 = valid_pipe[8];
  wire v9 = valid_pipe[9];

  // STAGE 0: input register
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s0 <= 8'h00; x1_s0 <= 8'h00; x2_s0 <= 8'h00;
    end else if (valid_in) begin
      x0_s0 <= x0_in; x1_s0 <= x1_in; x2_s0 <= x2_in;
    end
  end

  // Seven squarings. Each is share-wise (Frobenius is GF(2)-linear).
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s1 <= 8'h00; x1_s1 <= 8'h00; x2_s1 <= 8'h00;
    end else if (v0) begin
      x0_s1 <= masked_sbox_pkg::gf_sq_byte(x0_s0);
      x1_s1 <= masked_sbox_pkg::gf_sq_byte(x1_s0);
      x2_s1 <= masked_sbox_pkg::gf_sq_byte(x2_s0);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s2 <= 8'h00; x1_s2 <= 8'h00; x2_s2 <= 8'h00;
    end else if (v1) begin
      x0_s2 <= masked_sbox_pkg::gf_sq_byte(x0_s1);
      x1_s2 <= masked_sbox_pkg::gf_sq_byte(x1_s1);
      x2_s2 <= masked_sbox_pkg::gf_sq_byte(x2_s1);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s3 <= 8'h00; x1_s3 <= 8'h00; x2_s3 <= 8'h00;
    end else if (v2) begin
      x0_s3 <= masked_sbox_pkg::gf_sq_byte(x0_s2);
      x1_s3 <= masked_sbox_pkg::gf_sq_byte(x1_s2);
      x2_s3 <= masked_sbox_pkg::gf_sq_byte(x2_s2);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s4 <= 8'h00; x1_s4 <= 8'h00; x2_s4 <= 8'h00;
    end else if (v3) begin
      x0_s4 <= masked_sbox_pkg::gf_sq_byte(x0_s3);
      x1_s4 <= masked_sbox_pkg::gf_sq_byte(x1_s3);
      x2_s4 <= masked_sbox_pkg::gf_sq_byte(x2_s3);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s5 <= 8'h00; x1_s5 <= 8'h00; x2_s5 <= 8'h00;
    end else if (v4) begin
      x0_s5 <= masked_sbox_pkg::gf_sq_byte(x0_s4);
      x1_s5 <= masked_sbox_pkg::gf_sq_byte(x1_s4);
      x2_s5 <= masked_sbox_pkg::gf_sq_byte(x2_s4);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s6 <= 8'h00; x1_s6 <= 8'h00; x2_s6 <= 8'h00;
    end else if (v5) begin
      x0_s6 <= masked_sbox_pkg::gf_sq_byte(x0_s5);
      x1_s6 <= masked_sbox_pkg::gf_sq_byte(x1_s5);
      x2_s6 <= masked_sbox_pkg::gf_sq_byte(x2_s5);
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      x0_s7 <= 8'h00; x1_s7 <= 8'h00; x2_s7 <= 8'h00;
    end else if (v6) begin
      x0_s7 <= masked_sbox_pkg::gf_sq_byte(x0_s6);
      x1_s7 <= masked_sbox_pkg::gf_sq_byte(x1_s6);
      x2_s7 <= masked_sbox_pkg::gf_sq_byte(x2_s6);
    end
  end

  // ------------------------------------------------------------------
  // STAGE 2: first masked multiplication (x^2 * x^4) -> x^6.
  //
  // For d=2, we have 3 shares per operand. The Andreasen gadget:
  //   p_k = a_k * b        for k in 0..2    (clear, then re-share)
  //   p_k = refresh(p_k)   for k in 0..2    (3 random masks per refresh)
  //   out = p_0 XOR p_1 XOR p_2  (share-wise)
  //
  // For each k, p_k is a 3-share sharing of a_k * b. Concretely:
  //   p_k_0 = a_k * b_0,   p_k_1 = a_k * b_1,   p_k_2 = a_k * b_2
  //
  // The ISW refresh on a 3-share sharing uses 3 random masks m_0,
  // m_1, m_2 per partial product and applies:
  //   p_k_0' = p_k_0 ^ m_{k,0} ^ m_{k,2}   (since (0-1) mod 3 = 2)
  //   p_k_1' = p_k_1 ^ m_{k,0} ^ m_{k,1}   (since (1-1) mod 3 = 0)
  //   p_k_2' = p_k_2 ^ m_{k,1} ^ m_{k,2}   (since (2-1) mod 3 = 1)
  // ------------------------------------------------------------------
  reg [7:0] m1_a, m1_b, m1_c;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      m1_a <= 8'h00; m1_b <= 8'h00; m1_c <= 8'h00;
    end else if (v2) begin
      // partial product p_0 = a_0 * b (all 3 shares)
      m1_a <= ((masked_sbox_pkg::gf_mul_byte(x0_s1, x0_s2) ^ r00 ^ r02) ^
               (masked_sbox_pkg::gf_mul_byte(x1_s1, x0_s2) ^ r03 ^ r05) ^
               (masked_sbox_pkg::gf_mul_byte(x2_s1, x0_s2) ^ r06 ^ r08));
      m1_b <= ((masked_sbox_pkg::gf_mul_byte(x0_s1, x1_s2) ^ r00 ^ r01) ^
               (masked_sbox_pkg::gf_mul_byte(x1_s1, x1_s2) ^ r03 ^ r04) ^
               (masked_sbox_pkg::gf_mul_byte(x2_s1, x1_s2) ^ r06 ^ r07));
      m1_c <= ((masked_sbox_pkg::gf_mul_byte(x0_s1, x2_s2) ^ r01 ^ r02) ^
               (masked_sbox_pkg::gf_mul_byte(x1_s1, x2_s2) ^ r04 ^ r05) ^
               (masked_sbox_pkg::gf_mul_byte(x2_s1, x2_s2) ^ r07 ^ r08));
    end
  end

  // STAGE 3: m1 * x^8 -> x^14
  reg [7:0] m2_a, m2_b, m2_c;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      m2_a <= 8'h00; m2_b <= 8'h00; m2_c <= 8'h00;
    end else if (v3) begin
      m2_a <= ((masked_sbox_pkg::gf_mul_byte(m1_a, x0_s3) ^ r09 ^ r11) ^
               (masked_sbox_pkg::gf_mul_byte(m1_b, x0_s3) ^ r12 ^ r14) ^
               (masked_sbox_pkg::gf_mul_byte(m1_c, x0_s3) ^ r15 ^ r17));
      m2_b <= ((masked_sbox_pkg::gf_mul_byte(m1_a, x1_s3) ^ r09 ^ r10) ^
               (masked_sbox_pkg::gf_mul_byte(m1_b, x1_s3) ^ r12 ^ r13) ^
               (masked_sbox_pkg::gf_mul_byte(m1_c, x1_s3) ^ r15 ^ r16));
      m2_c <= ((masked_sbox_pkg::gf_mul_byte(m1_a, x2_s3) ^ r10 ^ r11) ^
               (masked_sbox_pkg::gf_mul_byte(m1_b, x2_s3) ^ r13 ^ r14) ^
               (masked_sbox_pkg::gf_mul_byte(m1_c, x2_s3) ^ r16 ^ r17));
    end
  end

  // STAGE 4: m2 * x^16 -> x^30
  reg [7:0] m3_a, m3_b, m3_c;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      m3_a <= 8'h00; m3_b <= 8'h00; m3_c <= 8'h00;
    end else if (v4) begin
      m3_a <= ((masked_sbox_pkg::gf_mul_byte(m2_a, x0_s4) ^ r18 ^ r20) ^
               (masked_sbox_pkg::gf_mul_byte(m2_b, x0_s4) ^ r21 ^ r23) ^
               (masked_sbox_pkg::gf_mul_byte(m2_c, x0_s4) ^ r24 ^ r26));
      m3_b <= ((masked_sbox_pkg::gf_mul_byte(m2_a, x1_s4) ^ r18 ^ r19) ^
               (masked_sbox_pkg::gf_mul_byte(m2_b, x1_s4) ^ r21 ^ r22) ^
               (masked_sbox_pkg::gf_mul_byte(m2_c, x1_s4) ^ r24 ^ r25));
      m3_c <= ((masked_sbox_pkg::gf_mul_byte(m2_a, x2_s4) ^ r19 ^ r20) ^
               (masked_sbox_pkg::gf_mul_byte(m2_b, x2_s4) ^ r22 ^ r23) ^
               (masked_sbox_pkg::gf_mul_byte(m2_c, x2_s4) ^ r25 ^ r26));
    end
  end

  // STAGE 5: m3 * x^32 -> x^62
  reg [7:0] m4_a, m4_b, m4_c;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      m4_a <= 8'h00; m4_b <= 8'h00; m4_c <= 8'h00;
    end else if (v5) begin
      m4_a <= ((masked_sbox_pkg::gf_mul_byte(m3_a, x0_s5) ^ r27 ^ r29) ^
               (masked_sbox_pkg::gf_mul_byte(m3_b, x0_s5) ^ r30 ^ r32) ^
               (masked_sbox_pkg::gf_mul_byte(m3_c, x0_s5) ^ r33 ^ r35));
      m4_b <= ((masked_sbox_pkg::gf_mul_byte(m3_a, x1_s5) ^ r27 ^ r28) ^
               (masked_sbox_pkg::gf_mul_byte(m3_b, x1_s5) ^ r30 ^ r31) ^
               (masked_sbox_pkg::gf_mul_byte(m3_c, x1_s5) ^ r33 ^ r34));
      m4_c <= ((masked_sbox_pkg::gf_mul_byte(m3_a, x2_s5) ^ r28 ^ r29) ^
               (masked_sbox_pkg::gf_mul_byte(m3_b, x2_s5) ^ r31 ^ r32) ^
               (masked_sbox_pkg::gf_mul_byte(m3_c, x2_s5) ^ r34 ^ r35));
    end
  end

  // STAGE 6: m4 * x^64 -> x^126
  reg [7:0] m5_a, m5_b, m5_c;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      m5_a <= 8'h00; m5_b <= 8'h00; m5_c <= 8'h00;
    end else if (v6) begin
      m5_a <= ((masked_sbox_pkg::gf_mul_byte(m4_a, x0_s6) ^ r36 ^ r38) ^
               (masked_sbox_pkg::gf_mul_byte(m4_b, x0_s6) ^ r39 ^ r41) ^
               (masked_sbox_pkg::gf_mul_byte(m4_c, x0_s6) ^ r42 ^ r44));
      m5_b <= ((masked_sbox_pkg::gf_mul_byte(m4_a, x1_s6) ^ r36 ^ r37) ^
               (masked_sbox_pkg::gf_mul_byte(m4_b, x1_s6) ^ r39 ^ r40) ^
               (masked_sbox_pkg::gf_mul_byte(m4_c, x1_s6) ^ r42 ^ r43));
      m5_c <= ((masked_sbox_pkg::gf_mul_byte(m4_a, x2_s6) ^ r37 ^ r38) ^
               (masked_sbox_pkg::gf_mul_byte(m4_b, x2_s6) ^ r40 ^ r41) ^
               (masked_sbox_pkg::gf_mul_byte(m4_c, x2_s6) ^ r43 ^ r44));
    end
  end

  // STAGE 7: m5 * x^128 -> x^254 = x^-1
  reg [7:0] inv0, inv1, inv2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      inv0 <= 8'h00; inv1 <= 8'h00; inv2 <= 8'h00;
    end else if (v7) begin
      inv0 <= ((masked_sbox_pkg::gf_mul_byte(m5_a, x0_s7) ^ r45 ^ r47) ^
               (masked_sbox_pkg::gf_mul_byte(m5_b, x0_s7) ^ r48 ^ r50) ^
               (masked_sbox_pkg::gf_mul_byte(m5_c, x0_s7) ^ r51 ^ r53));
      inv1 <= ((masked_sbox_pkg::gf_mul_byte(m5_a, x1_s7) ^ r45 ^ r46) ^
               (masked_sbox_pkg::gf_mul_byte(m5_b, x1_s7) ^ r48 ^ r49) ^
               (masked_sbox_pkg::gf_mul_byte(m5_c, x1_s7) ^ r51 ^ r52));
      inv2 <= ((masked_sbox_pkg::gf_mul_byte(m5_a, x2_s7) ^ r46 ^ r47) ^
               (masked_sbox_pkg::gf_mul_byte(m5_b, x2_s7) ^ r49 ^ r50) ^
               (masked_sbox_pkg::gf_mul_byte(m5_c, x2_s7) ^ r52 ^ r53));
    end
  end

  // ------------------------------------------------------------------
  // STAGE 8: AES affine (share-wise linear + constant on first share).
  // ------------------------------------------------------------------
  reg [7:0] aff0, aff1, aff2;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      aff0 <= 8'h00; aff1 <= 8'h00; aff2 <= 8'h00;
    end else if (v8) begin
      aff0 <= masked_sbox_pkg::aes_affine_byte(inv0) ^ 8'h63;
      aff1 <= masked_sbox_pkg::aes_affine_byte(inv1);
      aff2 <= masked_sbox_pkg::aes_affine_byte(inv2);
    end
  end

  // ------------------------------------------------------------------
  // STAGE 9: output register.
  // ------------------------------------------------------------------
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      y0_out <= 8'h00; y1_out <= 8'h00; y2_out <= 8'h00;
      valid_out <= 1'b0;
    end else begin
      y0_out <= aff0;
      y1_out <= aff1;
      y2_out <= aff2;
      valid_out <= v9;
    end
  end

endmodule

`endif

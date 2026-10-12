// =====================================================================
// masked_sbox_pkg.v
// Shared package for the masked AES S-box implementations.
//
// Provides:
//   - gf_sq_byte: GF(2^8) squaring (Frobenius, linear over GF(2))
//   - gf_mul_byte: GF(2^8) multiplication (AES polynomial 0x11B)
//   - gf_inv_byte: GF(2^8) multiplicative inverse (via log/exp tables)
//   - aes_affine_byte: AES affine transformation
//
// All operations are *combinational* functions; the mask of the
// secret lives entirely in the caller. This package is the byte-level
// helper that masked_sbox_first_order / masked_sbox_second_order
// instantiate as their non-secure building blocks.
//
// The log/exp tables below are generated against the AES field
// GF(2^8) / (x^8 + x^4 + x^3 + x + 1) (0x11B) with primitive
// generator 0x03. They were produced and validated against the
// reference Python implementation (reference/gf.py). They are
// inlined as case-statement functions because iverilog 13.0 does
// not support unpacked-array declarations inside `package`.
// =====================================================================

`ifndef MASKED_SBOX_PKG_V
`define MASKED_SBOX_PKG_V

package masked_sbox_pkg;

  // ------------------------------------------------------------------
  // gf_exp: returns 0x03^i in GF(2^8), with gf_exp(0) = 1 (i.e. the
  // 255-cycle starts here: gf_exp(0) = gf_exp(255) = 1).
  // ------------------------------------------------------------------
  function [7:0] gf_exp;
    input [7:0] i;
    begin
      case (i)
        8'h00: gf_exp = 8'h01; 8'h01: gf_exp = 8'h03; 8'h02: gf_exp = 8'h05;
        8'h03: gf_exp = 8'h0F; 8'h04: gf_exp = 8'h11; 8'h05: gf_exp = 8'h33;
        8'h06: gf_exp = 8'h55; 8'h07: gf_exp = 8'hFF; 8'h08: gf_exp = 8'h1A;
        8'h09: gf_exp = 8'h2E; 8'h0A: gf_exp = 8'h72; 8'h0B: gf_exp = 8'h96;
        8'h0C: gf_exp = 8'hA1; 8'h0D: gf_exp = 8'hF8; 8'h0E: gf_exp = 8'h13;
        8'h0F: gf_exp = 8'h35; 8'h10: gf_exp = 8'h5F; 8'h11: gf_exp = 8'hE1;
        8'h12: gf_exp = 8'h38; 8'h13: gf_exp = 8'h48; 8'h14: gf_exp = 8'hD8;
        8'h15: gf_exp = 8'h73; 8'h16: gf_exp = 8'h95; 8'h17: gf_exp = 8'hA4;
        8'h18: gf_exp = 8'hF7; 8'h19: gf_exp = 8'h02; 8'h1A: gf_exp = 8'h06;
        8'h1B: gf_exp = 8'h0A; 8'h1C: gf_exp = 8'h1E; 8'h1D: gf_exp = 8'h22;
        8'h1E: gf_exp = 8'h66; 8'h1F: gf_exp = 8'hAA; 8'h20: gf_exp = 8'hE5;
        8'h21: gf_exp = 8'h34; 8'h22: gf_exp = 8'h5C; 8'h23: gf_exp = 8'hE4;
        8'h24: gf_exp = 8'h37; 8'h25: gf_exp = 8'h59; 8'h26: gf_exp = 8'hEB;
        8'h27: gf_exp = 8'h26; 8'h28: gf_exp = 8'h6A; 8'h29: gf_exp = 8'hBE;
        8'h2A: gf_exp = 8'hD9; 8'h2B: gf_exp = 8'h70; 8'h2C: gf_exp = 8'h90;
        8'h2D: gf_exp = 8'hAB; 8'h2E: gf_exp = 8'hE6; 8'h2F: gf_exp = 8'h31;
        8'h30: gf_exp = 8'h53; 8'h31: gf_exp = 8'hF5; 8'h32: gf_exp = 8'h04;
        8'h33: gf_exp = 8'h0C; 8'h34: gf_exp = 8'h14; 8'h35: gf_exp = 8'h3C;
        8'h36: gf_exp = 8'h44; 8'h37: gf_exp = 8'hCC; 8'h38: gf_exp = 8'h4F;
        8'h39: gf_exp = 8'hD1; 8'h3A: gf_exp = 8'h68; 8'h3B: gf_exp = 8'hB8;
        8'h3C: gf_exp = 8'hD3; 8'h3D: gf_exp = 8'h6E; 8'h3E: gf_exp = 8'hB2;
        8'h3F: gf_exp = 8'hCD; 8'h40: gf_exp = 8'h4C; 8'h41: gf_exp = 8'hD4;
        8'h42: gf_exp = 8'h67; 8'h43: gf_exp = 8'hA9; 8'h44: gf_exp = 8'hE0;
        8'h45: gf_exp = 8'h3B; 8'h46: gf_exp = 8'h4D; 8'h47: gf_exp = 8'hD7;
        8'h48: gf_exp = 8'h62; 8'h49: gf_exp = 8'hA6; 8'h4A: gf_exp = 8'hF1;
        8'h4B: gf_exp = 8'h08; 8'h4C: gf_exp = 8'h18; 8'h4D: gf_exp = 8'h28;
        8'h4E: gf_exp = 8'h78; 8'h4F: gf_exp = 8'h88; 8'h50: gf_exp = 8'h83;
        8'h51: gf_exp = 8'h9E; 8'h52: gf_exp = 8'hB9; 8'h53: gf_exp = 8'hD0;
        8'h54: gf_exp = 8'h6B; 8'h55: gf_exp = 8'hBD; 8'h56: gf_exp = 8'hDC;
        8'h57: gf_exp = 8'h7F; 8'h58: gf_exp = 8'h81; 8'h59: gf_exp = 8'h98;
        8'h5A: gf_exp = 8'hB3; 8'h5B: gf_exp = 8'hCE; 8'h5C: gf_exp = 8'h49;
        8'h5D: gf_exp = 8'hDB; 8'h5E: gf_exp = 8'h76; 8'h5F: gf_exp = 8'h9A;
        8'h60: gf_exp = 8'hB5; 8'h61: gf_exp = 8'hC4; 8'h62: gf_exp = 8'h57;
        8'h63: gf_exp = 8'hF9; 8'h64: gf_exp = 8'h10; 8'h65: gf_exp = 8'h30;
        8'h66: gf_exp = 8'h50; 8'h67: gf_exp = 8'hF0; 8'h68: gf_exp = 8'h0B;
        8'h69: gf_exp = 8'h1D; 8'h6A: gf_exp = 8'h27; 8'h6B: gf_exp = 8'h69;
        8'h6C: gf_exp = 8'hBB; 8'h6D: gf_exp = 8'hD6; 8'h6E: gf_exp = 8'h61;
        8'h6F: gf_exp = 8'hA3; 8'h70: gf_exp = 8'hFE; 8'h71: gf_exp = 8'h19;
        8'h72: gf_exp = 8'h2B; 8'h73: gf_exp = 8'h7D; 8'h74: gf_exp = 8'h87;
        8'h75: gf_exp = 8'h92; 8'h76: gf_exp = 8'hAD; 8'h77: gf_exp = 8'hEC;
        8'h78: gf_exp = 8'h2F; 8'h79: gf_exp = 8'h71; 8'h7A: gf_exp = 8'h93;
        8'h7B: gf_exp = 8'hAE; 8'h7C: gf_exp = 8'hE9; 8'h7D: gf_exp = 8'h20;
        8'h7E: gf_exp = 8'h60; 8'h7F: gf_exp = 8'hA0; 8'h80: gf_exp = 8'hFB;
        8'h81: gf_exp = 8'h16; 8'h82: gf_exp = 8'h3A; 8'h83: gf_exp = 8'h4E;
        8'h84: gf_exp = 8'hD2; 8'h85: gf_exp = 8'h6D; 8'h86: gf_exp = 8'hB7;
        8'h87: gf_exp = 8'hC2; 8'h88: gf_exp = 8'h5D; 8'h89: gf_exp = 8'hE7;
        8'h8A: gf_exp = 8'h32; 8'h8B: gf_exp = 8'h56; 8'h8C: gf_exp = 8'hFA;
        8'h8D: gf_exp = 8'h15; 8'h8E: gf_exp = 8'h3F; 8'h8F: gf_exp = 8'h41;
        8'h90: gf_exp = 8'hC3; 8'h91: gf_exp = 8'h5E; 8'h92: gf_exp = 8'hE2;
        8'h93: gf_exp = 8'h3D; 8'h94: gf_exp = 8'h47; 8'h95: gf_exp = 8'hC9;
        8'h96: gf_exp = 8'h40; 8'h97: gf_exp = 8'hC0; 8'h98: gf_exp = 8'h5B;
        8'h99: gf_exp = 8'hED; 8'h9A: gf_exp = 8'h2C; 8'h9B: gf_exp = 8'h74;
        8'h9C: gf_exp = 8'h9C; 8'h9D: gf_exp = 8'hBF; 8'h9E: gf_exp = 8'hDA;
        8'h9F: gf_exp = 8'h75; 8'hA0: gf_exp = 8'h9F; 8'hA1: gf_exp = 8'hBA;
        8'hA2: gf_exp = 8'hD5; 8'hA3: gf_exp = 8'h64; 8'hA4: gf_exp = 8'hAC;
        8'hA5: gf_exp = 8'hEF; 8'hA6: gf_exp = 8'h2A; 8'hA7: gf_exp = 8'h7E;
        8'hA8: gf_exp = 8'h82; 8'hA9: gf_exp = 8'h9D; 8'hAA: gf_exp = 8'hBC;
        8'hAB: gf_exp = 8'hDF; 8'hAC: gf_exp = 8'h7A; 8'hAD: gf_exp = 8'h8E;
        8'hAE: gf_exp = 8'h89; 8'hAF: gf_exp = 8'h80; 8'hB0: gf_exp = 8'h9B;
        8'hB1: gf_exp = 8'hB6; 8'hB2: gf_exp = 8'hC1; 8'hB3: gf_exp = 8'h58;
        8'hB4: gf_exp = 8'hE8; 8'hB5: gf_exp = 8'h23; 8'hB6: gf_exp = 8'h65;
        8'hB7: gf_exp = 8'hAF; 8'hB8: gf_exp = 8'hEA; 8'hB9: gf_exp = 8'h25;
        8'hBA: gf_exp = 8'h6F; 8'hBB: gf_exp = 8'hB1; 8'hBC: gf_exp = 8'hC8;
        8'hBD: gf_exp = 8'h43; 8'hBE: gf_exp = 8'hC5; 8'hBF: gf_exp = 8'h54;
        8'hC0: gf_exp = 8'hFC; 8'hC1: gf_exp = 8'h1F; 8'hC2: gf_exp = 8'h21;
        8'hC3: gf_exp = 8'h63; 8'hC4: gf_exp = 8'hA5; 8'hC5: gf_exp = 8'hF4;
        8'hC6: gf_exp = 8'h07; 8'hC7: gf_exp = 8'h09; 8'hC8: gf_exp = 8'h1B;
        8'hC9: gf_exp = 8'h2D; 8'hCA: gf_exp = 8'h77; 8'hCB: gf_exp = 8'h99;
        8'hCC: gf_exp = 8'hB0; 8'hCD: gf_exp = 8'hCB; 8'hCE: gf_exp = 8'h46;
        8'hCF: gf_exp = 8'hCA; 8'hD0: gf_exp = 8'h45; 8'hD1: gf_exp = 8'hCF;
        8'hD2: gf_exp = 8'h4A; 8'hD3: gf_exp = 8'hDE; 8'hD4: gf_exp = 8'h79;
        8'hD5: gf_exp = 8'h8B; 8'hD6: gf_exp = 8'h86; 8'hD7: gf_exp = 8'h91;
        8'hD8: gf_exp = 8'hA8; 8'hD9: gf_exp = 8'hE3; 8'hDA: gf_exp = 8'h3E;
        8'hDB: gf_exp = 8'h42; 8'hDC: gf_exp = 8'hC6; 8'hDD: gf_exp = 8'h51;
        8'hDE: gf_exp = 8'hF3; 8'hDF: gf_exp = 8'h0E; 8'hE0: gf_exp = 8'h12;
        8'hE1: gf_exp = 8'h36; 8'hE2: gf_exp = 8'h5A; 8'hE3: gf_exp = 8'hEE;
        8'hE4: gf_exp = 8'h29; 8'hE5: gf_exp = 8'h7B; 8'hE6: gf_exp = 8'h8D;
        8'hE7: gf_exp = 8'h8C; 8'hE8: gf_exp = 8'h8F; 8'hE9: gf_exp = 8'h8A;
        8'hEA: gf_exp = 8'h85; 8'hEB: gf_exp = 8'h94; 8'hEC: gf_exp = 8'hA7;
        8'hED: gf_exp = 8'hF2; 8'hEE: gf_exp = 8'h0D; 8'hEF: gf_exp = 8'h17;
        8'hF0: gf_exp = 8'h39; 8'hF1: gf_exp = 8'h4B; 8'hF2: gf_exp = 8'hDD;
        8'hF3: gf_exp = 8'h7C; 8'hF4: gf_exp = 8'h84; 8'hF5: gf_exp = 8'h97;
        8'hF6: gf_exp = 8'hA2; 8'hF7: gf_exp = 8'hFD; 8'hF8: gf_exp = 8'h1C;
        8'hF9: gf_exp = 8'h24; 8'hFA: gf_exp = 8'h6C; 8'hFB: gf_exp = 8'hB4;
        8'hFC: gf_exp = 8'hC7; 8'hFD: gf_exp = 8'h52; 8'hFE: gf_exp = 8'hF6;
        8'hFF: gf_exp = 8'h01;
      endcase
    end
  endfunction

  // ------------------------------------------------------------------
  // gf_log: discrete log base 0x03 in GF(2^8). Defined for a != 0.
  // Callers must guard against a == 0.
  // ------------------------------------------------------------------
  function [7:0] gf_log;
    input [7:0] a;
    begin
      case (a)
        8'h01: gf_log = 8'h00; 8'h02: gf_log = 8'h19; 8'h03: gf_log = 8'h01;
        8'h04: gf_log = 8'h32; 8'h05: gf_log = 8'h02; 8'h06: gf_log = 8'h1A;
        8'h07: gf_log = 8'hC6; 8'h08: gf_log = 8'h4B; 8'h09: gf_log = 8'hC7;
        8'h0A: gf_log = 8'h1B; 8'h0B: gf_log = 8'h68; 8'h0C: gf_log = 8'h33;
        8'h0D: gf_log = 8'hEE; 8'h0E: gf_log = 8'hDF; 8'h0F: gf_log = 8'h03;
        8'h10: gf_log = 8'h64; 8'h11: gf_log = 8'h04; 8'h12: gf_log = 8'hE0;
        8'h13: gf_log = 8'h0E; 8'h14: gf_log = 8'h34; 8'h15: gf_log = 8'h8D;
        8'h16: gf_log = 8'h81; 8'h17: gf_log = 8'hEF; 8'h18: gf_log = 8'h4C;
        8'h19: gf_log = 8'h71; 8'h1A: gf_log = 8'h08; 8'h1B: gf_log = 8'hC8;
        8'h1C: gf_log = 8'hF8; 8'h1D: gf_log = 8'h69; 8'h1E: gf_log = 8'h1C;
        8'h1F: gf_log = 8'hC1; 8'h20: gf_log = 8'h7D; 8'h21: gf_log = 8'hC2;
        8'h22: gf_log = 8'h1D; 8'h23: gf_log = 8'hB5; 8'h24: gf_log = 8'hF9;
        8'h25: gf_log = 8'hB9; 8'h26: gf_log = 8'h27; 8'h27: gf_log = 8'h6A;
        8'h28: gf_log = 8'h4D; 8'h29: gf_log = 8'hE4; 8'h2A: gf_log = 8'hA6;
        8'h2B: gf_log = 8'h72; 8'h2C: gf_log = 8'h9A; 8'h2D: gf_log = 8'hC9;
        8'h2E: gf_log = 8'h09; 8'h2F: gf_log = 8'h78; 8'h30: gf_log = 8'h65;
        8'h31: gf_log = 8'h2F; 8'h32: gf_log = 8'h8A; 8'h33: gf_log = 8'h05;
        8'h34: gf_log = 8'h21; 8'h35: gf_log = 8'h0F; 8'h36: gf_log = 8'hE1;
        8'h37: gf_log = 8'h24; 8'h38: gf_log = 8'h12; 8'h39: gf_log = 8'hF0;
        8'h3A: gf_log = 8'h82; 8'h3B: gf_log = 8'h45; 8'h3C: gf_log = 8'h35;
        8'h3D: gf_log = 8'h93; 8'h3E: gf_log = 8'hDA; 8'h3F: gf_log = 8'h8E;
        8'h40: gf_log = 8'h96; 8'h41: gf_log = 8'h8F; 8'h42: gf_log = 8'hDB;
        8'h43: gf_log = 8'hBD; 8'h44: gf_log = 8'h36; 8'h45: gf_log = 8'hD0;
        8'h46: gf_log = 8'hCE; 8'h47: gf_log = 8'h94; 8'h48: gf_log = 8'h13;
        8'h49: gf_log = 8'h5C; 8'h4A: gf_log = 8'hD2; 8'h4B: gf_log = 8'hF1;
        8'h4C: gf_log = 8'h40; 8'h4D: gf_log = 8'h46; 8'h4E: gf_log = 8'h83;
        8'h4F: gf_log = 8'h38; 8'h50: gf_log = 8'h66; 8'h51: gf_log = 8'hDD;
        8'h52: gf_log = 8'hFD; 8'h53: gf_log = 8'h30; 8'h54: gf_log = 8'hBF;
        8'h55: gf_log = 8'h06; 8'h56: gf_log = 8'h8B; 8'h57: gf_log = 8'h62;
        8'h58: gf_log = 8'hB3; 8'h59: gf_log = 8'h25; 8'h5A: gf_log = 8'hE2;
        8'h5B: gf_log = 8'h98; 8'h5C: gf_log = 8'h22; 8'h5D: gf_log = 8'h88;
        8'h5E: gf_log = 8'h91; 8'h5F: gf_log = 8'h10; 8'h60: gf_log = 8'h7E;
        8'h61: gf_log = 8'h6E; 8'h62: gf_log = 8'h48; 8'h63: gf_log = 8'hC3;
        8'h64: gf_log = 8'hA3; 8'h65: gf_log = 8'hB6; 8'h66: gf_log = 8'h1E;
        8'h67: gf_log = 8'h42; 8'h68: gf_log = 8'h3A; 8'h69: gf_log = 8'h6B;
        8'h6A: gf_log = 8'h28; 8'h6B: gf_log = 8'h54; 8'h6C: gf_log = 8'hFA;
        8'h6D: gf_log = 8'h85; 8'h6E: gf_log = 8'h3D; 8'h6F: gf_log = 8'hBA;
        8'h70: gf_log = 8'h2B; 8'h71: gf_log = 8'h79; 8'h72: gf_log = 8'h0A;
        8'h73: gf_log = 8'h15; 8'h74: gf_log = 8'h9B; 8'h75: gf_log = 8'h9F;
        8'h76: gf_log = 8'h5E; 8'h77: gf_log = 8'hCA; 8'h78: gf_log = 8'h4E;
        8'h79: gf_log = 8'hD4; 8'h7A: gf_log = 8'hAC; 8'h7B: gf_log = 8'hE5;
        8'h7C: gf_log = 8'hF3; 8'h7D: gf_log = 8'h73; 8'h7E: gf_log = 8'hA7;
        8'h7F: gf_log = 8'h57; 8'h80: gf_log = 8'hAF; 8'h81: gf_log = 8'h58;
        8'h82: gf_log = 8'hA8; 8'h83: gf_log = 8'h50; 8'h84: gf_log = 8'hF4;
        8'h85: gf_log = 8'hEA; 8'h86: gf_log = 8'hD6; 8'h87: gf_log = 8'h74;
        8'h88: gf_log = 8'h4F; 8'h89: gf_log = 8'hAE; 8'h8A: gf_log = 8'hE9;
        8'h8B: gf_log = 8'hD5; 8'h8C: gf_log = 8'hE7; 8'h8D: gf_log = 8'hE6;
        8'h8E: gf_log = 8'hAD; 8'h8F: gf_log = 8'hE8; 8'h90: gf_log = 8'h2C;
        8'h91: gf_log = 8'hD7; 8'h92: gf_log = 8'h75; 8'h93: gf_log = 8'h7A;
        8'h94: gf_log = 8'hEB; 8'h95: gf_log = 8'h16; 8'h96: gf_log = 8'h0B;
        8'h97: gf_log = 8'hF5; 8'h98: gf_log = 8'h59; 8'h99: gf_log = 8'hCB;
        8'h9A: gf_log = 8'h5F; 8'h9B: gf_log = 8'hB0; 8'h9C: gf_log = 8'h9C;
        8'h9D: gf_log = 8'hA9; 8'h9E: gf_log = 8'h51; 8'h9F: gf_log = 8'hA0;
        8'hA0: gf_log = 8'h7F; 8'hA1: gf_log = 8'h0C; 8'hA2: gf_log = 8'hF6;
        8'hA3: gf_log = 8'h6F; 8'hA4: gf_log = 8'h17; 8'hA5: gf_log = 8'hC4;
        8'hA6: gf_log = 8'h49; 8'hA7: gf_log = 8'hEC; 8'hA8: gf_log = 8'hD8;
        8'hA9: gf_log = 8'h43; 8'hAA: gf_log = 8'h1F; 8'hAB: gf_log = 8'h2D;
        8'hAC: gf_log = 8'hA4; 8'hAD: gf_log = 8'h76; 8'hAE: gf_log = 8'h7B;
        8'hAF: gf_log = 8'hB7; 8'hB0: gf_log = 8'hCC; 8'hB1: gf_log = 8'hBB;
        8'hB2: gf_log = 8'h3E; 8'hB3: gf_log = 8'h5A; 8'hB4: gf_log = 8'hFB;
        8'hB5: gf_log = 8'h60; 8'hB6: gf_log = 8'hB1; 8'hB7: gf_log = 8'h86;
        8'hB8: gf_log = 8'h3B; 8'hB9: gf_log = 8'h52; 8'hBA: gf_log = 8'hA1;
        8'hBB: gf_log = 8'h6C; 8'hBC: gf_log = 8'hAA; 8'hBD: gf_log = 8'h55;
        8'hBE: gf_log = 8'h29; 8'hBF: gf_log = 8'h9D; 8'hC0: gf_log = 8'h97;
        8'hC1: gf_log = 8'hB2; 8'hC2: gf_log = 8'h87; 8'hC3: gf_log = 8'h90;
        8'hC4: gf_log = 8'h61; 8'hC5: gf_log = 8'hBE; 8'hC6: gf_log = 8'hDC;
        8'hC7: gf_log = 8'hFC; 8'hC8: gf_log = 8'hBC; 8'hC9: gf_log = 8'h95;
        8'hCA: gf_log = 8'hCF; 8'hCB: gf_log = 8'hCD; 8'hCC: gf_log = 8'h37;
        8'hCD: gf_log = 8'h3F; 8'hCE: gf_log = 8'h5B; 8'hCF: gf_log = 8'hD1;
        8'hD0: gf_log = 8'h53; 8'hD1: gf_log = 8'h39; 8'hD2: gf_log = 8'h84;
        8'hD3: gf_log = 8'h3C; 8'hD4: gf_log = 8'h41; 8'hD5: gf_log = 8'hA2;
        8'hD6: gf_log = 8'h6D; 8'hD7: gf_log = 8'h47; 8'hD8: gf_log = 8'h14;
        8'hD9: gf_log = 8'h2A; 8'hDA: gf_log = 8'h9E; 8'hDB: gf_log = 8'h5D;
        8'hDC: gf_log = 8'h56; 8'hDD: gf_log = 8'hF2; 8'hDE: gf_log = 8'hD3;
        8'hDF: gf_log = 8'hAB; 8'hE0: gf_log = 8'h44; 8'hE1: gf_log = 8'h11;
        8'hE2: gf_log = 8'h92; 8'hE3: gf_log = 8'hD9; 8'hE4: gf_log = 8'h23;
        8'hE5: gf_log = 8'h20; 8'hE6: gf_log = 8'h2E; 8'hE7: gf_log = 8'h89;
        8'hE8: gf_log = 8'hB4; 8'hE9: gf_log = 8'h7C; 8'hEA: gf_log = 8'hB8;
        8'hEB: gf_log = 8'h26; 8'hEC: gf_log = 8'h77; 8'hED: gf_log = 8'h99;
        8'hEE: gf_log = 8'hE3; 8'hEF: gf_log = 8'hA5; 8'hF0: gf_log = 8'h67;
        8'hF1: gf_log = 8'h4A; 8'hF2: gf_log = 8'hED; 8'hF3: gf_log = 8'hDE;
        8'hF4: gf_log = 8'hC5; 8'hF5: gf_log = 8'h31; 8'hF6: gf_log = 8'hFE;
        8'hF7: gf_log = 8'h18; 8'hF8: gf_log = 8'h0D; 8'hF9: gf_log = 8'h63;
        8'hFA: gf_log = 8'h8C; 8'hFB: gf_log = 8'h80; 8'hFC: gf_log = 8'hC0;
        8'hFD: gf_log = 8'hF7; 8'hFE: gf_log = 8'h70; 8'hFF: gf_log = 8'h07;
        default: gf_log = 8'h00;  // a == 0; callers must guard
      endcase
    end
  endfunction

  // ------------------------------------------------------------------
  // gf_mul_byte: GF(2^8) multiplication.
  // The product index is (log_a + log_b) mod 255. We compute it with
  // an explicit subtract-255-if-overflow to avoid iverilog's default
  // 8-bit wrap-around (which would treat 256 as 0 instead of 1).
  // Note: the intermediate sum MUST be wider than 8 bits, since
  // log_a + log_b can reach 254+254=508 (9 bits).
  // ------------------------------------------------------------------
  function [7:0] gf_mul_byte;
    input [7:0] a;
    input [7:0] b;
    reg [8:0] s;
    reg [7:0] r;
    begin
      r = 8'h00;
      if ((a == 8'h00) || (b == 8'h00))
        r = 8'h00;
      else begin
        s = {1'b0, gf_log(a)} + {1'b0, gf_log(b)};
        if (s >= 9'd255)
          s = s - 9'd255;
        r = gf_exp(s[7:0]);
      end
      gf_mul_byte = r;
    end
  endfunction

  // ------------------------------------------------------------------
  // gf_sq_byte: GF(2^8) squaring (Frobenius, linear over GF(2)).
  // The square index is 2 * log(a) mod 255, with the same wrap fix.
  // Note: the intermediate MUST be wider than 8 bits, since
  // 2 * log(a) can reach 2*254 = 508 (9 bits).
  // ------------------------------------------------------------------
  function [7:0] gf_sq_byte;
    input [7:0] a;
    reg [8:0] s;
    reg [7:0] r;
    begin
      r = 8'h00;
      if (a == 8'h00)
        r = 8'h00;
      else begin
        s = {1'b0, gf_log(a)} << 1;
        if (s >= 9'd255)
          s = s - 9'd255;
        r = gf_exp(s[7:0]);
      end
      gf_sq_byte = r;
    end
  endfunction

  // ------------------------------------------------------------------
  // gf_inv_byte: GF(2^8) multiplicative inverse (a == 0 -> 0).
  //   inv(a) = exp((255 - log(a)) mod 255) = exp(-log(a) mod 255).
  // The constant 255 is special: log is undefined at 0 and the
  // multiplicative group has order 255.
  // ------------------------------------------------------------------
  function [7:0] gf_inv_byte;
    input [7:0] a;
    reg [8:0] idx;
    reg [7:0] r;
    begin
      r = 8'h00;
      if (a != 8'h00) begin
        // 255 - log(a) gives a value in [1, 255]; we then take mod 255
        // to bring it into [0, 254] and pass it to gf_exp.
        idx = 9'd255 - {1'b0, gf_log(a)};
        if (idx == 9'd255)
          idx = 9'd0;
        r = gf_exp(idx[7:0]);
      end
      gf_inv_byte = r;
    end
  endfunction

  // ------------------------------------------------------------------
  // aes_affine_byte: AES affine transformation (FIPS-197 §5.1.1).
  //   y = A * x XOR 0x63, where A is the standard 8x8 GF(2) matrix.
  //
  // FIPS-197 §5.1.1, the affine map A is "diagonal + 4 right cyclic
  // shifts": for each output bit r, the row of A has ones on the
  // diagonal (input bit r) and on input bits (r+4) mod 8,
  // (r+5) mod 8, (r+6) mod 8, (r+7) mod 8. The constant 0x63
  // (= 0b01100011) is added to the result.
  //
  // i.e. y_r = x_r ^ x_{(r+4) mod 8} ^ x_{(r+5) mod 8}
  //              ^ x_{(r+6) mod 8} ^ x_{(r+7) mod 8}.
  //
  // The constant 0x63 is added *outside* this function so the caller
  // can place it on a chosen share (preserving the secret).
  // ------------------------------------------------------------------
  function [7:0] aes_affine_byte;
    input [7:0] x;
    reg [7:0] y;
    integer r;
    begin
      y = 8'h00;
      for (r = 0; r < 8; r = r + 1) begin
        y[r] = x[r] ^ x[(r + 4) % 8] ^ x[(r + 5) % 8]
                    ^ x[(r + 6) % 8] ^ x[(r + 7) % 8];
      end
      aes_affine_byte = y;
    end
  endfunction

endpackage

`endif

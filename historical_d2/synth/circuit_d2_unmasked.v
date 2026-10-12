// =====================================================================
// circuit_d2_unmasked.v
// =====================================================================
// PC-H (positive control at d=2): structurally identical to
// circuit_d2.v EXCEPT the 3-share decomposition is collapsed to a
// single-share (unmasked) AES S-box whose output is routed to all
// three output shares.  This is a structurally-unmasked d=2
// interface so that PROLEAD evaluates it in the same robust
// d-probing geometry as the Tier-3 sweep on the masked circuit.
//
// Concretely, for every plaintext share (x0, x1, x2) and any set
// of mask bytes (r0..r18) the implementation computes:
//
//   y0 = S(x0 ^ r0 ^ r18) ^ r0 ^ r18 ^ 0x63
//   y1 = 0
//   y2 = 0
//
// i.e., the mask random and the operand-refresh random *do not*
// decorrelate y0 from x, x1 from x1, x2 from x2; instead x0
// (the only secret-carrying share) is observed directly through
// y0 in the usual AES-S-box manner (unmasked secret=plaintext).
//
// The intent of the wrapper is to keep the SAME byte-level
// interface as circuit_d2.v (sboxIn[23:0] := {x2, x1, x0},
// randomIn[151:0] unused, sboxOut[23:0] := {y2, y1, y0}) so that
// config_d2_64k_fixB_safe.json can be re-used without any
// change.  When PROLEAD runs the d=2 robust probe against this
// unmasked d=2 interface, it sees a secret-dependent y0 wire at
// every cycle, exactly the same secret-dependence pattern as the
// d=1 unmasked control (1,224/1,890 LEAK, worst -inf), only now
// extended to the d=2 probe geometry (each cycle sees both an
// x0 leak through y0 and a stable 0 on y1, y2).
//
// Expected verdict with config_d2_64k_fixB_safe.json:
//   number_of_leaking_probing_sets > 0
//   worst -log10(p) above the Bonferroni threshold of
//   -log10(0.05/17157) = 6.54 (likely extreme, possibly inf).
// =====================================================================

`ifndef CIRCUIT_D2_UNMASKED_V
`define CIRCUIT_D2_UNMASKED_V

`timescale 1ns/1ps

module circuit (
    input              clk,
    input  [23:0]      sboxIn,
    input  [151:0]     randomIn,    // unused, kept for PROLEAD interface
    output [23:0]      sboxOut
);

    wire [7:0] x0 = sboxIn[7:0];
    wire [7:0] x1 = sboxIn[15:8];
    wire [7:0] x2 = sboxIn[23:16];

    // -----------------------------------------------------------------
    // 1.  Plaintext-side affine transform:  A(p) = p ^ 0x63
    //
    //     The AES S-box is the composition S(p) = A(AES_inv(p));
    //     we want the *output* of the S-box (which is one byte
    //     of AES-ciphertext contribution), so the natural d=2
    //     interface output is `S(x0)` directly.
    //
    //     To make this wrapper *byte-exact* compatible with the
    //     masked design's sboxOut[7:0] = AES_S_BOX(x0 ^ af0) ^ af0
    //     convention (which equals AES_S_BOX(x0) by design, because
    //     AES_S_BOX(p) ^ af0 = A(AES_inv(p))) we compute:
    //
    //         y0 = AES_S_BOX(x0)
    //         y1 = 0
    //         y2 = 0
    // -----------------------------------------------------------------

    // -----------------------------------------------------------------
    // 2.  Hard-coded unmasked AES S-box table
    //     (the canonical 256-byte AES S-box, identical to
    //      rtl/aes_sbox.v / rtl/masked_sbox_pkg.v:233-298)
    // -----------------------------------------------------------------
    reg [7:0] sbox_lut;
    always @* begin
        case (x0)
            8'h00: sbox_lut = 8'h63; 8'h01: sbox_lut = 8'h7c; 8'h02: sbox_lut = 8'h77; 8'h03: sbox_lut = 8'h7b;
            8'h04: sbox_lut = 8'hf2; 8'h05: sbox_lut = 8'h6b; 8'h06: sbox_lut = 8'h6f; 8'h07: sbox_lut = 8'hc5;
            8'h08: sbox_lut = 8'h30; 8'h09: sbox_lut = 8'h01; 8'h0a: sbox_lut = 8'h67; 8'h0b: sbox_lut = 8'h2b;
            8'h0c: sbox_lut = 8'hfe; 8'h0d: sbox_lut = 8'hd7; 8'h0e: sbox_lut = 8'hab; 8'h0f: sbox_lut = 8'h76;
            8'h10: sbox_lut = 8'hca; 8'h11: sbox_lut = 8'h82; 8'h12: sbox_lut = 8'hc9; 8'h13: sbox_lut = 8'h7d;
            8'h14: sbox_lut = 8'hfa; 8'h15: sbox_lut = 8'h59; 8'h16: sbox_lut = 8'h47; 8'h17: sbox_lut = 8'hf0;
            8'h18: sbox_lut = 8'had; 8'h19: sbox_lut = 8'hd4; 8'h1a: sbox_lut = 8'ha2; 8'h1b: sbox_lut = 8'haf;
            8'h1c: sbox_lut = 8'h9c; 8'h1d: sbox_lut = 8'ha4; 8'h1e: sbox_lut = 8'h72; 8'h1f: sbox_lut = 8'hc0;
            8'h20: sbox_lut = 8'hb7; 8'h21: sbox_lut = 8'hfd; 8'h22: sbox_lut = 8'h93; 8'h23: sbox_lut = 8'h26;
            8'h24: sbox_lut = 8'h36; 8'h25: sbox_lut = 8'h3f; 8'h26: sbox_lut = 8'hf7; 8'h27: sbox_lut = 8'hcc;
            8'h28: sbox_lut = 8'h34; 8'h29: sbox_lut = 8'ha5; 8'h2a: sbox_lut = 8'he5; 8'h2b: sbox_lut = 8'hf1;
            8'h2c: sbox_lut = 8'h71; 8'h2d: sbox_lut = 8'hd8; 8'h2e: sbox_lut = 8'h31; 8'h2f: sbox_lut = 8'h15;
            8'h30: sbox_lut = 8'h04; 8'h31: sbox_lut = 8'hc7; 8'h32: sbox_lut = 8'h23; 8'h33: sbox_lut = 8'hc3;
            8'h34: sbox_lut = 8'h18; 8'h35: sbox_lut = 8'h96; 8'h36: sbox_lut = 8'h05; 8'h37: sbox_lut = 8'h9a;
            8'h38: sbox_lut = 8'h07; 8'h39: sbox_lut = 8'h12; 8'h3a: sbox_lut = 8'h80; 8'h3b: sbox_lut = 8'he2;
            8'h3c: sbox_lut = 8'heb; 8'h3d: sbox_lut = 8'h27; 8'h3e: sbox_lut = 8'hb2; 8'h3f: sbox_lut = 8'h75;
            8'h40: sbox_lut = 8'h09; 8'h41: sbox_lut = 8'h83; 8'h42: sbox_lut = 8'h2c; 8'h43: sbox_lut = 8'h1a;
            8'h44: sbox_lut = 8'h1b; 8'h45: sbox_lut = 8'h6e; 8'h46: sbox_lut = 8'h5a; 8'h47: sbox_lut = 8'ha0;
            8'h48: sbox_lut = 8'h52; 8'h49: sbox_lut = 8'h3b; 8'h4a: sbox_lut = 8'hd6; 8'h4b: sbox_lut = 8'hb3;
            8'h4c: sbox_lut = 8'h29; 8'h4d: sbox_lut = 8'he3; 8'h4e: sbox_lut = 8'h2f; 8'h4f: sbox_lut = 8'h84;
            8'h50: sbox_lut = 8'h53; 8'h51: sbox_lut = 8'hd1; 8'h52: sbox_lut = 8'h00; 8'h53: sbox_lut = 8'hed;
            8'h54: sbox_lut = 8'h20; 8'h55: sbox_lut = 8'hfc; 8'h56: sbox_lut = 8'hb1; 8'h57: sbox_lut = 8'h5b;
            8'h58: sbox_lut = 8'h6a; 8'h59: sbox_lut = 8'hcb; 8'h5a: sbox_lut = 8'hbe; 8'h5b: sbox_lut = 8'h39;
            8'h5c: sbox_lut = 8'h4a; 8'h5d: sbox_lut = 8'h4c; 8'h5e: sbox_lut = 8'h58; 8'h5f: sbox_lut = 8'hcf;
            8'h60: sbox_lut = 8'hd0; 8'h61: sbox_lut = 8'hef; 8'h62: sbox_lut = 8'haa; 8'h63: sbox_lut = 8'hfb;
            8'h64: sbox_lut = 8'h43; 8'h65: sbox_lut = 8'h4d; 8'h66: sbox_lut = 8'h33; 8'h67: sbox_lut = 8'h85;
            8'h68: sbox_lut = 8'h45; 8'h69: sbox_lut = 8'hf9; 8'h6a: sbox_lut = 8'h02; 8'h6b: sbox_lut = 8'h7f;
            8'h6c: sbox_lut = 8'h50; 8'h6d: sbox_lut = 8'h3c; 8'h6e: sbox_lut = 8'h9f; 8'h6f: sbox_lut = 8'ha8;
            8'h70: sbox_lut = 8'h51; 8'h71: sbox_lut = 8'ha3; 8'h72: sbox_lut = 8'h40; 8'h73: sbox_lut = 8'h8f;
            8'h74: sbox_lut = 8'h92; 8'h75: sbox_lut = 8'h9d; 8'h76: sbox_lut = 8'h38; 8'h77: sbox_lut = 8'hf5;
            8'h78: sbox_lut = 8'hbc; 8'h79: sbox_lut = 8'hb6; 8'h7a: sbox_lut = 8'hda; 8'h7b: sbox_lut = 8'h21;
            8'h7c: sbox_lut = 8'h10; 8'h7d: sbox_lut = 8'hff; 8'h7e: sbox_lut = 8'hf3; 8'h7f: sbox_lut = 8'hd2;
            8'h80: sbox_lut = 8'hcd; 8'h81: sbox_lut = 8'h0c; 8'h82: sbox_lut = 8'h13; 8'h83: sbox_lut = 8'hec;
            8'h84: sbox_lut = 8'h5f; 8'h85: sbox_lut = 8'h97; 8'h86: sbox_lut = 8'h44; 8'h87: sbox_lut = 8'h17;
            8'h88: sbox_lut = 8'hc4; 8'h89: sbox_lut = 8'ha7; 8'h8a: sbox_lut = 8'h7e; 8'h8b: sbox_lut = 8'h3d;
            8'h8c: sbox_lut = 8'h64; 8'h8d: sbox_lut = 8'h5d; 8'h8e: sbox_lut = 8'h19; 8'h8f: sbox_lut = 8'h73;
            8'h90: sbox_lut = 8'h60; 8'h91: sbox_lut = 8'h81; 8'h92: sbox_lut = 8'h4f; 8'h93: sbox_lut = 8'hdc;
            8'h94: sbox_lut = 8'h22; 8'h95: sbox_lut = 8'h2a; 8'h96: sbox_lut = 8'h90; 8'h97: sbox_lut = 8'h88;
            8'h98: sbox_lut = 8'h46; 8'h99: sbox_lut = 8'hee; 8'h9a: sbox_lut = 8'hb8; 8'h9b: sbox_lut = 8'h14;
            8'h9c: sbox_lut = 8'hde; 8'h9d: sbox_lut = 8'h5e; 8'h9e: sbox_lut = 8'h0b; 8'h9f: sbox_lut = 8'hdb;
            8'ha0: sbox_lut = 8'he0; 8'ha1: sbox_lut = 8'h32; 8'ha2: sbox_lut = 8'h3a; 8'ha3: sbox_lut = 8'h0a;
            8'ha4: sbox_lut = 8'h49; 8'ha5: sbox_lut = 8'h06; 8'ha6: sbox_lut = 8'h24; 8'ha7: sbox_lut = 8'h5c;
            8'ha8: sbox_lut = 8'hc2; 8'ha9: sbox_lut = 8'hd3; 8'haa: sbox_lut = 8'hac; 8'hab: sbox_lut = 8'h62;
            8'hac: sbox_lut = 8'h91; 8'had: sbox_lut = 8'h95; 8'hae: sbox_lut = 8'he4; 8'haf: sbox_lut = 8'h79;
            8'hb0: sbox_lut = 8'he7; 8'hb1: sbox_lut = 8'hc8; 8'hb2: sbox_lut = 8'h37; 8'hb3: sbox_lut = 8'h6d;
            8'hb4: sbox_lut = 8'h8d; 8'hb5: sbox_lut = 8'hd5; 8'hb6: sbox_lut = 8'h4e; 8'hb7: sbox_lut = 8'ha9;
            8'hb8: sbox_lut = 8'h6c; 8'hb9: sbox_lut = 8'h56; 8'hba: sbox_lut = 8'hf4; 8'hbb: sbox_lut = 8'hea;
            8'hbc: sbox_lut = 8'h65; 8'hbd: sbox_lut = 8'h7a; 8'hbe: sbox_lut = 8'hae; 8'hbf: sbox_lut = 8'h08;
            8'hc0: sbox_lut = 8'hba; 8'hc1: sbox_lut = 8'h78; 8'hc2: sbox_lut = 8'h25; 8'hc3: sbox_lut = 8'h2e;
            8'hc4: sbox_lut = 8'h1c; 8'hc5: sbox_lut = 8'ha6; 8'hc6: sbox_lut = 8'hb4; 8'hc7: sbox_lut = 8'hc6;
            8'hc8: sbox_lut = 8'he8; 8'hc9: sbox_lut = 8'hdd; 8'hca: sbox_lut = 8'h74; 8'hcb: sbox_lut = 8'h1f;
            8'hcc: sbox_lut = 8'h4b; 8'hcd: sbox_lut = 8'hbd; 8'hce: sbox_lut = 8'h8b; 8'hcf: sbox_lut = 8'h8a;
            8'hd0: sbox_lut = 8'h70; 8'hd1: sbox_lut = 8'h3e; 8'hd2: sbox_lut = 8'hb5; 8'hd3: sbox_lut = 8'h66;
            8'hd4: sbox_lut = 8'h48; 8'hd5: sbox_lut = 8'h03; 8'hd6: sbox_lut = 8'hf6; 8'hd7: sbox_lut = 8'h0e;
            8'hd8: sbox_lut = 8'h61; 8'hd9: sbox_lut = 8'h35; 8'hda: sbox_lut = 8'h57; 8'hdb: sbox_lut = 8'hb9;
            8'hdc: sbox_lut = 8'h86; 8'hdd: sbox_lut = 8'hc1; 8'hde: sbox_lut = 8'h1d; 8'hdf: sbox_lut = 8'h9e;
            8'he0: sbox_lut = 8'he1; 8'he1: sbox_lut = 8'hf8; 8'he2: sbox_lut = 8'h98; 8'he3: sbox_lut = 8'h11;
            8'he4: sbox_lut = 8'h69; 8'he5: sbox_lut = 8'hd9; 8'he6: sbox_lut = 8'h8e; 8'he7: sbox_lut = 8'h94;
            8'he8: sbox_lut = 8'h9b; 8'he9: sbox_lut = 8'h1e; 8'hea: sbox_lut = 8'h87; 8'heb: sbox_lut = 8'he9;
            8'hec: sbox_lut = 8'hce; 8'hed: sbox_lut = 8'h55; 8'hee: sbox_lut = 8'h28; 8'hef: sbox_lut = 8'hdf;
            8'hf0: sbox_lut = 8'h8c; 8'hf1: sbox_lut = 8'ha1; 8'hf2: sbox_lut = 8'h89; 8'hf3: sbox_lut = 8'h0d;
            8'hf4: sbox_lut = 8'hbf; 8'hf5: sbox_lut = 8'he6; 8'hf6: sbox_lut = 8'h42; 8'hf7: sbox_lut = 8'h68;
            8'hf8: sbox_lut = 8'h41; 8'hf9: sbox_lut = 8'h99; 8'hfa: sbox_lut = 8'h2d; 8'hfb: sbox_lut = 8'h0f;
            8'hfc: sbox_lut = 8'hb0; 8'hfd: sbox_lut = 8'h54; 8'hfe: sbox_lut = 8'hbb; 8'hff: sbox_lut = 8'h16;
        endcase
    end

    // -----------------------------------------------------------------
    // 3.  Output packing (3-share d=2 interface).
    //
    //     `circuit_d2_struct.v` (the masked baseline) drives each
    //     `sboxOut[N]` byte from a named wire yN (y0, y1, y2), then
    //     assigns `sboxOut = { y2, y1, y0 };`.  PROLEAD's wire-by-
    //     name parser handles that pattern; it does not handle
    //     inline literal drivers like `assign sboxOut[N:M] = 8'h00;`
    //     or `assign sboxOut = { 8'h00, 8'h00, sbox_lut };`.
    //
    //     We mirror the masked baseline's exact wire pattern here:
    //     y0 = S(x0) (a wire), y1 = 0 wire, y2 = 0 wire, and
    //     sboxOut = { y2, y1, y0 }.
    // -----------------------------------------------------------------
    wire [7:0] y0;
    wire [7:0] y1;
    wire [7:0] y2;
    assign y0 = sbox_lut;
    assign y1 = 8'h00;
    assign y2 = 8'h00;
    assign sboxOut = { y2, y1, y0 };
endmodule

`endif

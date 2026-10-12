// =====================================================================
// circuit_unmasked.v
// Unmasked control top for PROLEAD negative-control evaluation.
// Identical port list and stimulus mapping to rtl/circuit.v, but the
// S-box is the plain unmasked pipelined implementation.
//
// sboxOut[7:0]  = S-box output (depends on BOTH input shares -> must leak)
// sboxOut[15:8] = tied to constant 0 through DFFs (structural netlists
//                 may not contain constant assigns; constant DFF inputs
//                 are accepted by the PROLEAD Verilog parser)
// =====================================================================
module circuit_unmasked (
    input  wire        clk,
    input  wire [15:0] sboxIn,
    input  wire [223:0] randomIn,
    output wire [15:0] sboxOut
);

    // Combine the two "shares" to form the actual S-box input.
    wire [7:0] x = sboxIn[7:0] ^ sboxIn[15:8];
    wire [7:0] y;

    unmasked_sbox u_sbox (
        .clk      (clk),
        .rst_n    (1'b1),
        .valid_in (1'b1),
        .x_in     (x),
        .y_out    (y),
        .valid_out()
    );

    assign sboxOut[7:0] = y;

    // Constant-zero upper byte via library DFFs with tied-low inputs.
    // keep=1 prevents constant folding (the parser cannot handle assigns,
    // but constant literal port connections are accepted).
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : g_tie
            (* keep = 1 *) DFF tie_ff (
                .C (clk),
                .D (1'b0),
                .Q (sboxOut[8 + i])
            );
        end
    endgenerate

    // randomIn is intentionally unused in the unmasked control.
    wire _unused = &{1'b0, randomIn};

endmodule

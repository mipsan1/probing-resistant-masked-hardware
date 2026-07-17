#!/usr/bin/env bash
# =====================================================================
# run_prolead_docker.sh
# =====================================================================
# Run PROLEAD-based robust $d$-probing verification on our masked
# AES S-box inside a Docker container (syn/Dockerfile.prolead).
#
# This validates the same probing-security claim as our in-house
# Python PROLEAD-equivalent (`probe/probe_analyzer.py`) using
# PROLEAD's published C++ toolchain.
#
# Usage:
#   docker build -t prolead-masked-aes -f syn/Dockerfile.prolead .
#   docker run --rm -v $(pwd):/work prolead-masked-aes \
#       bash /work/syn/run_prolead_docker.sh
# =====================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Synthesize the gate-level circuit (idempotent; works both in
# the container and on the host if the host has Yosys)
yosys -q syn/synth_circuit.ys

# 1b. Remap `$_SDFF_PN0_` (used by Yosys for our 1st-order
# `always @(posedge clk or negedge rst_n)` flops) to plain
# `$_DFF_P_` so that the design can be matched against our
# custom library.  After `setundef -zero` the reset line is
# tied to `1'b0` and never asserts, so this is conservative.
python3 syn/remap_prolead_cells.py \
    syn/prolead/circuit.v \
    syn/prolead/circuit.v

# 2. Run PROLEAD on the synthesized circuit
mkdir -p sim/prolead
if [ ! -x /opt/PROLEAD/release/PROLEAD ]; then
    echo "ERROR: /opt/PROLEAD/release/PROLEAD not found in container."
    echo "The Dockerfile.prolead build may have failed; check with:"
    echo "  docker run --rm prolead-masked-aes ls /opt/PROLEAD/release"
    exit 1
fi
# Use the custom yosys-primitives library shipped with this
# submission (see syn/prolead/library_yosys.json).  PROLEAD's
# default `nang45` library does not include the `$_AND_` /
# `$_OR_` / `$_XOR_` / `$_NOT_` / `$_MUX_` / `$_DFF_P_` /
# `$_SDFF_PN0_` cell names that Yosys emits after
# `flatten; opt; clean; setundef -zero; write_verilog -noexpr`.
/opt/PROLEAD/release/PROLEAD \
    --designFile syn/prolead/circuit.v \
    --configFile syn/prolead/config.json \
    --outputDirectory sim/prolead \
    --libraryFile syn/prolead/library_yosys.json \
    --libraryName yosys_primitives

# 3. Convert PROLEAD's JSON report to a markdown summary
python3 syn/prolead_report_to_md.py \
    sim/prolead/server_config.json \
    sim/prolead/server_report.txt \
    sim/prolead/prolead_summary.md

echo "[prolead] DONE; report at sim/prolead/prolead_summary.md"

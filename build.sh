#!/usr/bin/env bash
# =====================================================================
# build.sh
# =====================================================================
# One-button reproduction of all synthesis, simulation, and
# post-processing results.  This wraps the individual scripts in
# `syn/` and `rtl/` so a fresh checkout can be turned into a
# full report with a single command.
#
# Usage:
#   bash build.sh                  # do everything
#   bash build.sh sbox             # only S-box sim
#   bash build.sh round1           # only round-1 sim
#   bash build.sh synth            # only synthesis
#   bash build.sh delay            # only critical-path estimate
#   bash build.sh power            # only power-trace dump
#   bash build.sh vcd              # only VCD dump (RTL-level)
#   bash build.sh vcd_gl           # only VCD power-trace (gate-level, with TVLA)
#   bash build.sh prolead          # PROLEAD robust probing via Docker
#   bash build.sh paper            # only the LaTeX paper
#
# All artefacts are written under `sim/` (vectors, traces) and `syn/`
# (gate-level netlists, area report, delay estimate).
# =====================================================================

set -euo pipefail
cd "$(dirname "$0")"

# ---------------------------------------------------------------------
# Sanity: tool checks
# ---------------------------------------------------------------------
need_tool() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "ERROR: $1 is required but not on PATH" >&2
        exit 1
    }
}

# ---------------------------------------------------------------------
# Sub-routines
# ---------------------------------------------------------------------
do_sbox() {
    echo "[build] S-box RTL + gate-level simulation (256 input bytes)"
    need_tool iverilog
    cd rtl
    iverilog -g2012 -I. -o /tmp/sb_sim \
        tb_masked_sbox_exhaustive.v \
        masked_sbox_first_order.v \
        masked_sbox_second_order.v \
        masked_sbox_pkg.v
    vvp /tmp/sb_sim
    cd ..
    iverilog -g2012 -Irtl -o /tmp/sb_gl_sim \
        rtl/tb_masked_sbox_exhaustive_syn.v \
        syn/masked_sbox_first_order_syn.v \
        syn/masked_sbox_second_order_syn.v
    vvp /tmp/sb_gl_sim
}

do_round1() {
    echo "[build] Round-1 RTL + gate-level simulation (100 random vectors)"
    need_tool iverilog
    cd syn
    yosys -s synth_round1.ys
    cd ../rtl
    iverilog -g2012 -I. -o /tmp/r1_sim tb_masked_aes_round1.v \
        masked_sbox_first_order.v masked_sbox_pkg.v masked_aes_round1.v
    vvp /tmp/r1_sim
    iverilog -g2012 -I. -o /tmp/r1_gl_sim tb_masked_aes_round1.v \
        ../syn/masked_aes_round1_syn.v
    vvp /tmp/r1_gl_sim
    cd ..
}

do_synth() {
    echo "[build] Yosys synthesis (per-S-box + full chip)"
    need_tool yosys
    cd syn
    yosys -s synth_round1.ys
    cd ..
    # S-box synthesis scripts
    yosys -p "read_verilog -sv rtl/masked_sbox_pkg.v \
              rtl/masked_sbox_first_order.v \
              rtl/masked_sbox_second_order.v; \
              synth -top masked_sbox_first_order; stat"
    yosys -p "read_verilog -sv rtl/masked_sbox_pkg.v \
              rtl/masked_sbox_first_order.v \
              rtl/masked_sbox_second_order.v; \
              synth -top masked_sbox_second_order; stat"
}

do_delay() {
    echo "[build] Critical-path delay estimate"
    need_tool yosys
    need_tool python3
    yosys -p "read_verilog -sv rtl/masked_sbox_pkg.v \
              rtl/masked_sbox_first_order.v \
              rtl/masked_sbox_second_order.v \
              rtl/masked_aes_round1.v; \
              hierarchy -check -top masked_aes_round1_first_order; \
              flatten; proc; opt; fsm; opt; memory; opt; techmap; opt; clean; \
              write_json syn/masked_aes_round1_flat.json"
    python3 syn/estimate_delay_json.py syn/masked_aes_round1_flat.json \
        | tee syn/delay_report.txt
}

do_power() {
    echo "[build] Power-trace dump (per-cycle, RTL)"
    need_tool iverilog
    need_tool python3
    bash syn/run_power_dump_rtl.sh
}

do_vcd() {
    echo "[build] VCD power-trace pipeline"
    need_tool iverilog
    need_tool python3
    bash syn/run_vcd_dump.sh
}

do_vcd_gl() {
    echo "[build] Gate-level VCD power-trace pipeline (d=1 + d=2, with TVLA)"
    need_tool iverilog
    need_tool yosys
    need_tool python3
    bash syn/run_vcd_dump_gl.sh
}

do_prolead() {
    echo "[build] PROLEAD robust d-probing verification (via Docker)"
    need_tool docker
    need_tool yosys
    need_tool python3
    # Build Docker image if not present
    if ! docker image inspect prolead-masked-aes >/dev/null 2>&1; then
        docker build -t prolead-masked-aes -f syn/Dockerfile.prolead .
    fi
    # Synthesise + remap on the host first so the design is ready
    # when the container starts.  The container only re-runs the
    # synthesis when /work/syn/prolead/circuit.v is missing.
    yosys -q syn/synth_circuit.ys
    python3 syn/remap_prolead_cells.py \
        syn/prolead/circuit.v syn/prolead/circuit.v
    docker run --rm -v "$(pwd)":/work prolead-masked-aes \
        bash /work/syn/run_prolead_docker.sh
}

do_paper() {
    echo "[build] LaTeX paper"
    need_tool pdflatex
    need_tool bibtex
    pdflatex -interaction=nonstopmode manuscript.tex
    bibtex manuscript
    pdflatex -interaction=nonstopmode manuscript.tex
    pdflatex -interaction=nonstopmode manuscript.tex
}

do_all() {
    do_sbox
    do_synth
    do_round1
    do_delay
    do_power
    do_vcd
    do_vcd_gl
    do_prolead
    do_paper
}

# ---------------------------------------------------------------------
# Argument dispatch
# ---------------------------------------------------------------------
target="${1:-all}"
case "$target" in
    all)     do_all ;;
    sbox)    do_sbox ;;
    round1)  do_round1 ;;
    synth)   do_synth ;;
    delay)   do_delay ;;
    power)   do_power ;;
    vcd)     do_vcd ;;
    vcd_gl)  do_vcd_gl ;;
    prolead) do_prolead ;;
    paper)   do_paper ;;
    *)
        echo "usage: $0 {all|sbox|round1|synth|delay|power|vcd|vcd_gl|prolead|paper}" >&2
        exit 1
        ;;
esac

echo "[build] DONE ($target)"

#!/usr/bin/env bash
#
# build_and_run_mode_B.sh -- one-shot PROLEAD mode B execution on
# macOS (Apple Silicon).
#
# Assumes you have already:
#   1. Placed netlist.json in ./design/
#   2. Created modeB_dffs.txt (one DFF instance name per line, 16 total)
#   3. Copied your baseline PROLEAD YAML into design/prolead_config_modeB.yaml
#      and applied the two [MODEB] edits (hdl_files + reports paths).
#
# Usage:
#   chmod +x build_and_run_mode_B.sh
#   ./build_and_run_mode_B.sh          # 128 K sim smoke test (~30-60 min on M3)
#   ./build_and_run_mode_B.sh --full   # 512 K sim final     (~2-4 h on M3)

set -euo pipefail

MODE="${1:-smoke}"
WORK="$(pwd)"
DESIGN="$WORK/design"
RESULTS="$WORK/results"
mkdir -p "$DESIGN" "$RESULTS"

log() { printf "\n\033[1;34m[%s]\033[0m %s\n" "$(date +%H:%M:%S)" "$*"; }

# -------------------------------------------------------------------
# 1. Homebrew deps
# -------------------------------------------------------------------
if ! command -v brew >/dev/null; then
  echo "Homebrew required. Install from https://brew.sh first." >&2; exit 1
fi
for pkg in boost libomp cmake yosys python@3.12; do
  brew list "$pkg" >/dev/null 2>&1 || { log "installing $pkg"; brew install "$pkg"; }
done

# -------------------------------------------------------------------
# 2. Verify inputs
# -------------------------------------------------------------------
[[ -f "$DESIGN/netlist.json"       ]] || { echo "Missing $DESIGN/netlist.json"; exit 2; }
[[ -f "$DESIGN/modeB_dffs.txt"     ]] || { echo "Missing $DESIGN/modeB_dffs.txt"; exit 2; }
[[ -f "$DESIGN/prolead_config_modeB.yaml" ]] || { echo "Missing $DESIGN/prolead_config_modeB.yaml"; exit 2; }

# -------------------------------------------------------------------
# 3. Generate mode B netlist (JSON -> Verilog)
# -------------------------------------------------------------------
log "generating mode B netlist"
python3 make_mode_B_netlist.py \
  --in  "$DESIGN/netlist.json" \
  --out "$DESIGN/netlist_modeB.json" \
  --dff-list "$DESIGN/modeB_dffs.txt"

log "lowering JSON -> Verilog with Yosys"
yosys -q -p "read_json $DESIGN/netlist_modeB.json; write_verilog -noattr $DESIGN/netlist_modeB.v"

# -------------------------------------------------------------------
# 4. Clone + build PROLEAD (idempotent)
# -------------------------------------------------------------------
if [ ! -d "$WORK/PROLEAD" ]; then
  log "cloning PROLEAD"
  git clone https://github.com/ChairImpSec/PROLEAD.git "$WORK/PROLEAD"
fi

OMP_PREFIX="$(brew --prefix libomp)"
BOOST_PREFIX="$(brew --prefix boost)"

if [ ! -x "$WORK/PROLEAD/build/prolead" ]; then
  log "building PROLEAD (clang + OpenMP + Boost)"
  mkdir -p "$WORK/PROLEAD/build"
  cd "$WORK/PROLEAD/build"
  cmake .. \
    -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
    -DCMAKE_C_FLAGS="-Xpreprocessor -fopenmp -I$OMP_PREFIX/include -I$BOOST_PREFIX/include" \
    -DCMAKE_CXX_FLAGS="-Xpreprocessor -fopenmp -I$OMP_PREFIX/include -I$BOOST_PREFIX/include" \
    -DCMAKE_EXE_LINKER_FLAGS="-L$OMP_PREFIX/lib -lomp -L$BOOST_PREFIX/lib"
  make -j"$(sysctl -n hw.ncpu)"
  cd "$WORK"
fi

# -------------------------------------------------------------------
# 5. Optional parameter override for --full
# -------------------------------------------------------------------
CFG="$DESIGN/prolead_config_modeB.yaml"
if [ "$MODE" = "--full" ]; then
  log "switching to 512K simulations"
  sed -i.bak 's/number_of_simulations:.*/number_of_simulations: 524288/' "$CFG"
fi

# -------------------------------------------------------------------
# 6. Run PROLEAD (caffeinate prevents sleep)
# -------------------------------------------------------------------
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$RESULTS/modeB_${MODE#--}_$STAMP.log"
log "launching PROLEAD -> $LOG"
caffeinate -is "$WORK/PROLEAD/build/prolead" --config "$CFG" 2>&1 | tee "$LOG"

# -------------------------------------------------------------------
# 7. One-line verdict summary
# -------------------------------------------------------------------
log "verdict extraction"
grep -Ei 'leaking|probing set|verdict|status' "$LOG" | tail -20
echo
log "finished. Copy $RESULTS/*.log back to your workstation."

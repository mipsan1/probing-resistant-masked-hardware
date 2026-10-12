#!/bin/bash
set -u
ROOT="/Users/ckim/Downloads/IEEE-Transactions-TIFS_0717_hardware_Advanced"
cd "$ROOT" || exit 1

PROLEAD="./PROLEAD/release/PROLEAD"
DESIGN="syn/prolead/circuit_d2_struct.v"
CONFIG="syn/prolead/config_d2_64k_fixB.json"
LIB="syn/prolead/library_yosys.json"
BASE_OUT="sim/prolead_d2_full"
TOTAL_BATCHES=33   # 20% of 163 full batches
LOG="$BASE_OUT/runner.log"

mkdir -p "$BASE_OUT"

if [ -f "$BASE_OUT/COMPLETE" ]; then
  echo "[$(date '+%F %T')] already complete, exiting cleanly" >> "$LOG"
  exit 0
fi

for i in $(seq 0 $((TOTAL_BATCHES-1))); do
  OUT="$BASE_OUT/batch_$i"
  # PROLEAD always writes to <resultfolder>/prolead_<top>_<fault>_<step>_<sims>_leakages.json
  # With our config fault=0, step=0, sims=64000, so filename = prolead_circuit_0_0_64000_leakages.json
  DONEFLAG="$OUT/prolead_circuit_0_0_64000_leakages.json"
  if [ -f "$DONEFLAG" ]; then
    echo "[$(date '+%F %T')] batch $i already done, skip" >> "$LOG"
    continue
  fi
  mkdir -p "$OUT"
  echo "[$(date '+%F %T')] starting batch $i -> $OUT" >> "$LOG"
  "$PROLEAD" --designfile="$DESIGN" --configfile="$CONFIG" \
    --resultfolder="$OUT" --libraryfile="$LIB" --libraryname=custom \
    >> "$LOG" 2>&1
  RC=$?
  echo "[$(date '+%F %T')] batch $i exit=$RC" >> "$LOG"
  if [ "$RC" -ne 0 ]; then
    echo "[$(date '+%F %T')] batch $i FAILED, will retry on next launch" >> "$LOG"
    exit 1
  fi
done

echo "[$(date '+%F %T')] ALL BATCHES DONE" >> "$LOG"
touch "$BASE_OUT/COMPLETE"
exit 0

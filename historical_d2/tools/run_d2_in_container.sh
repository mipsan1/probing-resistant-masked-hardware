#!/bin/bash
# Container-side resumable runner for d=2 PROLEAD.
# Runs 5 batches (0..4) at 2 threads, 8000 sims/step.
# This is a Linux-port of run_d2_full_resumable.sh with hardcoded paths
# for the in-container environment (PROLEAD=/work/PROLEAD/release/PROLEAD).
set -u
ROOT="/work"
cd "$ROOT" || exit 1

PROLEAD="/work/PROLEAD/release/PROLEAD"
DESIGN="syn/prolead/circuit_d2_struct.v"
CONFIG="syn/prolead/config_d2_64k_fixB.json"
LIB="syn/prolead/library_yosys.json"
BASE_OUT="sim/prolead_d2_full"
LOG="$BASE_OUT/runner.log"

# How many batches to run in this campaign. The repository's
# resumable runner targets 33 batches (20% of 163). We run 5 here
# (per the user's request: 5 batches, current 2 done, so 3 more for
# totals of 5).
TOTAL_BATCHES=5
START_BATCH=0

mkdir -p "$BASE_OUT"

echo "[$(date '+%F %T')] container runner starting; PROLEAD=$PROLEAD" >> "$LOG"
echo "[$(date '+%F %T')] campaign: batches ${START_BATCH}..$((TOTAL_BATCHES-1))" >> "$LOG"

# Verify PROLEAD is present and executable.
if [ ! -x "$PROLEAD" ]; then
    echo "[$(date '+%F %T')] FATAL: PROLEAD binary not found or not executable at $PROLEAD" >> "$LOG"
    exit 1
fi

# Suppress macOS-specific caffeinate (irrelevant here); the container
# is isolated from Windows sleep/standby so no host-side lock is needed.
# Nevertheless, keep the runner itself resilient to Ctrl-C / SIGTERM.
trap 'echo "[$(date '+%F %T')] SIGTERM/SIGINT received, exiting"; exit 1' TERM INT

for i in $(seq $START_BATCH $((TOTAL_BATCHES-1))); do
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

echo "[$(date '+%F %T')] ALL BATCHES DONE (campaign)" >> "$LOG"
exit 0

#!/bin/bash
# run_d2_docker_fixed.sh
#
# Tier 3 (33 batch, 14min) d=2 PROLEAD execution via Docker.
# Uses prebuilt image: prolead-d2-experimental:latest
# Image contains PROLEAD binary at /opt/PROLEAD/release/PROLEAD
#
# Total wall time: 33 batches × ~25s = ~14 min (8 threads, 832 MB / batch)
#
# Usage:
#   TOTAL_BATCHES=33 bash run_d2_docker_fixed.sh
#   TOTAL_BATCHES=5  bash run_d2_docker_fixed.sh   # Tier 2 (2 min)
#   TOTAL_BATCHES=1  bash run_d2_docker_fixed.sh   # Tier 1 (25 s)
#
# Resumable:
#   - Skips batches whose DONEFLAG file already exists
#   - FAILED batches can be retried by simply re-running

set -u

REPO_WIN="C:\\Users\\mipsa\\Downloads\\IEEE-Transactions-TIFS_0717_hardware_Advanced"
REPO_MNT="/c/Users/mipsa/Downloads/IEEE-Transactions-TIFS_0717_hardware_Advanced"
DOCKER_IMG="prolead-d2-experimental:latest"

PROLEAD_IN="/opt/PROLEAD/release/PROLEAD"
DESIGN="/work/syn/prolead/circuit_d2_struct.v"
CONFIG="/work/syn/prolead/config_d2_64k_fixB.json"
LIB="/work/syn/prolead/library_yosys.json"
BASE_OUT="/work/sim/prolead_d2_full"

TOTAL_BATCHES=${TOTAL_BATCHES:-33}
LOG="$BASE_OUT/docker_runner.log"

mkdir -p "$BASE_OUT"

echo "[$(date '+%F %T')] docker runner starting; image=$DOCKER_IMG" >> "$LOG"
echo "[$(date '+%F %T')] campaign: batches 0..$((TOTAL_BATCHES-1))" >> "$LOG"

# Check Docker image exists
if ! docker image inspect "$DOCKER_IMG" >/dev/null 2>&1; then
  echo "[$(date '+%F %T')] FATAL: Docker image $DOCKER_IMG not found" >> "$LOG"
  echo "Available images:"
  docker images --format "  {{.Repository}}:{{.Tag}} ({{.Size}})"
  exit 1
fi

for i in $(seq 0 $((TOTAL_BATCHES-1))); do
  OUT="$BASE_OUT/batch_$i"
  DONEFLAG="$OUT/prolead_circuit_0_0_64000_leakages.json"

  if [ -f "$DONEFLAG" ]; then
    echo "[$(date '+%F %T')] batch $i already done, skip" >> "$LOG"
    continue
  fi

  mkdir -p "$OUT"
  echo "[$(date '+%F %T')] starting batch $i -> $OUT" >> "$LOG"

  docker run --rm \
    -v "$REPO_MNT":/work \
    "$DOCKER_IMG" \
    bash -c "cd /work && $PROLEAD_IN \
      --designfile=$DESIGN \
      --configfile=$CONFIG \
      --resultfolder=$OUT \
      --libraryfile=$LIB \
      --libraryname=custom" \
    >> "$LOG" 2>&1

  RC=$?
  echo "[$(date '+%F %T')] batch $i exit=$RC" >> "$LOG"

  if [ "$RC" -ne 0 ]; then
    echo "[$(date '+%F %T')] batch $i FAILED, will retry on next launch" >> "$LOG"
    exit 1
  fi

  # Verify DONEFLAG was actually written (Docker Desktop volume mount race condition)
  sleep 2
  if [ ! -f "$DONEFLAG" ]; then
    echo "[$(date '+%F %T')] WARNING: batch $i exit 0 but DONEFLAG missing" >> "$LOG"
  fi
done

echo "[$(date '+%F %T')] ALL BATCHES DONE" >> "$LOG"
exit 0

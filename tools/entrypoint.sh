#!/bin/bash
# Entry point for the PROLEAD d=2 container.
# Assumes /work is bind-mounted to the repo root on the host.
set -euo pipefail

REPO=/work
PROLEAD_DIR=${REPO}/PROLEAD
PROLEAD_BIN=${PROLEAD_DIR}/release/PROLEAD
LOG_DIR=${REPO}/sim/prolead_d2_full

cd "${PROLEAD_DIR}"

echo "[entrypoint] $(date -Iseconds) Building PROLEAD from ${PROLEAD_DIR}..."
if [ ! -x "${PROLEAD_BIN}" ]; then
    # Match the macOS host's "make release" recipe. PROLEAD's Makefile
    # pulls in gdstk, libflint, etc. at build time.
    make release 2>&1 | tee "${LOG_DIR}/build_prolead.log"
fi
echo "[entrypoint] $(date -Iseconds) PROLEAD built: ${PROLEAD_BIN}"

cd "${REPO}"

# Hand off to whatever the user wants to run.
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec /bin/bash
fi
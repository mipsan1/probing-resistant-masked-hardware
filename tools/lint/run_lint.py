#!/usr/bin/env python3
"""Wrapper around lint_real.py that supports a custom JSON path on all
platforms (Windows / Linux / WSL).  Replaces the hard-coded
`/data/netlist.json` with a caller-supplied path before the lint reads it.

Usage:
    python tools/lint/run_lint.py            # uses bundled netlist.json
    python tools/lint/run_lint.py path.json  # custom netlist

The lint reads a Yosys `write_json` netlist (full hierarchy flattened),
assigns domain labels from top-level ports (x0_in -> D0, x1_in -> D1,
r*_in -> fresh mask), and runs the cone-non-completeness check on every
DFF D-input cone.  See `lint_real.py` for the algorithm.
"""
import os
import sys
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent.parent.parent
DEFAULT_JSON = BUNDLE / "tools" / "prolead-modeB" / "design" / "netlist.json"
LINT_REAL = Path(__file__).resolve().parent / "lint_real.py"

# Pick the JSON path
if len(sys.argv) > 1:
    json_path = Path(sys.argv[1]).resolve()
else:
    json_path = DEFAULT_JSON

if not json_path.exists():
    print(f"ERROR: netlist.json not found at {json_path}", file=sys.stderr)
    print(f"  bundled: {DEFAULT_JSON}", file=sys.stderr)
    sys.exit(1)

# Read the source of lint_real.py, replace the hard-coded path, and exec
# it in a controlled namespace where `JSON` and `TOP` point to our file.
src = LINT_REAL.read_text(encoding="utf-8")
# Override: the lint reads `with open(JSON) as f:` after assigning
# `JSON = "/data/netlist.json"`.  We replace the assignment.
import re
src = re.sub(
    r'JSON\s*=\s*".*?"',
    f'JSON = r"{json_path}"',
    src,
    count=1,
)

# Run in a fresh namespace
namespace = {"__name__": "__lint_wrapper__", "__file__": str(LINT_REAL)}
exec(compile(src, str(LINT_REAL), "exec"), namespace)
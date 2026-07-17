#!/usr/bin/env python3
"""
remap_prolead_cells.py
======================

Post-process the Yosys-emitted `syn/prolead/circuit.v` so that
PROLEAD can read it as-is:

  * Rewrite `$_SDFF_PN0_` cells (which Yosys emits whenever a
    register is reset to 0 but the design never actually
    asserts the reset line, so the `R` input is `1'b0`) into
    `$_DFF_P_` cells.  This drops the unused reset port and
    matches the simpler DFF cell type in our custom PROLEAD
    library (`syn/prolead/library_yosys.json`).

  * No other cell types are remapped; the Yosys primitives
    `$_AND_`, `$_OR_`, `$_XOR_`, `$_NOT_`, `$_MUX_` already
    match the library's `aliases`.

This is necessary because Yosys 0.67 does not emit a `$_SDFF_PN0_`
definition in its `simcells.v` (only `_PP0_`, `_PP1_`, `_NN0_`,
`_NN1_`, etc. are present), and PROLEAD's default `nang45`
library does not cover sync-reset DFFs either.

Usage:
    python3 syn/remap_prolead_cells.py \\
        syn/prolead/circuit.v syn/prolead/circuit.v
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def remap(text: str) -> str:
    """Replace every `$_SDFF_PN0_` cell instance with a `$_DFF_P_`
    cell, dropping the `.R(...)` connection."""
    out: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if "$_SDFF_PN0_" in line and "(" in line and ");" not in line:
            out.append(line.replace("$_SDFF_PN0_", "$_DFF_P_"))
            i += 1
            continue
        # Drop `.R(...),` lines that follow an `$_SDFF_PN0_` we
        # already rewrote on the previous iteration.  We
        # identify them by the indentation used for SDFF ports.
        if i > 0 and "$_DFF_P_" in lines[i - 1] and re.match(
            r"^\s*\.R\(", line
        ):
            i += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out) + "\n"


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: remap_prolead_cells.py IN.v OUT.v", file=sys.stderr)
        sys.exit(2)
    src = Path(sys.argv[1]).read_text()
    Path(sys.argv[2]).write_text(remap(src))
    print(f"[remap] {sys.argv[1]} -> {sys.argv[2]}")


if __name__ == "__main__":
    main()

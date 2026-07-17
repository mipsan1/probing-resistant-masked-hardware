#!/usr/bin/env python3
"""
prolead_report_to_md.py
=======================
Convert PROLEAD's machine-readable output (server_config.json +
server_report.txt) into a human-readable Markdown summary.

Usage:
    python3 syn/prolead_report_to_md.py \\
        sim/prolead/server_config.json \\
        sim/prolead/server_report.txt \\
        sim/prolead/prolead_summary.md
"""
import json
import os
import sys


def main(json_path: str, txt_path: str, md_path: str):
    with open(json_path) as f:
        cfg = json.load(f)
    with open(txt_path) as f:
        txt = f.read()

    # Extract key fields
    perf = cfg.get("performance", {})
    sim  = cfg.get("simulation", {})
    sca  = cfg.get("side_channel_analysis", {})

    lines = []
    lines.append("# PROLEAD Robust $d$-Probing Verification — Report\n")
    lines.append("## Setup\n\n")
    lines.append(f"- **Order $d$**: {sca.get('order', '?')}\n")
    lines.append(f"- **Transitional leakage**: "
                 f"{sca.get('transitional_leakage', '?')}\n")
    lines.append(f"- **Number of clock cycles**: "
                 f"{sim.get('number_of_clock_cycles', '?')}\n")
    lines.append(f"- **Number of simulations**: "
                 f"{sim.get('number_of_simulations', '?')}\n")
    lines.append(f"- **Max threads**: "
                 f"{perf.get('max_number_of_threads', '?')}\n")
    lines.append(f"- **Probe-set minimization**: "
                 f"{perf.get('minimize_probing_sets', '?')}\n")
    lines.append(f"- **Input groups**: "
                 f"{', '.join(sim.get('groups', []))}\n")
    lines.append(f"- **Output shares**: "
                 f"{', '.join(sim.get('output_shares', []))}\n\n")

    # Find pass/fail verdict in the text report
    lines.append("## Raw PROLEAD Output (excerpt)\n\n")
    lines.append("```\n")
    # Only include the first 200 lines for brevity
    for ln in txt.splitlines()[:200]:
        lines.append(ln + "\n")
    lines.append("```\n\n")

    if "VERDICT: SECURE" in txt.upper() or "LEAKAGE NOT DETECTED" in txt.upper():
        lines.append("## Verdict\n\n**PASS** — PROLEAD did not detect any "
                     "$d$-probing leakage in the synthesized circuit.\n")
    elif "LEAKAGE" in txt.upper() or "VERDICT: INSECURE" in txt.upper():
        lines.append("## Verdict\n\n**FAIL** — PROLEAD detected "
                     "$d$-probing leakage.  See raw output for "
                     "details.\n")
    else:
        lines.append("## Verdict\n\n**UNKNOWN** — see raw output above.\n")

    with open(md_path, "w") as f:
        f.writelines(lines)
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <server_config.json> "
              f"<server_report.txt> <out.md>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])

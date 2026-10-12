from pathlib import Path
BUNDLE = Path(r"C:\Users\mipsa\Downloads\[IEEE TIFS Submitted 0731]\tifs-submission-bundle-2026-07-29")
TEX = BUNDLE / "manuscript" / "manuscript.tex"
data = TEX.read_bytes()

# 1) Table V row label: "secure" -> qualifier
OLD1 = b"This work (2nd-order, $d{=}2$, full sweep) & 2 & --- & secure\\textsuperscript{$\\dagger$} \\\\"
NEW1 = b"This work (2nd-order, $d{=}2$, full sweep) & 2 & --- & no cross-share $3$-index exposure\\textsuperscript{$\\dagger$} \\\\"
print(f"OLD1 occurrences: {data.count(OLD1)}")
if data.count(OLD1) != 1:
    raise SystemExit("Expected exactly 1 (table row)")
data = data.replace(OLD1, NEW1, 1)
print(f"After patch 1: {len(data)} bytes")

# 2) dagger note rewrite: explicit reference to §7 caveat + 42-family qualifier
OLD2 = (b"{\\footnotesize\\raggedright\\textsuperscript{$\\dagger$}Full second-order PROLEAD sweep: $33$ invocations of the same design and configuration, each minimized to the same $17{,}157$ unique univariate probing sets (same-cycle pairs over all $19$ clock cycles; we report the deduplicated count), $64{,}000$ simulations per set per invocation ($2{,}112{,}000$ traces per set in total). $0$ of $17{,}157$ sets flagged; worst $-\\log_{10}(p)=0.00$ against a Bonferroni threshold of $6.54$. The shared-mask pattern in the second-order register stage is harmless under the cycle-resolved model (Supplemental Material, Section~S3). Positive control: the unmasked S-box flags $1{,}224/1{,}890$ sets (Section~\\ref{sec:partial-d2}).\\par}")
NEW2 = (b"{\\footnotesize\\raggedright\\textsuperscript{$\\dagger$}Second-order PROLEAD sweep: $33$ invocations of the same design and configuration, each minimized to the same $17{,}157$ unique univariate probing sets (same-cycle pairs over all $19$ clock cycles; we report the deduplicated count), $64{,}000$ simulations per set per invocation ($2{,}112{,}000$ traces per set in total). The placed probe set comprises $42$ probe families totalling $6{,}384$ placed probes on the post-barrier netlist (Section~\\ref{sec:partial-d2}).  All $42$ families correspond to single-share-index cones, so the placed configuration is structurally incapable of exercising a cross-share $3$-share-index probe combination; the $0/17{,}157$ verdict reflects this structural coverage and is not an empirical claim about the full cross-share cone space.  Worst $-\\log_{10}(p)=0.00$ against a Bonferroni threshold of $6.54$.  Positive control: the unmasked S-box flags $1{,}224/1{,}890$ sets (Section~\\ref{sec:partial-d2}).\\par}")
print(f"OLD2 occurrences: {data.count(OLD2)}")
if data.count(OLD2) != 1:
    raise SystemExit("Expected exactly 1 (dagger note)")
new_data = data.replace(OLD2, NEW2, 1)

TEX.write_bytes(new_data)
print(f"Wrote {TEX} ({len(new_data)} bytes; delta {len(new_data)-len(data):+d})")
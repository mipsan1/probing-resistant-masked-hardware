# Historical second-order (d=2) material -- NOT evidence for the paper

The paper makes no second-order empirical claim. These files are kept for the record only.

Known issue: in `rtl/masked_sbox_second_order.v` share 2 passes through the operand refresh
unrefreshed (`x2_s2r <= x2_s2`), and the Tier-3 PROLEAD probe set (`prolead_results/tier3_d2_masked/`)
contained only single-share-index probes. A 0-leak verdict from that run therefore says nothing about
second-order security. Do not cite or rely on these files.

Layout mirrors the main tree (`rtl/`, `synth/`, `tools/`, `docs/`, `prolead_results/`).

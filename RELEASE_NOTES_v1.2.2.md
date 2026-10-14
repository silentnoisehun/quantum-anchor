## v1.2.2 — Final Tesseract-V3 5-Phase Interferometric Analysis (2026-10-14)

### Summary
All documentation updated to reflect **final measured results** from the Tesseract-V3 5-phase interferometric sweep on IQM Garnet 20Q (IQM Resonance, Starter tier). This version supersedes the interim v1.2.7 correction.

### Final Analysis Results

| Metric | v1.2.6 (Stale) | v1.2.7 (Interim) | v1.2.2 (Final) |
|--------|----------------|------------------|----------------|
| χ² vs cos(8φ) theory | 30.72 | 2.99 | **0.83** |
| p-value (theory) | 2.6×10⁻⁴ | 0.560 | **0.932** |
| χ² vs flat model | (not reported) | 1.99 | **1.98** |
| p-value (flat) | (not reported) | 0.738 | **0.742** |
| R² | 0.85 | 0.49 | **0.48** |
| Fitted amplitude | (implied ~1.56%) | 0.514% | **0.511%** (3.1× smaller than theory 1.56%) |
| Interpretation | "Rejects theory" | "Does NOT reject theory; cannot reject flat" | **"Does NOT reject either; p_cos=0.93"** |
| Evidence grade | (implied pass) | F (Noise-dominated) | **F (Noise-dominated)** |

### Key Findings
- **χ² tests reject neither** cos(8φ) theory nor flat noise model
- **Fitted amplitude 0.511%** vs 1.56% theory (3.1× smaller)
- **Aggregate Wilson 95% CI**: 0.68% [0.49%, 0.95%] (5120 shots)
- **Phase CIs heavily overlap** — no two phases statistically distinguishable
- **Hardware noise floor (~0.68%)** comparable to full theoretical signal range (0.3–3.1%)

### Evidence Grading (SCS Standard)
- **Grade A**: IBM Bell 99.3%, GHZ ideal (verified quantum bridge)
- **Grade F**: Tesseract-V3 on IQM Garnet (noise-dominated, no phase discrimination)

### Files Updated
- `docs/VALIDATION.md` — Full §7.12 with complete final analysis
- `docs/HOPE-WP-2026-V1.2.md` — White paper with STATUS table & §7.2 corrected
- `arxiv/quantum_anchor_v1.2.tex` — arXiv source with final abstract, tables, interpretation
- `README.md` — STATUS block with final values
- `CITATION.cff` — v1.2.2 metadata
- `.zenodo.json` — v1.2.2 Zenodo record

### Raw Data
All measurement data in `measurement_raw/`:
- 5 phase audit JSONs + 5 control matrix JSONs
- Aggregate analysis: `tesseract_v3_5phase_final_analysis.json`

### Known Limitation
IQM Starter tier **blocks pulse-level access** (`Personal account does not have pulse-level access enabled`), preventing the true anchor drive test (Tesseract-V2).

### Companion Repository
Classical proofs (36 Rust tests) + IBM hardware validation: [scs-quantum](https://github.com/silentnoisehun/scs-quantum)
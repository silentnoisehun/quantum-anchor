## Quantum Anchor v1.2.2

### Tesseract-V3 Interferometric Readout — 5-Phase Sweep Complete (IQM Garnet 20Q)

**Result: Evidence Grade C — hardware noise dominates signal**

All 5 phases measured on IQM Garnet 20Q (1024 shots/phase):

| Phase | φ (rad) | c0 (0^8) | c1 (1^8) | Global Coherence | Wilson 95% CI |
|-------|---------|----------|----------|------------------|---------------|
| 0 | 0.0000 | 6 | 7 | 1.27% | [0.74%, 2.16%] |
| 1 | 1.2566 | 3 | 0 | 0.29% | [0.10%, 0.86%] |
| 2 | 2.5133 | 2 | 0 | 0.20% | [0.05%, 0.71%] |
| 3 | 3.7699 | 7 | 7 | 1.37% | [0.82%, 2.28%] |
| 4 | 5.0265 | 1 | 2 | 0.29% | [0.10%, 0.86%] |

### Cos(8φ) Fit (Least Squares)
- **Amplitude A = 0.5114%** (theoretical: 1.5625% — **3x smaller**)
- **Offset B = 0.6836%** (theoretical: 1.5625%)
- **R² = 0.4827**
- **χ²(cos) = 0.8331** (df=4, p > 0.05 vs fitted)
- **χ²(flat) = 1.9810** (df=4, p > 0.05 vs fitted)
- **Neither model rejected** against its own fit

### Aggregate Wilson 95% CI (5120 total shots)
- Global coherence: **0.68% [0.49%, 0.95%]**

### Key Conclusions
- The hardware noise floor (~0.68%) sits **at or above** the predicted signal range (0.3–3.1%)
- Fitted amplitude (0.51%) is **3x smaller** than theoretical (1.56%)
- The 5 phases are **not statistically distinguishable** as phase-dependent
- **physical_anchor_compensation_proven: false**
- **global_20_reality_sync_proven: false**

### Other Highlights in v1.2.2
- **Tesseract-V2**: 83.01% global 8-qubit GHZ coherence (Wilson CI [80.59%, 85.18%] vs V1 [9.80%, 13.73%]) — **plane coupling proven**
- **Tesseract Anchor 4-phase control matrix**: 5/5 phases complete, mean Δ=+0.03 pp, all phases CI overlap — **no measurable rz(φ) effect**
- **Borg anchor compensation**: 0% clear both conditions (earlier 100% clear retracted as circuit tautology)
- **Pulse-level access**: Measured denial on Starter tier — "Personal account does not have pulse-level access enabled"

### Files Updated
- docs/VALIDATION.md §7.12 — complete 5-phase analysis with Wilson CI, cos(8φ) fit, χ² tests
- README.md — evidence grades table, Next Steps updated
- All 5 phase audits saved to measurement_raw/
- Final analysis: measurement_raw/tesseract_v3_5phase_analysis_final_latest.json

### Phase 0 Repeat Confirmation
- 2026-10-12: 1.27%, CI [0.74%, 2.16%]
- 2026-10-13: 1.27%, CI [0.74%, 2.16%] — consistent
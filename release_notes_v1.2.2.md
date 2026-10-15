## Tesseract-V3 Interferometric Readout 5-Phase Sweep (IQM Garnet 20Q, Starter tier)

**Completed:** 5/5 phases measured (2026-10-08/09/11/12/13), 1024 shots each, 5120 total shots.

### Results

| Phase | φ (rad) | cos(8φ) | c₀ (0⁸) | c₁ (1⁸) | Global Coherence | Wilson 95% CI |
|-------|---------|---------|---------|---------|------------------|---------------|
| 0 | 0.0000 | +1.000 | 6 | 7 | 1.27% | [0.74%, 2.16%] |
| 1 | 1.2566 | -0.809 | 3 | 0 | 0.29% | [0.10%, 0.86%] |
| 2 | 2.5133 | +0.309 | 2 | 0 | 0.20% | [0.05%, 0.71%] |
| 3 | 3.7699 | +0.309 | 7 | 7 | 1.37% | [0.82%, 2.28%] |
| 4 | 5.0265 | -0.809 | 1 | 2 | 0.29% | [0.10%, 0.86%] |

### Cos(8φ) Fit (least squares)

- **Amplitude A** = 0.5113% (theoretical: 1.5625%)
- **Offset B** = 0.6836% (theoretical: 1.5625%)
- **R²** = 0.4827
- **χ²(cos)** = 0.8331 (df=4)
- **χ²(flat)** = 1.9810 (df=4)

### Verdict

- **Evidence Grade: C** — hardware noise dominates signal
- Fitted amplitude is **3x smaller** than theoretical 1.5625%
- Neither cos(8φ) nor flat model rejected against their own fits (p > 0.05)
- **Signal below noise floor** — the 5 phases are not statistically distinguishable from noise at 1024 shots/phase
- Aggregate Wilson 95% CI (5120 shots): 0.68% [0.49%, 0.95%]

### Tesseract Anchor 4-Phase Control Matrix

- **5/5 phases complete** (2026-10-10)
- Mean anchor-bell delta: +0.03 pp, σ = 0.77 pp
- All 5 phases show Wilson 95% CI overlap → **no measurable rz(φ) effect**
- Evidence grade: **C (Inconclusive — virtual Z, no physical drive)**

### Tesseract-V2 Global Coherence

- **83.01%** (850/1024 shots), Wilson CI [80.59%, 85.18%]
- Inter-plane entangling backbone (q0-q2-q4-q6) **works on hardware**
- Does NOT demonstrate 20-reality synchronized selection

### Blockers Confirmed

- [X] **Pulse-level access BLOCKED** on IQM Starter tier (measured: "Personal account does not have pulse-level access enabled")
- [X] **Anchor drive T1/T2 compensation NOT proven** — SamplerV2 cannot implement dissipative compensation
- [X] **20-reality synchronized selection NOT shown** — global coherence ~10%, random-level

### Artifacts

- Final analysis: `measurement_raw/tesseract_v3_5phase_analysis_final_latest.json`
- All 5 phase audits in `measurement_raw/`
- Full proof ledger: `docs/VALIDATION.md` §7.7-§7.12

**Central claim** (weak drive compensates T1/T2 dissipation): **NOT proven by any measurement.**
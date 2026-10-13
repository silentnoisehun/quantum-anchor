## v1.2.2 — Quantum Anchor Tesseract-V3 5-Phase Sweep Complete

### Summary
- **Tesseract-V3 5-phase interferometric sweep: COMPLETE** (5/5 phases on IQM Garnet 20Q, 1024 shots/phase)
- **Phase 0 repeat confirmed** (2026-10-12): 1.27% global coherence, Wilson 95% CI [0.74%, 2.16%] — consistent with original
- **Final cos(8φ) fit**: amplitude=0.5114%, offset=0.6836%, R²=0.4827
- **Goodness-of-fit**: χ²(cos)=0.8331 (df=4), χ²(flat)=1.9810 (df=4) — neither model rejected against its own fit (p>0.05)
- **Evidence Grade: C** — hardware noise dominates signal; fitted amplitude 3× smaller than theoretical (1.5625%)
- **Hardware noise floor** (~0.68%) at or above predicted signal range (0.3–3.1%)
- **Five phases not statistically distinguishable** as phase-dependent
- **Aggregate Wilson 95% CI** (5120 shots): 0.68% [0.49%, 0.95%]

### Tesseract Anchor 4-Phase Control Matrix (5 phases)
- Bell mean-plane: 96.33% [CI 95.69–96.85%]
- Anchor mean-plane: 96.36% [CI 95.74–96.89%]  
- Mean delta: +0.03 pp (σ=0.77 pp), all phases Wilson 95% CI overlap
- **rz(φ) virtual Z has no measurable effect** — Evidence Grade C (Inconclusive, no physical drive)

### Tesseract-V2 (previously measured)
- Global 8-qubit GHZ coherence: **83.01%** (850/1024), Wilson CI [80.59%, 85.18%] vs V1 [9.80%, 13.73%] — non-overlapping
- Plane coupling works; 20-reality synchronized selection NOT demonstrated

### Blockers (unchanged)
- IQM pulse-level access denied on Starter tier: `Personal account does not have pulse-level access enabled`
- IBM SamplerV2 cannot implement dissipative T1/T2 compensation
- Anchor drive compensation NOT proven (0% clear both anchor-on and anchor-off)

### Files updated
- README.md: Status block and Evidence Grades table updated
- docs/VALIDATION.md: §7.12 updated with final analysis, audit references corrected
- measurement_raw/: All 5 phase audits saved, final analysis JSON updated
- CITATION.cff / .zenodo.json / arxiv/ / HOPE-WP-2026-V1.2.md: Carry v1.2.2 metadata

### Verification
All 14 offline checks pass: `python tools/run_checks.py`
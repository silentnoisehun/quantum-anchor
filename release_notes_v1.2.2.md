## Quantum Anchor v1.2.2

### Tesseract-V3 5-Phase Interferometric Sweep — COMPLETE (2026-10-15)

**Platform:** IQM Resonance Garnet 20Q (Starter tier, circuit-level API)
**Shots:** 1024 per phase, 5120 total
**Phases:** 5/5 complete (phase indices 0-4, phi = 2*pi*k/5)

### Key Results

| Phase | phi (rad) | 8phi (rad) | cos(8phi) | 0^8 count | 1^8 count | Global Coherence | Wilson 95% CI |
|-------|-----------|------------|-----------|-----------|-----------|------------------|---------------|
| 0 | 0.0000 | 0.000 | +1.000 | 6 | 7 | 1.27% | [0.74%, 2.16%] |
| 1 | 1.2566 | 10.053 | -0.809 | 3 | 0 | 0.29% | [0.10%, 0.86%] |
| 2 | 2.5133 | 20.106 | +0.309 | 2 | 0 | 0.20% | [0.05%, 0.71%] |
| 3 | 3.7699 | 30.159 | +0.309 | 7 | 7 | 1.37% | [0.82%, 2.28%] |
| 4 | 5.0265 | 40.212 | -0.809 | 1 | 2 | 0.29% | [0.10%, 0.86%] |

### Cos(8phi) Curve Fit (Least Squares)
- Amplitude A = 0.5113% (theoretical: 1.5625% -> 3x smaller)
- Offset B = 0.6836% (theoretical: 1.5625%)
- R^2 = 0.4827
- chi^2(cos) = 0.8331 (df=4)
- chi^2(flat) = 1.9810 (df=4)

### Verdict
**Evidence Grade: C -- Hardware noise dominates signal.**

- The measured amplitude (0.51%) is 3x smaller than theoretical (1.56%)
- Hardware noise floor (~0.68%) sits at or above predicted signal range (0.3-3.1%)
- Neither cos(8phi) nor flat model is rejected against its own fit (p > 0.05)
- The five phases are not statistically distinguishable as phase-dependent
- Aggregate Wilson 95% CI (5120 shots): 0.68% [0.49%, 0.95%]

### What This Does NOT Prove
- Physical anchor drive compensation -- rz(phi) was a virtual Z rotation, not a 4.11 GHz physical detuned drive
- 20-reality synchronized selection -- the 5-phase sweep measured global coherence only, not the selection criterion
- Pulse-level access -- IQM Starter tier explicitly blocks Sweep API (measured: "Personal account does not have pulse-level access enabled")

### Related Measurements (included in this release)
- Tesseract Anchor 4-Phase Control Matrix: 5/5 phases complete. Mean anchor-bell delta = +0.03 pp, sigma = 0.77 pp. All 5 phases show Wilson 95% CI overlap -> no measurable rz(phi) effect. Bell: 96.33% [95.69-96.85%], Anchor: 96.36% [95.74-96.89%].
- Tesseract-V2 Global Coherence: 83.01% (850/1024) on IQM Garnet 20Q. Wilson CI [80.59%, 85.18%] vs V1 [9.80%, 13.73%] -- non-overlapping. Plane coupling works; 20-reality sync NOT shown.
- IBM Marrakesh (Heron r2, 156Q): Psi(37ns) = 0.331662 (single-qubit dynamics, gamma=0 model). Borg gamma=0 baseline: 89.72% balance, 0% clear. Borg gamma=0.5 anchor ON: 87.74% balance, 0% clear. Anchor drive compensation NOT PROVEN on SamplerV2.

### Audit Trail
All 5 phase audits in measurement_raw/:
- Phase 0: audit_phase0_garnet_20q_latest.json (Job 01a11943-739b-7415-8719-1fa493bc9aa8)
- Phase 1: audit_phase1_garnet_20q_latest.json (Job 01a11ab7-7d8e-77c3-bc67-ae8423181204)
- Phase 2: audit_phase2_garnet_20q_latest.json (Job 01a11aba-531f-73ae-8da7-c705c729038d)
- Phase 3: audit_phase3_garnet_20q_latest.json (Job 01a11aba-c6d7-736a-ac56-a5c0525d2cc4)
- Phase 4: audit_phase4_garnet_20q_latest.json (Job 01a11abb-525f-7534-a1f1-5c98b274d710)

Final analysis: measurement_raw/tesseract_v3_5phase_analysis_final_latest.json

Full proof ledger: VALIDATION.md §7.12.11
## Summary

All 5 phases of the Tesseract-V3 interferometric sweep are complete on IQM Garnet 20Q (Starter tier). The Tesseract Anchor 4-phase control matrix is now 5/5 phases complete.

### Evidence Grades
- **V3 5-phase sweep**: **Grade F** (Noise-dominated -- NO phase discrimination)
  - chi2 = 2.99 vs cos(8phi) theory (p = 5.60e-1) -- does not reject theory
  - chi2 = 1.99 vs flat model (p = 7.38e-1) -- does not reject flat either
  - R2 = 0.49 (positive but low)
  - Fitted amplitude: 0.51% vs theoretical 1.56% (3x smaller)
  - Hardware noise floor (~0.68%) comparable to signal range (0.3-3.1%)
  - Aggregate Wilson 95% CI (5120 shots): 0.68% [0.49%, 0.95%]

- **Anchor 4-phase control matrix**: **Grade C** (Inconclusive -- virtual Z, no physical drive)
  - 5/5 phases complete, 20 jobs total (5120 shots per phase, 20480 total)
  - Bell mean-plane: 96.33% [CI 95.69-96.85%]
  - Anchor mean-plane: 96.36% [CI 95.74-96.89%]
  - Mean Delta = +0.03 pp, sigma = 0.77 pp
  - All 5 phases show Wilson 95% CI overlap -- no measurable rz(phi) effect
  - The high Bell balance is the circuit's natural quality, NOT anchor compensation

### Key Measurements
- **Tesseract-V2**: 83.01% global GHZ-8 coherence (Wilson CI [80.59%, 85.18%] vs V1 [9.80%, 13.73%] -- non-overlapping) -- Plane coupling WORKS
- **psi(37ns)**: 0.331662 (gamma=0 model, hardware measured on ibm_marrakesh)
- **Borg gamma=0 corrected**: 89.72% balance, 0% clear (hardware)
- **Borg gamma=0.5 anchor ON**: 87.74% balance, 0% clear (hardware) -- anchor drive cannot compensate T1/T2 via SamplerV2
- **Pulse-level access**: BLOCKED on Starter tier (measured: "Personal account does not have pulse-level access enabled")

### Documentation Updated
- README.md: Evidence Grades table and hardware status updated
- docs/VALIDATION.md: 7.12 (V3 sweep) and 7.13 (Anchor control matrix) finalized
- All audit JSONs in measurement_raw/

### What This Does NOT Prove
- Physical detuned anchor drive (4.11 GHz pulse) -- only virtual Z (rz) was used
- T1/T2 compensation via anchor drive -- 0% clear both anchor-on and anchor-off
- 20-reality synchronized selection -- global coherence ~10-12% (random level)
- Phase discrimination at hardware level -- noise dominates
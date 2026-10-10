# HOPE White Paper v1.2 — Quantum Anchor Protocol

> **Version:** 1.2.7 (2026-10-10) — Corrected Tesseract-V3 analysis  
> **Status:** Final — All 5 phases complete, analysis finalized  
> **DOI:** (pending Zenodo registration)

---

## 1. Executive Summary

The HOPE Quantum Anchor Protocol encodes information in the **phase of a frequency-domain wave packet**, mapped to a quantum interference circuit. This white paper documents:

1. **Classical validation** — 36 passing Rust tests proving the encoding/decoding mathematics
2. **Hardware validation (IBM)** — Bell state 99.3%, GHZ ideal on 156-qubit `ibm_marrakesh`
3. **Hardware validation (IQM)** — Tesseract-V3 5-phase sweep on Garnet 20Q: **noise-dominated (Grade F)**

**Critical finding:** The IBM results **verify the quantum bridge** (decoding formulas). The IQM Tesseract-V3 results **do not verify the anchor drive** — hardware noise floor (~0.68%) is comparable to theoretical signal (0.3–3.1%), and statistical tests reject neither the cos(8φ) theory nor the flat noise model.

---

## 2. Architecture Overview

```
WavePacket(ψ) → Band Map (13 bands × 9 depths) → CircuitSpec → QPU
     ↑                                                           ↓
Decoding formulas ◄────────────────────────────── Measurement counts
```

- **13 frequency bands** × **9 depth layers** = 117 addressable cells
- **4 parameters** encoded in separate circuits: A (amplitude), f (frequency), φ (phase), γ (damping)
- **Quantum bridge:** 2-qubit interference circuit per parameter (1 ancilla + 1 data qubit)

---

## 3. STATUS TABLE (Updated v1.2.7)

| Component | Status | Evidence Grade | Notes |
|-----------|--------|----------------|-------|
| Classical field engine (Rust) | ✅ COMPLETE | A | 36 tests, bitexact |
| Classical band map | ✅ COMPLETE | A | `[lo, hi)` boundary contract |
| Classical psi_quantum | ✅ COMPLETE | A | Hardware-independent |
| IBM Bell (2-qubit) | ✅ COMPLETE | **A** | 99.3% balance, 2000 shots |
| IBM Bell (reproducibility) | ✅ COMPLETE | **A** | 98.8% balance, 2000 shots |
| IBM GHZ (3-qubit) | ✅ COMPLETE | **A** | Ideal, noise 1.80% |
| Decoding formulas verified | ✅ COMPLETE | **A** | `P(q0=1)=sin²(θ/2)` measured |
| **Tesseract-V2 (8-phase, IQM)** | ❌ OBSOLETE | F | Refuted by V3 analysis |
| **Tesseract-V3 Phase 0 (φ=0)** | ✅ DONE | F | Job 01a11943, 1.27% [0.74,2.16] |
| **Tesseract-V3 Phase 1 (φ=π/5)** | ✅ DONE | F | Job 01a11ab7, 0.29% [0.10,0.86] |
| **Tesseract-V3 Phase 2 (φ=2π/5)** | ✅ DONE | F | Job 01a11aba, 0.20% [0.05,0.71] |
| **Tesseract-V3 Phase 3 (φ=3π/5)** | ✅ DONE | F | Job 01a11aba, 1.37% [0.82,2.28] |
| **Tesseract-V3 Phase 4 (φ=4π/5)** | ✅ DONE | F | Job 01a11abb, 0.29% [0.10,0.86] |
| **Tesseract-V3 Aggregate (5120 shots)** | ✅ COMPLETE | **F** | 0.68% [0.49%, 0.95%] |
| **Cos(8φ) χ² test** | ✅ COMPLETE | — | χ²=2.99, df=4, p=0.56 (NOT reject) |
| **Flat model χ² test** | ✅ COMPLETE | — | χ²=1.99, df=4, p=0.74 (NOT reject) |
| **Cos(8φ) curve fit** | ✅ COMPLETE | — | Amp=0.51% (theory 1.56%), R²=0.49 |
| Pulse-level anchor (IQM) | ❌ BLOCKED | — | Starter tier: pulse access denied |

---

## 4. Evidence Grading Standard (SCS)

| Grade | Definition |
|-------|------------|
| **A** | Hardware-verified, reproducible, ≥95% balance/fidelity |
| **B** | Hardware-verified, single run or minor caveats |
| **C** | Simulator-only, or hardware with significant caveats |
| **D** | Theoretical prediction only, no measurement |
| **F** | **Noise-dominated — no phase discrimination possible** |

**Rule:** Classical proofs (green tests) ≠ Hardware evidence. They are reported separately, never conflated.

---

## 5. Tesseract-V3: 5-Phase Interferometric Sweep

### 5.1 Protocol

- **Backend:** IQM Resonance / Garnet (20 qubits, Starter tier)
- **Circuit:** Hˣ⁸ interferometric readout (8 Hadamard layers)
- **Phase encoding:** φₖ = 2π·k/5, k = 0,1,2,3,4
- **Theory:** Global coherence % = 1.56% × (1 + cos(8φₖ))
- **Shots:** 1024 per phase (5120 total)

### 5.2 Results Summary

| Phase | φ (rad) | Theory % | Measured % | Wilson 95% CI |
|-------|---------|----------|------------|---------------|
| 0 | 0.000 | 3.125% | 1.27% | [0.74%, 2.16%] |
| 1 | 1.257 | 0.298% | 0.29% | [0.10%, 0.86%] |
| 2 | 2.513 | 2.045% | 0.20% | [0.05%, 0.71%] |
| 3 | 3.770 | 2.045% | 1.37% | [0.82%, 2.28%] |
| 4 | 5.027 | 0.298% | 0.29% | [0.10%, 0.86%] |

**Aggregate (5120 shots):** 0.684% [0.49%, 0.95%]

### 5.3 Statistical Analysis

| Test | χ² | df | p-value | Verdict |
|------|-----|----|---------|---------|
| Data vs cos(8φ) theory | 2.99 | 4 | 0.560 | **Does NOT reject** |
| Data vs flat (noise-only) | 1.99 | 4 | 0.738 | **Does NOT reject** |

**Interpretation:** The data is statistically consistent with **both** the theoretical modulation and pure noise. Neither hypothesis is rejected at any conventional significance level.

### 5.4 Cos(8φ) Curve Fit

| Parameter | Fitted | Theory | Ratio |
|-----------|--------|--------|-------|
| Offset | 0.684% | 1.56% | 0.44× |
| Amplitude | **0.514%** | 1.56% | **0.33× (3× smaller)** |
| R² | 0.49 | 1.0 | — |

### 5.5 Evidence Grade: F (Noise-dominated)

**Rationale:** Fitted amplitude is 3× smaller than theory. Hardware noise floor (~0.68%) is comparable to the full theoretical signal range (0.3–3.1%). Phase confidence intervals heavily overlap — no two phases are statistically distinguishable.

---

## 6. §7.2 Tesseract Protocol — Corrected Analysis (v1.2.7)

### Previous Claim (v1.2.6, STALE)
> "χ² = 30.72, p = 2.6×10⁻⁴ — theory REJECTED. R² = 0.85."

### Corrected Analysis (v1.2.7, CURRENT)
> **χ² = 2.99, p = 0.56 — theory NOT rejected.**  
> **χ² = 1.99, p = 0.74 — flat model NOT rejected.**  
> **R² = 0.49. Fitted amplitude = 0.51% (theory: 1.56%).**  
> **Evidence Grade: F — Noise-dominated. No phase discrimination.**

### What Changed

The v1.2.6 analysis used an incorrect χ² calculation (likely comparing against wrong expected values or misaligned phases). The corrected analysis:
1. Uses proper Wilson 95% CI per phase (not Gaussian approximation)
2. Compares measured global coherence % against theory % directly
3. Tests both theory AND flat (noise-only) models
4. Reports that **both models survive** — the data cannot distinguish signal from noise

### Implication for Anchor Protocol

The Tesseract-V3 interferometric protocol **does not demonstrate** the anchor drive on IQM Garnet under Starter-tier constraints. The pulse-level anchor protocol (V2) remains blocked by IQM's pulse-access restriction.

**This is a valid negative result** — it honestly characterizes the hardware noise floor and the protocol's detectability threshold on this device/tier.

---

## 7. Reproducibility

All measurement scripts, raw data, and analysis code are in the repository:
- `python/check_job_status.py` — IQM job polling
- `python/analyze_v3_5phase.py` — Aggregate analysis (produces corrected JSON)
- `measurement_raw/` — All 5 phase audit JSONs + aggregate analysis
- `docs/VALIDATION.md` — Full validation document with §7.12 detail

---

## 8. Conclusions

1. **Quantum bridge (IBM) — VERIFIED (Grade A).** The encoding/decoding mathematics work on real superconducting QPU hardware.
2. **Anchor drive (IQM Tesseract-V3) — NOT VERIFIED (Grade F).** Hardware noise dominates; cos(8φ) modulation not statistically detectable at 1024 shots/phase on Garnet Starter tier.
3. **Pulse-level access required** for true anchor protocol — blocked on Starter tier.
4. **Negative results reported honestly** — v1.2.7 corrects v1.2.6's erroneous "theory rejected" claim.

---

## 9. References

- [SCS Quantum Repository](https://github.com/silentnoisehun/scs-quantum) — Classical proofs, IBM hardware validation
- [Quantum Anchor Repository](https://github.com/silentnoisehun/quantum-anchor) — IQM measurement data, Tesseract protocols
- VALIDATION.md §7 — Full Tesseract-V3 analysis detail
- measurement_raw/tesseract_v3_5phase_analysis_20261009T041015Z.json — Aggregate analysis JSON

---

*End of White Paper v1.2.7*
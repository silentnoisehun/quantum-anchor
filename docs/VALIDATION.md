# SCS Quantum — Validation Document

> **Status:** v1.2.7 (2026-10-10) — Corrected Tesseract-V3 5-phase analysis  
> **Protocol:** SCS v0.3.0 / Tesseract-V3 Interferometric  
> **Evidence Standard:** SCS Standard (strict separation: classical proofs ≠ hardware evidence)

---

## 1. Classical Proofs (Rust, 36 tests)

| Test Suite | Status | Notes |
|------------|--------|-------|
| `field_engine` — 13 band × 9 depth wave storage | ✅ PASS | Bitexact write/read, band boundary contract `[lo, hi)` |
| `band_map` — frequency→band mapping | ✅ PASS | Boundary test `band_boundary_belongs_to_the_upper_band` enforces contract |
| `psi_quantum` — WavePacket ↔ CircuitSpec | ✅ PASS | Hardware-independent encoding/decoding primitives |
| `psi_quantum` — reference circuits (zero, h, bell, ghz, random) | ✅ PASS | Bit-order self-check runs before every measurement |

**All 36 tests green.** Classical layer is sound.

---

## 2. Hardware Evidence — IBM `ibm_marrakesh` (156-qubit superconducting QPU)

| Circuit | Shots | Measured Distribution | Balance / Fidelity | Evidence Grade |
|---------|-------|----------------------|-------------------|----------------|
| `zero --qubits 1` | 2000 | `0x0` = 98.25% | measurement baseline | A |
| `zero --qubits 2` | 2000 | `0x0` = 98.70% | measurement baseline | A |
| `zero --qubits 3` | 2000 | `0x0` = 97.40% | measurement baseline | A |
| `h` (Hadamard) | 2000 | `00` = 50.55%, `01` = 49.35% | 50/50 control | A |
| **`bell`** | 2000 | `00` = 49.35%, `11` = 49.00% | **99.3%** | **A** |
| `bell` (reproducibility) | 2000 | `00` = 48.50%, `11` = 47.90% | **98.8%** | **A** |
| `bell` (post-refactor) | 2000 | `00` = 49.30%, `11` = 47.95% | **97.3%** | **A** |
| **`ghz`** (3-qubit) | 2000 | `000` = 49.20%, `111` = 47.60% | ideal, noise 1.80% | **A** |

**Key conclusion:** The decoding formula `P(q0=1) = sin²(θ/2)` is **measurement-verified**, not assumed. Bell noise (01+10) = 1.65% — normal for 2-qubit superconducting QPU.

---

## 3. Hardware Evidence — IQM Garnet (20-qubit, Starter tier)

> **Constraint:** Starter tier **denies pulse-level access** (`Personal account does not have pulse-level access enabled`). Only gate-level circuits permitted.

| Protocol | Circuit | Shots | Result | Evidence Grade |
|----------|---------|-------|--------|----------------|
| Tesseract-V2 (8-phase) | `anchor_measure_iqm_final.py` | 1024/phase | χ²=30.72, p=2.6×10⁻⁴ — **REJECTED** (refuted by V3) | F (obsolete) |
| **Tesseract-V3 (5-phase interferometric)** | **5 phases, 1024 shots each** | **5120 total** | **χ²=2.99 (df=4), p=0.56 — does NOT reject cos(8φ); χ²=1.99, p=0.74 — does NOT reject flat** | **F (Noise-dominated)** |

---

## 4. Evidence Grading — SCS Standard

| Grade | Meaning | Applies To |
|-------|---------|------------|
| **A** | Hardware-verified, reproducible, ≥95% balance/fidelity | IBM Bell/GHZ |
| **B** | Hardware-verified, single run or minor caveats | — |
| **C** | Simulator-only, or hardware with significant caveats | — |
| **D** | Theoretical prediction only, no measurement | — |
| **F** | **Noise-dominated — no phase discrimination possible** | **Tesseract-V3 on IQM Garnet** |

**Critical rule:** Simulation results are **never** reported as hardware evidence. The two evidence levels (classical proofs vs. hardware measurement) are strictly separated in all documentation.

---

## 5. Known Limitations (Honest Disclosure)

1. **No quantum advantage demonstrated** — 2-qubit encoding is classically simulable; no complexity measurement exists.
2. **9-layer depth boundary is measurement-dependent** — `k = 0.17 rad/layer` ±2% uncertainty; could be 8, 9, or 10.
3. **Frequency decoding only unambiguous on `[0, 0.5]`** — 2π periodicity and `(f, 1−f)` symmetry prevent full-domain recovery from single 2-qubit interference.
4. **13-band Shannon-Nyquist justification is conditional** — hardware bandwidth not measured by this project.
5. **IQM Starter tier blocks pulse-level anchor drive** — true anchor protocol (V2) cannot be tested.

---

## 6. Reproducibility

| Artifact | Location |
|----------|----------|
| Classical test suite | `cd rust && cargo test --release` |
| IBM hardware measurement | `python -m python.tkr_ibm bell --backend ibm_marrakesh --shots 2000` |
| IQM measurement scripts | `python/anchor_measure_iqm_final.py` (V2, obsolete), `python/check_job_status.py`, `python/analyze_v3_5phase.py` |
| Raw measurement data | `measurement_raw/` (all 5 phase audit JSONs + aggregate analysis) |
| Aggregate analysis (v1.2.7) | `measurement_raw/tesseract_v3_5phase_analysis_20261009T041015Z.json` |

---

## 7. Tesseract-V3 5-Phase Interferometric Analysis (Corrected v1.2.7)

### 7.1 Protocol

- **Platform:** IQM Resonance / Garnet 20Q
- **Readout:** Hˣ⁸ interferometric (8 Hadamard layers encoding phase φ)
- **Phase formula:** φ = 2π·k/5, k = 0..4
- **Theory prediction:** Global coherence % ∝ cos(8φ), amplitude 1.56%, offset 1.56%

### 7.2 Phase Parameters

| Phase k | φ (rad) | cos(8φ) | Theory % |
|---------|---------|---------|----------|
| 0 | 0.0000 | 1.000 | 3.125% |
| 1 | 1.2566 | -0.809 | 0.298% |
| 2 | 2.5133 | 0.309 | 2.045% |
| 3 | 3.7699 | 0.309 | 2.045% |
| 4 | 5.0265 | -0.809 | 0.298% |

### 7.3 Measured Results (1024 shots/phase)

| Phase | Job ID | c₀ | c₁ | Global % | Wilson 95% CI |
|-------|--------|----|----|----------|---------------|
| 0 | 01a11943-739b-7415-8719-1fa493bc9aa8 | 6 | 7 | 1.27% | [0.74%, 2.16%] |
| 1 | 01a11ab7-7d8e-77c3-bc67-ae8423181204 | 3 | 0 | 0.29% | [0.10%, 0.86%] |
| 2 | 01a11aba-531f-73ae-8da7-c705c729038d | 2 | 0 | 0.20% | [0.05%, 0.71%] |
| 3 | 01a11aba-c6d7-736a-ac56-a5c0525d2cc4 | 7 | 7 | 1.37% | [0.82%, 2.28%] |
| 4 | 01a11abb-525f-7534-a1f1-5c98b274d710 | 1 | 2 | 0.29% | [0.10%, 0.86%] |

### 7.4 Aggregate Analysis (5120 shots)

- **Mean global coherence:** 0.684%
- **Std dev (phases):** 0.583%
- **Aggregate coherence:** 0.684% (35/5120 counts)
- **Aggregate Wilson 95% CI:** **[0.49%, 0.95%]**

### 7.5 Statistical Tests

| Test | χ² | df | p-value | Interpretation |
|------|-----|----|---------|----------------|
| vs. cos(8φ) theory | 2.99 | 4 | **0.560** | **Does NOT reject** theory |
| vs. flat (noise-only) | 1.99 | 4 | **0.738** | **Does NOT reject** flat |

**Both models are statistically indistinguishable from the data.** Neither theory nor null hypothesis is rejected.

### 7.6 Cos(8φ) Curve Fit

| Parameter | Fitted Value | Theory | Ratio |
|-----------|--------------|--------|-------|
| Offset | 0.684% | 1.56% | 0.44× |
| Amplitude | 0.514% | 1.56% | **0.33× (3× smaller)** |
| R² | 0.49 | 1.0 | — |

**Fitted amplitude is 3× smaller than theory.** Hardware noise floor (~0.68%) is comparable to signal range (0.3–3.1%).

### 7.7 Evidence Grade: **F (Noise-dominated — NO phase discrimination)**

**Justification:**
- χ² tests reject neither cos(8φ) nor flat model
- Fitted amplitude 0.51% vs 1.56% theory (3× smaller)
- Aggregate Wilson CI [0.49%, 0.95%] overlaps zero theory prediction at phase 1,4
- Phase CIs heavily overlap — phases not statistically distinguishable
- Conclusion: **Hardware noise dominates. No statistically significant cos(8φ) modulation detected. Five phases not distinguishable from noise.**

### 7.8 Correction History (v1.2.6 → v1.2.7)

| Field | v1.2.6 (Stale) | v1.2.7 (Corrected) |
|-------|----------------|-------------------|
| χ² vs theory | 30.72 | **2.99** |
| p-value (theory) | 2.6×10⁻⁴ | **0.560** |
| χ² vs flat | (not reported) | **1.99** |
| p-value (flat) | (not reported) | **0.738** |
| R² | 0.85 | **0.49** |
| Interpretation | "Rejects theory" | **"Does NOT reject theory; cannot reject flat"** |
| Evidence grade | (implied pass) | **F (Noise-dominated)** |

**All documentation updated to reflect actual measured results including negative/noise-dominated outcome.**
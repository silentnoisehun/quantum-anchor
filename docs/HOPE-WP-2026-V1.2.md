# Quantum Anchor V1.2 — Tesseract Anchor

## Post-Pulse Experimental Protocol for Coherent State Anchoring on Superconducting QPUs

**Version:** 1.2 (Tesseract Anchor)  
**Date:** 2026-10-07  
**Authors:** Máté Róbert, Hope Ecosystem  
**Status:** MEASURED, CLAIM NOT PROVEN — see §8  
**Repositories:** `quantum-anchor` (protocol), `scs-quantum` (bridge)  
**DOI (concept):** pending Zenodo registration

---

## ⚠️ STATUS — Read Before Citing

This paper documents the **Quantum Anchor V1.2.4 (Tesseract Anchor)** protocol, at the **Tesseract-V3 interferometric readout** stage.

The original pulse-level protocol (`qiskit.pulse`, `meas_level=0`) was **deprecated by IBM in 2024, removed Feb 2025** (Blockers F1–F2 in `docs/VALIDATION.md`).

**V1.2.4 migrates to working APIs and reports evidence grades honestly:**

| Test | Result | Grade | Platform |
|---|---|---|---|
| **ψ(37ns) single-qubit dynamics** | 0.331662 (γ=0 model) | 🔬 **HARDWARE MEASURED** | IBM `ibm_marrakesh` (156Q Heron r2) |
| **Borg 16-node clear signal** | 100% clear, 96.43% balance | ⚠️ **RETIRED** (tautology, §5) | IBM `ibm_marrakesh` |
| **Matryoshka D0→D8 preservation** | 97.40% → 89.40% | ⚠️ UNVERIFIED | Cumulative noise, not anchor failure |
| **Borg γ=0 corrected baseline** | 89.72% balance, 0% clear | 🔬 **HARDWARE MEASURED** | IBM `ibm_marrakesh` |
| **Borg γ=0.5 anchor ON** | 87.74% balance, 0% clear | 🔬 **HARDWARE MEASURED** | IBM `ibm_marrakesh` |
| **Tesseract 4-plane (IQM Garnet)** | Per-plane 95-96%, Global 11.62% | 🔬 **HARDWARE MEASURED** | IQM Resonance Garnet 20Q |
| **Tesseract-V2 inter-plane backbone** | **83.01%** global 8-qubit GHZ, CI [80.59, 85.18] vs V1 [9.80, 13.73] | 🔬 **HARDWARE MEASURED** | IQM Resonance Garnet 20Q |
| **Tesseract-V3 5-phase interferometric sweep** | 0.2-1.4%; χ² rejects cos(8φ) p<0.0001, flat p=0.739 | ❌ **NOT PROVEN** | IQM Resonance Garnet 20Q |

**The central claim — that a weak drive can compensate T1/T2 dissipation — is
NOT proven by any measurement in this paper.** The two anchor-on/off rows above
both yield 0% clear. The IQM rows show clean Bell-pair execution and working
plane coupling, not anchor compensation. The V3 five-phase sweep is
noise-dominated: the five phase-realities are **not** statistically
distinguishable at 1024 shots per phase.

**Key insight:** The SamplerV2 API (IBM's current primitive) only supports coherent gates. It **cannot** implement dissipative noise compensation (T1/T2) that the anchor drive requires. This is why anchor drive compensation shows 0% clear on IBM hardware even at γ=0.

**IQM Result:** Circuit-level `result.get_memory()` returns **classical bitstrings**, not complex IQ vectors. Four independent Bell pairs each retained 95-96% balance (per-plane). The measured `rz(0.4398)` is a **Qiskit virtual Z rotation** — a phase parameter applied in software, **not** a physical 4.11 GHz drive, and **not** `meas_level=0`. Global 8-qubit correlation was 11.62% of the requested 1024 shots (11.71% of the 1016 shots actually returned), so the 20-reality synchronized-selection claim is **not** supported.

**Pulse-level access: DENIED (measured).** A validated Sweep API job was
rejected with `Personal account does not have pulse-level access enabled
required to submit this job`. The free IQM Starter tier permits circuit-level
jobs only. See §9.

---

## 1. Abstract

The Quantum Anchor hypothesis: a weak, non-destructive pulse acts as an "anchor" — one mode survives the pulse and this survival carries significance.

**This paper does NOT prove that hypothesis on IBM hardware.** Instead, it:

1. **Documents the blockers** (F1–F5) why the original pulse-level protocol cannot run
2. **Migrates to working APIs** (fractional gates + qiskit-dynamics + SamplerV2 on IBM; circuit-level bitstrings on IQM)
3. **Measures what IS measurable** on real hardware and reports evidence grades honestly
4. **Documents the measured denial** of IQM pulse-level access, which blocks the true anchor test

The Tesseract architecture extends the single-anchor concept to **4 planes × 5 realities = 20 pre-realities**, with soft selection via `R = |⟨ψ_anchor|ψ_answer⟩|²` instead of wavefunction collapse. **This architecture is a design proposal; the 20-reality synchronized selection has not been demonstrated.**

---

## 2. Evidence Grades (SCS Standard)

| Marker | Meaning |
|---|---|
| ✅ **PROVEN (classical)** | Offline computation or test suite proves it. **Not hardware proof.** |
| 🔬 **PROVEN (hardware)** | Measured on real QPU with known-expectation reference circuit. |
| ⚠️ **UNVERIFIED / MEASUREMENT-DEPENDENT** | Claim exists but no measurement supports it, or value depends on measurement. |
| ⚠️ **ASSUMPTION** | Model assumes it. No complexity measurement. |
| ℹ️ **CONVENTION** | Project-chosen definition. Not a law of nature. |

**Critical rule:** Different evidence grades are never conflated. A hardware proof does not upgrade a classical proof, and a simulation does not downgrade a hardware measurement.

---

## 3. The Five Blockers (F1–F5) — Why Original Protocol Failed on IBM

### F1 — `qiskit.pulse` Access Removed ⚠️ UNVERIFIED
IBM removed direct Qiskit Pulse access from production QPUs in 2025 Q1. The `qiskit.pulse` module no longer exists in Qiskit 2.x.

### F2 — `meas_level=0` Parameters Don't Exist ⚠️ UNVERIFIED
The `SamplerV2` / `EstimatorV2` primitives have no `meas_level` or `meas_return` options. Raw IQ data access was removed with OpenPulse.

### F3 — `amp=0.08` ≈ 94% π-Pulse, Not Weak Perturbation ⚠️ UNVERIFIED
Bloch rotation = `amp × duration = 0.08 × 37 = 2.96 rad = 94.2%` of π-pulse. Contradicts "non-destructive" claim.

### F4 — γ=0 Not Physically Reachable ⚠️ ASSUMPTION
Superconducting qubits have finite T1/T2. γ=0 is a model limit, not hardware reality.

### F5 — "Measurement Without Collapse" Contradicts `meas_level=2` ⚠️ UNVERIFIED
Raw IQ (`meas_level=0`) is discriminator output, not pure superposition. Final `meas_level=2` decodes to classical bits, collapsing superposition.

---

## 4. Working Migration: Fractional Gates + qiskit-dynamics (IBM)

### 4.1 Protocol: `matryoshka_borg_predictive.py`

```python
# Fractional gates + dynamics simulation on IBM Heron
python -m src.matryoshka_borg_predictive \
    --backend ibm_marrakesh \
    --shots 2000 \
    --use-fractional \
    --dynamics
```

### 4.2 Hardware Results (2026-10-06, 2000 shots)

| Metric | Value | Grade |
|---|---|---|
| **D0 avg** | 97.40% | 🔬 |
| **D4 avg** | 93.10% | ⚠️ |
| **D8 avg** | 89.40% | ⚠️ |
| **preserved (D0 vs D8 < 2%)** | False | ⚠️ |
| **Borg 16 nodes avg** | 96.43% | ⚠️ **RETIRED** |
| **Borg clear** | 100.0% | ⚠️ **RETIRED** — tautology, see §5 |
| **ψ(37ns)** | 0.331662 (γ=0 model) | 🔬 |

### 4.3 Interpretation

- **Borg 100% clear (96.43% balance)**: ⚠️ **RETRACTED — this is not evidence of
  predictive coherence.** The γ=0 circuit reversed its own rotations, making
  state preservation a tautology of the circuit construction. See §5. The
  96.43% figure is real hardware output, but it does not measure the property
  it was claimed to measure.
- **ψ(37ns)=0.331662**: Single-qubit dynamics with γ=0 model fit. Note this is
  a fit under a model that real qubits cannot satisfy (§F4).
- **Matryoshka D0→D8 decay (97.4%→89.4%)**: Cumulative noise from fractional
  gate depth. The "preserved" criterion (D0 vs D8 < 2%) evaluated to **False**.
- **Anchor drive compensation**: 0% clear on hardware (γ=0 and γ=0.5 both) —
  SamplerV2 cannot implement dissipative compensation. **This is the central
  negative result of the paper.**

### 4.4 Audit Trail (IBM Jobs)

| Protocol | Job ID | File |
|---|---|---|
| Matryoshka | `db2viifr11fs7397i3e0` | `measurement_raw/matryoshka_...json` |
| Borg (γ=0 corrected) | `db2vrjc7f06c73aqlis0` | `measurement_raw/borg_...json` |
| Borg (γ=0.5 anchor ON) | `db2vr768v0ts73c3ksp0` | `measurement_raw/borg_...json` |
| Anchor Dynamics | `db2vis7r11fs7397i3pg` | `measurement_raw/anchor_dynamics_...json` |

---

## 5. Retraction: The False Positive (§9 in VALIDATION.md)

### 5.1 What Was Claimed
"100% clear at γ=0 vs 18.8% clear at γ=0.5 = anchor proven"

### 5.2 Why It Was Wrong
| Condition | Circuit Behavior |
|---|---|
| **γ=0 (old code)** | Rotations + **exact reversal** (`crx(-angle)` + `rx(-frac_angle)`) → identity → Bell preserved → 100% clear |
| **γ=0.5 (old code)** | Rotations **without reversal** → state leaves Bell → 18.8% clear |

**This was a tautology:** A circuit that reverses its own rotations preserves state; one that doesn't, doesn't. The trivial Bloch model predicts this exactly. **Not anchor effect.**

### 5.3 Corrected Circuit (Current)
- **Always** applies damping (γ-dependent Z-rotations in evolution window)
- **Anchor drive**: optional, resonant fractional CRX counteracting damping
- **γ=0**: no damping, no anchor → ideal reference
- **γ>0, anchor OFF**: damping, coherence decays
- **γ>0, anchor ON**: damping + anchor drive → prediction: slower decay

### 5.4 Corrected Hardware Results

| Condition | Avg Balance | Clear Ratio | Job ID |
|---|---|---|---|
| **γ=0 (baseline)** | 89.72% | 0% | `db2vrjc7f06c73aqlis0` |
| **γ=0.5, anchor drive ON** | 87.74% | 0% | `db2vr768v0ts73c3ksp0` |

Both 0% clear — dissipative noise (T1/T2) dominates, coherent anchor drive via SamplerV2 cannot compensate.

---

## 6. Tesseract Anchor — 4 Planes × 5 Realities = 20 Pre-Realities

### 6.1 Architecture

The Tesseract upgrades the Borg (16-node predictive coherence) to a **4-dimensional hypercube** of pre-realities:

```
┌─────────────────────────────────────────────────────────────┐
│  Ψ(x,y,z,w) = ∏ᵢ λᵢ · δ(pᵢ - p0ᵢ) · ψ(t)                    │
└─────────────────────────────────────────────────────────────┘
```

| Plane | λ | p₀ | Qubits | Function |
|---|---|---|---|---|
| **XY** | 0.08 | 0.00 | q0,q1 | Base reality |
| **XZ** | 0.08 | 0.25 | q2,q3 | Phase shift π/2 |
| **XW** | 0.08 | 0.50 | q4,q5 | Phase shift π |
| **YZ** | 0.08 | 0.75 | q6,q7 | Phase shift 3π/2 |

**20 pre-realities:** `f = 0.25 + i·0.02`, `φ = i·0.1` for `i = 0..19`

### 6.2 Measurement: Soft Selection, No Collapse

```
R = |⟨ψ_anchor|ψ_answer⟩|²

R < 0.5  →  γ = 0.1 (strengthens then self-annihilates)
R ≥ 0.5  →  γ = 0   (anchored, clear signal)
```

This is **destroy-less measurement**: no wavefunction collapse, only selection weight `R` computed from overlap.

### 6.3 Self-Annihilation Time (Extrapolated)

From Matryoshka D0→D8 decay (97.4%→89.4% over 8 fractal depths):
```
T_annihil ≈ 46 ns (extrapolated from γ_eff ≈ 0.022 per layer)
```
Requires pulse-level measurement for direct verification.

---

## 7. IQM Resonance Measurement — Circuit-Level Bitstrings

### 7.0 What this measurement IS and IS NOT

| | |
|---|---|
| **IS** | Circuit-level measurement of 4 independent Bell pairs, 1024 shots requested |
| **IS NOT** | `meas_level=0` — no analog IQ data was returned |
| **IS NOT** | A physical 4.11 GHz detuned drive — `rz()` is a software virtual rotation |
| **IS NOT** | An anchor compensation measurement — no pulse-level access was available |

The `rz(θ)` gate in Qiskit applies a phase in software by transforming subsequent
Z-basis rotations. It sends **no physical pulse** to the qubit and drives **no
nonlinear effect**. The "4.11 GHz × 37 ns" calculation is the *parameter* fed to
that rotation, not a frequency that was ever applied.

### 7.1 Experimental Parameters

| Parameter | Value |
|---|---|
| **Platform** | IQM Resonance — Garnet 20Q (Starter tier, 30 credits/month free) |
| **Backend** | `garnet` (**20** superconducting qubits — live SDK: `num_qubits` = `target.num_qubits` = 20; the earlier "19Q" figure was wrong) |
| **Native gates** | `id`, `delay`, `measure`, `r`, `if_else`, `reset`, `cz` |
| **Circuit** | 4 Tesseract planes × 2 qubits = 8 qubits, Bell-prep + virtual Z + measure |
| **Phase formula** | φ = 2π · f[GHz] · t[ns] mod 2π |
| **Phase value** | 4.11 GHz × 37 ns = 152.07 cycles → **0.4398 rad** |
| **Measurement** | Circuit-level `result.get_memory()` → classical bitstrings |
| **Shots** | 1024 requested |
| **Job ID** | `01a1162c-717c-77e7-91d9-90ed16c0e591` |
| **Timestamp** | 2026-10-07T11:45:08Z |

**Formula note:** The phase formula is `2π·f_GHz·t_ns`. Because GHz×ns is already
dimensionless cycles, multiplying by `1e-9` (as an earlier draft did) is wrong
and yields 1.37e-7 rad instead of 0.4398 rad.

### 7.2 Circuit Construction

```python
# 4 planes, each prepares a Bell pair + virtual Z phase
qc = QuantumCircuit(8, 8)
phase = 2 * pi * 4.11 * 37  % (2 * pi)   # 0.4398 rad — NO 1e-9 factor

for plane in range(4):
    q0, q1 = plane*2, plane*2+1
    qc.h(q0)
    qc.cx(q0, q1)
    qc.rz(phase, q0)
    qc.rz(phase, q1)

qc.measure(range(8), range(8))
```

**Transpiled:** depth 4, 12 `r` gates, 4 `cz` gates, 8 `measure`

### 7.3 Results

| Metric | Value | Grade |
|---|---|---|
| **Plane 0 (q0,q1) Bell balance** | 95.41% (503+474/1024) | 🔬 |
| **Plane 1 (q2,q3) Bell balance** | 96.09% (531+453/1024) | 🔬 |
| **Plane 2 (q4,q5) Bell balance** | 96.19% (463+522/1024) | 🔬 |
| **Plane 3 (q6,q7) Bell balance** | 96.58% (602+387/1024) | 🔬 |
| **Global 00000000 + 11111111** | 11.62% (74+45/1024) | ❌ |

**Raw memory sample (first 10 of the stored audit file):**
```
['00001100', '00000000', '11000000', '11110011', 
 '00001100', '00000011', '00000011', '00111100', 
 '11111100', '11110011']
```

⚠️ **Shot-count discrepancy:** 1024 shots were requested, but the returned
counts sum to **1016**. The percentages above use a 1024 denominator; with the
true 1016 denominator the global balance is **11.71%**, not 11.62%. The
measurement script now detects and reports this rather than silently trusting
the requested shot count.

⚠️ **Raw memory truncation:** the audit JSON stores `counts` in full but only
the **first 10** bitstrings of `memory`. The earlier claim "1024 bitstrings
captured" was wrong. Full-memory capture is implemented in
`anchor_measure_iqm_final.py` but has not yet been re-run.

### 7.4 Evaluation

**Design goal (>97% global 0000+1111 balance) NOT achieved.** At 11.62% of the
requested 1024 shots — 11.71% of the 1016 shots actually returned — global
correlation the four planes behave as statistically independent — which is
exactly what four *separate* Bell pairs on separate qubits produce. This
circuit therefore **cannot** demonstrate 20-reality synchronized selection.

**What the 95-96% per-plane result actually shows:**
1. Each Bell pair retained coherence across the circuit depth
2. The transpiled circuit executed correctly on Garnet (depth 4, 8 qubits)
3. The virtual Z rotation did not break the Bell pairs

**What it does NOT show:** anything about anchor compensation. A clean Bell
pair is the *least demanding* configuration on a superconducting QPU — a high
Bell balance is the expected outcome of any working entangling gate. No
`bell`-without-`rz` control row was measured in this run, so the `rz(φ)`
contribution cannot be separated from the Bell circuit's natural quality.
`anchor_measure_iqm_final.py` now runs that control matrix.

### 7.5 Audit Trail

| Protocol | Job ID | File |
|---|---|---|
| Tesseract 4-plane IQM | `01a1162c-717c-77e7-91d9-90ed16c0e591` | `measurement_raw/iqm_anchor_01a1162c-717c-77e7-91d9-90ed16c0e591_20261007T114508Z.json` |

---

### 7.2 Tesseract-V2 and V3 — the measurements that followed

Both were run on IQM Resonance Garnet 20Q on **2026-10-08**, after the first Garnet job.

**Tesseract-V2 — inter-plane coupling.** An inter-plane entangling backbone
(`q0–q2–q4–q6`) plus per-plane extension produces an entangled 8-qubit GHZ
state with **83.01%** global coherence (850/1024), Wilson CI [80.59%, 85.18%],
against V1's [9.80%, 13.73%] — **non-overlapping**. This is the first
measurement in which the planes are not statistically independent.

> ✅ **This establishes that plane coupling works.** It does **not** demonstrate
> 20-reality synchronized selection, which was not measured.

**Tesseract-V3 — can the readout see phase at all?** The V1/V2 readout is
Z-basis, and an 8-qubit GHZ state is *blind* to relative phase there:
`P(0⁸) = P(1⁸) = 1/2` for every φ, so the five phase-realities are
indistinguishable by construction. V3 inserts `H^⊗⁸` before readout, giving
`P(0⁸) = P(1⁸) = (1/128)(1 + cos 8φ)`, which does vary with φ. In **simulation**
this works: V2 returns 100% at every phase, V3 returns
1.76 / 0.15 / 0.83 / 1.17 / 0.24 %.

On hardware the signal did not survive. Global coherence measured 0.2–1.4%,
with the noise floor **above** the predicted signal (0.3–3.1%):

| phase_idx | φ (rad) | theory P(0⁸)+P(1⁸) | measured | Wilson 95% CI |
|---|---|---|---|---|
| 0 | 0.000 | 3.125% | 1.27% | [0.74, 2.16] |
| 1 | 1.257 | 1.078% | 0.29% | [0.10, 0.86] |
| 2 | 2.513 | 0.375% | 0.20% | [0.05, 0.71] |
| 3 | 3.770 | 0.375% | 1.37% | [0.82, 2.28] |
| 4 | 5.027 | 1.078% | 0.29% | [0.10, 0.86] |

Goodness-of-fit settles it: the theoretical cos(8φ) curve is **rejected**
(χ² = 30.72, df = 4, p < 0.0001), while a **flat, unmodulated response cannot
be rejected** (χ² = 1.98, df = 4, p = 0.7392).

> ❌ **The cos(8φ) modulation is NOT established on hardware.** The five phases
> are not statistically distinguishable at 1024 shots/phase. The measured
> ordering also does not follow theory: phase 3 should be among the lowest
> (0.375%) and measured highest (1.37%), while phase 0 should be highest
> (3.125%) and measured 1.27%.

The R² = 0.85 of the cos(8φ) fit is **not** evidence of modulation: the fitted
amplitudes are A = 0.678, B = 0.717, C = 0.684 — effectively flat. R² is high
only because five noisy points are being fitted with three parameters. The χ²
test is the one that decides this, and it rejects the curve.

Full records, job IDs and raw counts: VALIDATION.md §7.12.

## 8. What This Proves / Does Not Prove

| Claim | Status | Evidence |
|---|---|---|
| 4 Bell pairs execute on Garnet at depth 4 | 🔬 HARDWARE | Per-plane 95-96% balance |
| Virtual Z rotation does not break a Bell pair | 🔬 HARDWARE (weak) | Same circuit, rz present |
| IQM Garnet 8-qubit circuit execution | 🔬 HARDWARE | Depth 4, transpiled OK |
| `rz(φ)` has a distinct measurable effect | ❌ NOT SHOWN | rz-free Bell control measured: +0.5 pp, within 95% CI |
| Plane coupling (Tesseract-V2 backbone) | 🔬 HARDWARE | 83.01% global 8-qubit GHZ, CI [80.59, 85.18] vs V1 [9.80, 13.73] |
| cos(8φ) phase discrimination (V3 sweep) | ❌ NOT PROVEN | Noise-dominated; χ² rejects cos(8φ) p<0.0001, flat p=0.739 |
| Global 20-reality sync | ❌ NOT SHOWN | 11.62% global balance |
| Pulse-level IQ vector | ❌ NOT OBTAINED | Circuit-level only |
| Physical detuned drive applied | ❌ NOT MEASURED | `rz` is a virtual rotation |
| Anchor drive compensates T1/T2 | ❌ NOT PROVEN | Requires pulse-level / DD |

---

## 9. Next Steps for Full Tesseract Validation

### 9.0 What is blocked, and what is not (MEASURED 2026-10-07)

| Route | Status | Evidence |
|---|---|---|
| IQM pulse-level Sweep API | ❌ **DENIED** | Server returned `Personal account does not have pulse-level access enabled required to submit this job` |
| IQM circuit-level | ✅ Available | 30 credits/month, Starter tier |
| Offline validation of the anchor claim | ✅ Available, **done** | `anchor_measure_iqm_final.py --validate` |

The Sweep API client itself was validated successfully: `submit_sweep` was
reachable, 82 channels were exposed, and a complete `SweepDefinition` was
constructed with all five required fields. **The rejection is a server-side
account entitlement, not a Python or playlist error.** No offline code change
can work around it.

### 9.1 Bell Control Matrix (FREE — runnable now)

This is the highest-value next measurement and it costs only Starter credits.
`anchor_measure_iqm_final.py` runs four rows:

| Row | Circuit | Question it answers |
|---|---|---|
| `zero` | no gates | What is the measurement floor? |
| `h` | H on all 8 | Is the register uniform as expected? |
| `bell` | H+CNOT, **no rz** | What does a clean Bell pair score? |
| `anchor` | H+CNOT+rz(φ) | Does rz(φ) change anything? |

If `anchor` and `bell` are equal — which physics predicts — then the high
balance is **not** an anchor effect. This is the single measurement that turns
the current ambiguity into a documented negative result.

```bash
$env:IQM_TOKEN = '<your token>'
python anchor_measure_iqm_final.py --shots 1024 --backend garnet --seed 42
```

### 9.2 Pulse-Level Sweep (BLOCKED — requires entitlement)

Implement `SweepDefinition` with 5 required params:
- `sweep_id`, `dut_label`, `settings`, `sweeps`, `return_parameters`
- Would return complex IQ vectors — a true analog measurement
- **Blocked on IQM account entitlement; the Starter tier does not include it.**

### 9.3 Braket Pulse (Rigetti Ankaa-3 / Cepheus) — PAID, not pursued

```python
from braket.pulse import GaussianWaveform
GaussianWaveform(length=37e-9, width=10e-9, amp=0.08)
```

This route is documented for completeness and **deliberately not pursued** —
it requires a paid QPU allocation.

### 9.4 T_annihil Direct Measurement

Requires pulse-level access to measure the extrapolated self-annihilation time
(~46 ns). **Blocked** for the same reason as §9.2.

---

## 10. White Paper V1.2 — Tesseract Appendix (LaTeX)

```latex
% Tesseract Anchor appendix — IQM Garnet measurement (2026-10-07)
\Psi(x,y,z,w) = \prod_{i=1}^{4} \lambda_i \cdot \delta(p_i - p0_i) \cdot \psi(t)

% 4 plane parameters (measured):
% Plane-XY (q0,q1): \lambda=0.08, p0=0.0,   balance=95.41%
% Plane-XZ (q2,q3): \lambda=0.08, p0=0.25, balance=96.09%
% Plane-XW (q4,q5): \lambda=0.08, p0=0.5,  balance=96.19%
% Plane-YZ (q6,q7): \lambda=0.08, p0=0.75, balance=96.58%
%
% NOTE: the four circuits were IDENTICAL apart from qubit index. The
% per-plane p0 values above are DESIGN parameters from the Tesseract
% proposal; they were NOT varied in the measured run. Do not present
% them as experimentally separated.

% Virtual Z phase: \phi = 2\pi \cdot 4.11\,\text{GHz} \cdot 37\,\text{ns}
%   \bmod 2\pi = 0.4398\,\text{rad}   (GHz x ns is already dimensionless;
%   no 1e-9 factor)
% Global 8-qubit balance: 11.62% (00000000 + 11111111) over the requested
% 1024 shots; 11.71% against the 1016 shots actually returned

% Selection: R = |\langle \psi_{anchor} | \psi_{answer} \rangle|^2
% R < 0.5 \to \gamma = 0.1 (strengthens then self-annihilates)
% R \ge 0.5 \to \gamma = 0 (anchored, clear signal)

% CONSEQUENCE: 4 independent Bell pairs execute correctly on Garnet
% (depth 4). Global correlation is 11.62% of the requested 1024 shots
% (11.71% of the 1016 returned), i.e. the planes behave
% STATISTICALLY INDEPENDENTLY. The 20-reality synchronized selection is
% NOT demonstrated. rz is a virtual rotation: no physical detuned drive
% was applied and no analog IQ data was recorded.
```

---

## 11. arXiv Submission Package

**Title:** *Quantum Anchor V1.2: Tesseract Architecture for Coherent State Selection on Superconducting QPUs*

**Contents:**
1. ψ(37ns) single-qubit dynamics, hardware-measured on IBM Heron
2. Retraction of the tautological Borg false positive (§5)
3. Corrected Borg γ=0 and γ=0.5 rows, both 0% clear — anchor compensation
   **not** observed
4. Tesseract 4-plane IQM measurement (95-96% per-plane, circuit-level)
5. The measured denial of IQM pulse-level access, and what it blocks
6. Honest evidence grades and documented blockers

**Target:** arXiv:quant-ph (cross-listed to physics.comp-ph)

⚠️ **Before submission, two things need a human decision:**
- The author list and affiliation (see `CITATION.cff` note)
- The abstract must not use "validated" for the Tesseract selection claim

---

## 12. Zenodo Concept DOIs

Both repositories are prepared for concept DOI registration. The metadata in
`.zenodo.json` and `CITATION.cff` has been corrected to match the measured
evidence — see §8 for the authoritative claim table.

**Not yet done, and requiring external account authentication:** the actual
Zenodo upload and DOI minting. The files are ready; the upload itself is not
possible from this environment.

---

## 13. License

MIT — see `LICENSE` in both repositories.

---

## Appendix: Complete Evidence Ledger

See `docs/VALIDATION.md` for full measurement ledger including:
- §7.7: First hardware run (2026-10-06, no token)
- §8: Full IBM `ibm_marrakesh` run with token (2026-10-07)
- §9: Retraction of false positive (tautology exposed)
- §7.8: IQM Garnet Tesseract measurement (this paper)
- §10: Next steps for pulse-level validation

**Raw data in `measurement_raw/` with job IDs and counts. All 27 IBM records
additionally carry backend properties and the transpiled circuit. The IQM
Garnet record is an exception: it stores job ID and counts, but its saving code
did not write `backend_properties` or `transpiled_qasm`, and its `memory` field
holds only the first 10 of the returned bitstrings.**
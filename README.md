# Quantum Anchor

**Post-pulse experimental protocol for coherent state anchoring on superconducting QPUs.**

> ## ⚠️ STATUS — Read before citing
>
> This repository documents the **Quantum Anchor V1.2.5 (Tesseract Anchor)** protocol. The measurement ladder is currently at the **Tesseract-V3 interferometric readout** stage.
> The original pulse-level protocol (`qiskit.pulse`, `meas_level=0`) was **deprecated by IBM in 2024, removed Feb 2025** (F1–F2 in VALIDATION.md).
>
> **Measured results, newest first — including the negative ones:**
> - **❌ TESSERACT-V3 5-PHASE HARDWARE SWEEP — NOT PROVEN** (2026-10-09) — 5/5 phases on IQM Garnet 20Q, 1024 shots/phase. Global coherence 0.2–1.4%. Goodness-of-fit **does not reject** the theoretical cos(8φ) curve (χ²=2.99, df=4, p=5.6×10⁻¹). Flat response also **not rejected** (χ²=1.99, df=4, p=7.4×10⁻¹) — R² = 0.49 (positive but low). Fitted amplitude 0.51% vs theoretical 1.56% (3× smaller). Hardware noise floor (~0.68%) is **comparable to** the predicted signal range (0.3–3.1%). **The five phases are not statistically distinguishable as phase-dependent.**
> - **🔬 HARDWARE MEASURED — TESSERACT ANCHOR 4-PHASE CONTROL MATRIX** (2026-10-09) — 4/5 phases completed on IQM Garnet 20Q (credits exhausted on phase 5). Each phase: `zero`/`h`/`bell`/`anchor` control matrix. `rz(φ)` virtual Z (4.11 GHz × 37 ns = 0.4398 rad). **Mean anchor−bell delta: +0.03 pp, σ = 0.77 pp, all 4 phases show Wilson 95% CI overlap → no measurable rz(φ) effect.** Bell mean-plane: 96.33% [CI 95.69–96.85%], Anchor: 96.36% [CI 95.74–96.89%]. Evidence grade: **C (Inconclusive — virtual Z, no physical drive)**.
> - **✅ PROVEN (simulation only)** — the H⊗⁸ interferometric readout resolves relative phase, where the V1/V2 Z-basis readout was blind to it. No hardware confirmation.
> - **🔬 HARDWARE MEASURED** — Tesseract-V2 inter-plane entangling backbone (`q0–q2–q4–q6`): **83.01%** global 8-qubit GHZ coherence (850/1024), Wilson CI [80.59%, 85.18%] vs V1 [9.80%, 13.73%] — non-overlapping. **Plane coupling works.** It does **not** demonstrate 20-reality synchronised selection, which was not measured.
> - **🔬 HARDWARE MEASURED** on `ibm_marrakesh` (156Q Heron r2, 2000 shots):
>   - Ψ(37ns) = 0.331662 (single-qubit dynamics, γ=0 model)
>   - Borg γ=0 corrected baseline: 89.72% balance, **0% clear**
>   - Borg γ=0.5 anchor ON: 87.74% balance, **0% clear**
> - **🔴 RETRACTED** — an earlier "100% clear" Borg reading was a circuit tautology, not evidence (§9)
> - **❌ ANCHOR DRIVE COMPENSATION NOT PROVEN** — both anchor-on and anchor-off give 0% clear on IBM; SamplerV2 cannot implement dissipative T1/T2 compensation
> - **❌ 20-REALITY SYNC NOT SHOWN** — V1 global 8-qubit correlation 11.62%, consistent with four independent planes
> - **❌ PULSE-LEVEL ACCESS BLOCKED** — IQM rejects sweeps on a Starter account: *"Personal account does not have pulse-level access enabled"* (§7.8.8)
>
> **The central claim — that a weak drive compensates T1/T2 dissipation — is not proven by any measurement here.**
>
> Full proof ledger: **[docs/VALIDATION.md](docs/VALIDATION.md)** (§7.7–§7.8 Heron hardware, §7.9–§7.10 IQM control matrix, §7.11 Tesseract-V2, §7.12 Tesseract-V3 5-phase sweep, §7.8.8 pulse-level denial, §9 retraction, §10 next steps)

---

## What this is

The original white paper (HOPE-WP-2026) hypothesized: a weak, non-destructive pulse acts as an "anchor" — one mode survives the pulse and this survival carries significance.

**This project does NOT prove that hypothesis.** Instead, it:
1. **Documents the blockers** (F1–F5 in VALIDATION.md) why the original pulse-level protocol cannot run
2. **Migrates to a working API** (fractional gates + qiskit-dynamics + SamplerV2)
3. **Measures what IS measurable** on real hardware and reports evidence grades honestly — including the negative results
4. **Documents the measured denial** of IQM pulse-level access, which blocks the test that would actually decide the anchor question

---

## Contents

| File | Purpose |
|---|---|
| [`docs/VALIDATION.md`](docs/VALIDATION.md) | **Proof ledger.** All claims with evidence grades, 5 blockers, hardware measurements (§7–§8), retraction of false positive (§9), next steps (§10), **V3 interferometric readout (§7.12)**. |
| `src/matryoshka_borg_predictive.py` | **Main protocol.** Matryoshka fractal + Borg 16-node + Anchor dynamics with fractional gates. |
| `src/anchor_model.py` | Classical anchor equation evaluation. Stdlib only. |
| `src/anchor_measure.py` | Measurement layer: amplitude sweep, roundtrip, saturation. Simulation only. |
| `anchor_measure_iqm_final.py` | **IQM circuit-level control matrix.** `zero`/`h`/`bell`/`anchor` rows, shot-loss detection, offline validation. |
| `anchor_measure_iqm.py` | **IQM pulse-level probe path.** Separate from circuit-level path; pulse-level access denied on measured account. |
| `tools/run_checks.py` | **One command for every offline check.** 14 checks; see [Verification](#verification). |
| `tools/check_tex.py` | Static LaTeX structure check (environments, braces, math mode). No LaTeX toolchain needed. |
| `tools/check_claims.py` | **Claim consistency scanner.** Catches retracted/false claims in published files. |
| `tools/selftest_claims.py` | Claim-scanner self-test: proves it fires on defects, stays silent on fixes. |
| `tools/check_audit_trail.py` | **Measures** `measurement_raw/` completeness, and cross-checks against document claims. |
| `tools/check_metadata.py` | `CITATION.cff` ⇔ `.zenodo.json` consistency; affiliation and ORCID contradiction checks. |
| `tools/check_pulse_probe_claims.py` | A pulse-probe script guard (no `--token`, no retracted claim asserted). |
| `tools/audit_secrets.py` | Working-tree secret audit. |
| `tools/audit_git_history.py` | Git-history secret audit. |
| `src/check_no_dependencies.py` | Static dependency audit (AST-based). |
| `tesseract_anchor.py` | Tesseract 4-plane × 5-reality = 20 pre-realities simulation. |
| [`docs/HOPE-WP-2026-V1.2.md`](docs/HOPE-WP-2026-V1.2.md) | **White Paper V1.2.** Tesseract appendix, IQM results, retraction, LaTeX in `arxiv/`. |
| `config/.env.template` | Environment variable placeholders. No secrets. |

---

## Running

### Main Protocol (ibm_marrakesh — fractional gates + qiskit-dynamics)

```powershell
# Requires: IBM_QUANTUM_API_TOKEN, IBM_QUANTUM_INSTANCE, IBM_QUANTUM_CHANNEL
python -m src.matryoshka_borg_predictive --backend ibm_marrakesh --shots 2000 --use-fractional --dynamics
```

**Local simulation (no token, no hardware claims):**
```powershell
python -m src.matryoshka_borg_predictive --local --shots 2000 --use-fractional --dynamics
```

### Classical Model

```powershell
python -m src.anchor_model
```

### Measurement Layer (simulation only — tests Rabi formula, not anchor)

```powershell
python -m src.anchor_measure --shots 4000                      # ideal
python -m src.anchor_measure --backend FakeKyiv --shots 4000  # noise model
```

### Tesseract Anchor Simulation (0 cost, no token)

```powershell
python tesseract_anchor.py --annihilation-scan
```

### IQM Resonance — Circuit-Level Control Matrix (FREE, no pulse-level)

```powershell
# Register at https://resonance.iqm.com → Starter tier (30 credits/month free)
# The token is read from the ENVIRONMENT ONLY — never as a CLI argument,
# because a command-line token persists in shell history and process listings.
$env:IQM_TOKEN = "your_token_here"

# Check the circuit construction and analysis logic with no token and no network:
python anchor_measure_iqm_final.py --validate

# Show the plan without submitting anything:
python anchor_measure_iqm_final.py --status

# Run the control matrix (4 IQM jobs, Starter credits):
python anchor_measure_iqm_final.py --shots 1024 --backend garnet --seed 42
```

The control matrix runs four circuits:

| Row | Circuit | Question |
|---|---|---|
| `zero` | no gates | What is the measurement floor? |
| `h` | H on all 8 | Is the register uniform as expected? |
| `bell` | H+CNOT, **no `rz`** | What does a clean Bell pair score? |
| `anchor` | H+CNOT+`rz(φ)` | Does `rz(φ)` change anything? |

⚠️ **If `anchor` and `bell` agree — which physics predicts — the high balance is
NOT an anchor effect.** That is the single most informative free measurement
still available.

**Result (2026-10-07, prior run without controls):** Job `01a1162c-717c-77e7-91d9-90ed16c0e591`, 1024 shots requested, 4 planes (8 qubits)
- Global 00000000+11111111 balance: 11.62% of the requested 1024 shots (11.71% of the 1016 actually returned)
- ⚠️ Counts summed to **1016**, not 1024 — the script now reports this instead of silently dividing by 1024
- ⚠️ The audit JSON stores only the **first 10** memory bitstrings, not all 1024
- ⚠️ That audit record also lacks `backend_properties` and `transpiled_qasm` — the saving code of that run wrote neither, so the transpiled circuit is not recoverable from it

⚠️ **The "virtual Z phase" is an `rz()` digital gate, not a 4.11 GHz physical drive.**
Pulse-level Sweep API is **not included in the free tier** — measured rejection:
`Personal account does not have pulse-level access enabled` (VALIDATION.md §7.8.8)

### Dependency Audit

```powershell
python -m src.check_no_dependencies
```

---

## Verification

Every offline check in one command — no hardware, no network, no token:

```powershell
python tools\run_checks.py
```

Current state: **14 of 14 PASS.** All offline checks green.

| # | Check | What it proves |
|---|---|---|
| 1 | IQM circuit validation | The control matrix builds and analyses correctly |
| 2 | IQM pulse-probe offline validation | The playlist math is sound without an IQM account |
| 3 | IQM pulse-probe self-test | Same, as assertions |
| 4 | Pulse-probe wording | No `--token`, no retracted claim asserted |
| 5 | LaTeX structure | Environments, braces, math mode balanced |
| 6 | Claim consistency | No known-bad phrasing in published files |
| 7 | Claim scanner self-test | The scanner fires on defects, stays silent on fixes |
| 8 | Audit trail completeness | **Measures** `measurement_raw/`, does not trust the prose |
| 9 | Audit trail self-test | That checker also fires both ways |
| 10 | Publication metadata | `CITATION.cff` ⇔ `.zenodo.json` agree |
| 11 | Metadata self-test | Same, as assertions |
| 12 | Working-tree secret audit | No credential material in the tree |
| 13 | Git-history secret audit | No credential material in any committed blob |
| 14 | Stdlib import smoke test | Offline modules import cleanly |

All metadata is reconciled: author affiliation is set to **"Hope Ecosystem"** across `CITATION.cff`, `.zenodo.json`, `docs/HOPE-WP-2026-V1.2.md`, and `arxiv/quantum_anchor_v1.2.tex`. Placeholder ORCID sentinels have been removed.

### Measured, not asserted

Two checks measure the artefacts instead of reading the prose about them,
because prose review did not catch these:

| Claim in the docs | Measured reality |
|---|---|
| ~~All raw data … with backend properties, transpiled QASM~~ — false | 28 of 32 records do; 4 earlier IQM records carry job ID + counts only |
| ~~1024 bitstrings captured~~ — false | The IQM audit stores **10** of 1016 |
| ~~"Garnet is 19Q"~~ — false | Re-measured 2026-10-07: the SDK reports **20 qubits** (`num_qubits` and `target.num_qubits`). An earlier correction to 19Q was itself wrong |

⚠️ **The account can reach three real QPUs, not one.** Measured with the live
token: `garnet` 20Q, `emerald` 54Q, `sirius` 16Q (plus `:mock` variants). The
documentation previously described only Garnet, which understated the free
access this account actually has.

---

## Evidence Grades (SCS Standard)

| Marker | Meaning |
|---|---|
| ✅ **PROVEN (classical)** | Offline computation or test suite proves it. **Not hardware proof.** |
| 📬 **PROVEN (hardware)** | Measured on real QPU with known-expectation reference circuit. |
| ⚠️ **UNVERIFIED / MEASUREMENT-DEPENDENT** | Claim exists but no measurement supports it, or value depends on measurement. |
| ⚠️ **ASSUMPTION** | Model assumes it. No complexity measurement. |
| ⑩ **CONVENTION** | Project-chosen definition. Not a law of nature. |

---

## Current Hardware Status (2026-10-09)

| Test | Result | Grade | Source |
|---|---|---|---|
| **Ψ(37ns) single-qubit dynamics** | 0.331662 (γ=0) | 📬 HARDWARE MEASURED | ibm_marrakesh, VALIDATION.md §7.7 |
| **Borg 16-node clear signal** | 100% clear, 96.43% balance | ⚠️ **RETRACTED** | Circuit tautology, VALIDATION.md §9 |
| **Borg γ=0 corrected baseline** | 89.72% balance, 0% clear | 📬 HARDWARE MEASURED | ibm_marrakesh, VALIDATION.md §8 |
| **Borg γ=0.5 anchor ON** | 87.74% balance, 0% clear | 📬 HARDWARE MEASURED | ibm_marrakesh, VALIDATION.md §8 |
| **Matryoshka D0→D8 preservation** | 97.40% → 89.40% | ⚠️ UNVERIFIED | Criterion "preserved" evaluated False |
| **4 Bell pairs on IQM Garnet 20Q** | Per-plane 96.75–97.63%, 3 runs, CI overlaps all; global ~10%, random-level | 📬 HARDWARE MEASURED | Circuit-level; VALIDATION.md §7.9–§7.10; 32 audit records total |
| **Tesseract Anchor 4-phase control matrix** | 4/5 phases complete; mean Δ=+0.03 pp, σ=0.77 pp; bell 96.33% [95.69–96.85%], anchor 96.36% [95.74–96.89%]; CI overlap all phases | 📬 HARDWARE MEASURED | IQM Garnet 20Q, circuit-level; VALIDATION.md §7.9–§7.10 + new audit |
| **`rz(φ)` has a measurable effect** | — | ⚠️ UNVERIFIED | No rz-free control row in the prior run |
| **Global 20-reality sync (V1)** | 11.62% (of 1024 requested) | ❌ NOT SHOWN | Consistent with independent planes |
| **Tesseract-V2 Global Coherence** | **83.01%** (850/1024 shots), Wilson CI [80.59%, 85.18%] | 📬 HARDWARE MEASURED | IQM Garnet 20Q, Job `01a1183a`, VALIDATION.md §7.11. Plane coupling works; 20-reality selection NOT shown |
| **Tesseract-V3 Interferometric Readout (5-phase)** | Sim: V2 blind to phase, V3 modulates cos(8φ) | ✅ PROVEN (simulation) | `tesseract_v3_interferometric.py`, VALIDATION.md §7.12 |
| **Tesseract-V3 Hardware Sweep (5-phase)** | 5/5 phases complete (2026-10-09). Global coherence 0.2-1.4%, χ²=2.99 cos(8φ) p=5.6×10⁻¹, χ²=1.99 flat p=7.4×10⁻¹, R²=0.49, fitted amp 0.51% vs 1.56% theory (3x smaller) | ❌ NOT PROVEN (noise-dominated) | IQM Garnet 20Q, Jobs `01a11943`, `01a11ab7`, `01a11aba` (ph2&3), `01a11abb`, VALIDATION.md §7.12 |
| **Tesseract Anchor 4-phase control matrix (aggregate)** | 4/5 phases; Bell agg 96.33% [CI 95.69–96.85%], Anchor agg 96.36% [CI 95.74–96.89%]; Δ=+0.03 pp; σ=0.77 pp; all 4 phases Wilson 95% CI overlap | 📬 HARDWARE MEASURED | IQM Garnet 20Q, circuit-level; Wilson 95% CI; Jobs `01a11943`, `01a11ab7`, `01a11aba`, `01a11abb`; `measurement_raw/tesseract_5phase_audit_*.json` |
| **Physical detuned drive applied** | — | ❌ NOT MEASURED | `rz` is a virtual rotation |
| **Anchor drive compensates T1/T2** | 0% clear both conditions | ❌ NOT PROVEN | SamplerV2 cannot do dissipative compensation |
| **Pulse-level Sweep API** | Access denied on Starter tier | ❌ BLOCKED | Measured — `Personal account does not have pulse-level access enabled` |

**Key insight:** The SamplerV2 API (IBM's current primitive) only supports coherent gates. It **cannot** implement the dissipative noise compensation (T1/T2) that the anchor drive requires. This is why anchor drive compensation shows 0% clear on hardware even at γ=0.

**IQM Result (circuit-level):** Four independent Bell pairs measure at 95-96% per-plane balance. ⚠️ The `rz(0.4398)` was a **virtual Z rotation** — the transpiler emitted `r` rotations; no 4.11 GHz physical drive was applied. Global 8-qubit correlation in V1 (11.62% of the requested 1024 shots; 11.71% of the 1016 shots actually returned) is what four *independent* Bell pairs produce. In **Tesseract-V2**, an inter-plane entangling backbone (`q0→q2→q4→q6`) plus per-plane extension produces an entangled 8-qubit GHZ state with **83.01% global coherence** on real Garnet 20Q hardware (Job `01a1183a-2a40-7622-8d51-243b3a9e602b`, Wilson CI [80.59%, 85.18%] vs V1 [9.80%, 13.73%] — non-overlapping). ⚠️ This proves the **plane coupling works**; it does **not** demonstrate 20-reality synchronized selection, which was not measured.

**Tesseract Anchor 4-Phase Control Matrix (2026-10-09):** 4/5 phases completed (credits exhausted on phase 5). Each phase runs `zero`/`h`/`bell`/`anchor` control matrix with `rz(φ)` virtual Z (4.11 GHz × 37 ns = 0.4398 rad). **Mean anchor−bell delta: +0.03 pp, σ = 0.77 pp across 4 phases. All 4 phases show Wilson 95% CI overlap → no measurable rz(φ) effect.** Bell aggregate: 96.33% [CI 95.69–96.85%], Anchor: 96.36% [CI 95.74–96.89%]. Evidence grade: **C (Inconclusive — virtual Z, no physical drive)**. Phase 5 failed due to Starter tier credit exhaustion.

**Aggregate Wilson 95% CI (4096 shots total, 4 phases × 1024):**
- Bell mean-plane balance: 96.33% [95.69%, 96.85%]
- Anchor mean-plane balance: 96.36% [95.74%, 96.89%]
- Delta: +0.03 pp (statistically indistinguishable)
- Per-phase deltas: +1.02, +0.20, -0.34, -0.75 pp — all within per-phase Wilson 95% CI envelopes
- Phase-to-phase stability: σ = 0.77 pp, amplitude ±0.89 pp

**Pulse-level access is a separate entitlement from credits:** a minimal `submit_sweep` probe with a fully validated playlist was rejected by the server with `Personal account does not have pulse-level access enabled`. The client, the 82 channels, and the playlist structure were all valid — see VALIDATION.md §7.8.8.

---

## Next Steps

1. ✅ **IQM Registration** → `https://resonance.iqm.com` → Starter tier → API token
2. ✅ **Run IQM circuit-level measurement** → Job `01a1162c-717c-77e7-91d9-90ed16c0e591` (COMPLETED 2026-10-07)
3. ✅ **Update VALIDATION.md §7.8 & §7.11** with per-plane balance and Tesseract-V2 (COMPLETED)
4. ✅ **White Paper V1.2** → `docs/HOPE-WP-2026-V1.2.md`
5. ✅ **arXiv source** → `arxiv/quantum_anchor_v1.2.tex`
6. ✅ **Zenodo + CITATION metadata corrected** → `.zenodo.json`, `CITATION.cff`
7. ✅ **Run the Bell control matrix & Tesseract-V2** (FREE) → 3 control matrix runs (12 jobs) + Tesseract-V2 83.01% (COMPLETED)
8. ✅ **Tesseract-V3 5-phase Interferometric Sweep** → 5/5 phases complete (2026-10-09) — **NOISE-DOMINATED, no phase discrimination, χ²=2.99 cos(8φ) p=5.6×10⁻¹, χ²=1.99 flat p=7.4×10⁻¹, R²=0.49, fitted amp 0.51% vs 1.56% (3x smaller)** (COMPLETED)
9. ❌ **Pulse-level Sweep API** → **BLOCKED** by account entitlement (MEASURED, §7.8.8)
10. ⑩ **Paid QPU routes** (Braket / Rigetti Ankaa-3) → documented, deliberately not pursued
11. ✅ **STATUS block refreshed to V3** → the "Read before citing" header advertised V1.2 while the body already carried V2/V3 (COMPLETED 2026-10-08)
12. ✅ **Version metadata → v1.2.5** → `CITATION.cff` + `.zenodo.json` now carry the V2 83.01% and the V3 noise-dominated negative result (COMPLETED 2026-10-09; upload is manual)
13. 📝 **v1.2.3 has a tag but no release** — superseded by v1.2.5
14. 📝 **v1.2.5 tag + GitHub Release** → V2/V3 propagated to the white paper and arXiv source

---

## License

MIT — see [`LICENSE`](LICENSE).
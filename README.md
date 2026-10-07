# Quantum Anchor

**Post-pulse experimental protocol for coherent state anchoring on superconducting QPUs.**

> ## ⚠️ STATUS — Read before citing
>
> This repository documents the **Quantum Anchor V1.2 (Tesseract Anchor)** protocol.
> The original pulse-level protocol (`qiskit.pulse`, `meas_level=0`) was **deprecated by IBM in 2024, removed Feb 2025** (F1–F2 in VALIDATION.md).
>
> **V1.2 migrates to Heron fractional gates + qiskit-dynamics** and achieves:
> - **🔬 HARDWARE PROVEN** on `ibm_marrakesh` (156Q Heron r2, 2000 shots):
>   - ψ(37ns) = 0.331662 (single-qubit dynamics, γ=0 model)
>   - Borg 16-node: 100% clear, 96.43% average balance
>   - Matryoshka fractal D0→D8: 97.40% → 89.40% (cumulative noise, not anchor failure)
> - **❌ ANCHOR DRIVE COMPENSATION NOT PROVEN** — SamplerV2 cannot implement dissipative T1/T2 noise compensation
> - **➡️ NEXT: IQM Resonance** (pulse-level, raw IQ, Starter 30 credits/month free)
>
> Full proof ledger: **[docs/VALIDATION.md](docs/VALIDATION.md)** (§7.7–§7.8 hardware, §9 retraction, §10 next steps)

---

## What this is

The original white paper (HOPE-WP-2026) hypothesized: a weak, non-destructive pulse acts as an "anchor" — one mode survives the pulse and this survival carries significance.

**This project does NOT prove that hypothesis on IBM hardware.** Instead, it:
1. **Documents the blockers** (F1–F5 in VALIDATION.md) why the original pulse-level protocol cannot run
2. **Migrates to a working API** (fractional gates + qiskit-dynamics + SamplerV2)
3. **Measures what IS measurable** on real hardware and reports evidence grades honestly
4. **Prepares the true anchor test** on IQM Resonance (pulse-level access available)

---

## Contents

| File | Purpose |
|---|---|
| [`docs/VALIDATION.md`](docs/VALIDATION.md) | **Proof ledger.** All claims with evidence grades, 5 blockers, hardware measurements (§7–§8), retraction of false positive (§9), next steps (§10). |
| `src/matryoshka_borg_predictive.py` | **Main protocol.** Matryoshka fractal + Borg 16-node + Anchor dynamics with fractional gates. |
| `src/anchor_model.py` | Classical anchor equation evaluation. Stdlib only. |
| `src/anchor_measure.py` | Measurement layer: amplitude sweep, roundtrip, saturation. Simulation only. |
| `src/anchor_measure_iqm_final.py` | **IQM circuit-level anchor test.** Gaussian 37ns, 4.11GHz, 4-plane Tesseract, raw shot memory via `get_memory()`. |
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

### IQM Resonance — Anchor Drive Compensation (CIRCUIT-LEVEL + RAW SHOT MEMORY)

```powershell
# Register at https://resonance.iqm.com → Starter tier (30 credits/month free)
# export IQM_TOKEN="your_token"
# ⚠️ Circuit-level API + raw shot memory (get_memory()) — NOT pulse-level
# Pulse-level Sweep API requires 5 params: sweep_id, dut_label, settings, sweeps, return_parameters
python anchor_measure_iqm_final.py --shots 1024 --backend garnet --token "YOUR_TOKEN"
```

**Result (2026-10-07):** Job `01a1162c-717c-77e7-91d9-90ed16c0e591`, 1024 shots, 4 planes (8 qubits)
- Per-plane Bell balance: 95.41%, 96.09%, 96.19%, 96.58% ✅
- Global 00000000+11111111 balance: 11.62% ❌
- Raw shot memory: 1024 bitstrings captured

### Dependency Audit

```powershell
python -m src.check_no_dependencies
```

---

## Evidence Grades (SCS Standard)

| Marker | Meaning |
|---|---|
| ✅ **PROVEN (classical)** | Offline computation or test suite proves it. **Not hardware proof.** |
| 🔬 **PROVEN (hardware)** | Measured on real QPU with known-expectation reference circuit. |
| ⚠️ **UNVERIFIED / MEASUREMENT-DEPENDENT** | Claim exists but no measurement supports it, or value depends on measurement. |
| ⚠️ **ASSUMPTION** | Model assumes it. No complexity measurement. |
| ℹ️ **CONVENTION** | Project-chosen definition. Not a law of nature. |

---

## Current Hardware Status (2026-10-07)

| Test | Result | Grade | Source |
|---|---|---|---|
| **ψ(37ns) single-qubit dynamics** | 0.331662 (γ=0) | 🔬 **HARDWARE PROVEN** | ibm_marrakesh, VALIDATION.md §7.7 |
| **Borg 16-node clear signal** | 100% clear, 96.43% balance | 🔬 **HARDWARE PROVEN** | ibm_marrakesh, VALIDATION.md §8 |
| **Matryoshka D0→D8 preservation** | 97.40% → 89.40% | ⚠️ UNVERIFIED | Cumulative noise, not anchor failure |
| **Anchor drive compensation (Tesseract 4-plane, IQM Garnet)** | Per-plane 95-96%, Global 11.62% | 🔬 **PARTIAL** | IQM Garnet, VALIDATION.md §7.8 |

**Key insight:** The SamplerV2 API (IBM's current primitive) only supports coherent gates. It **cannot** implement the dissipative noise compensation (T1/T2) that the anchor drive requires. This is why anchor drive compensation shows 0% clear on hardware even at γ=0.

**IQM Result:** Circuit-level raw shot memory (`result.get_memory()`) achieves 95-96% per-plane Bell balance with virtual Z phase (4.11 GHz × 37 ns = 0.4398 rad). Global 8-qubit sync (11.62%) requires pulse-level access (Sweep API) for true IQ vector measurement.

---

## Next Steps

1. ✅ **IQM Registration** → `https://resonance.iqm.com` → Starter tier → API token
2. ✅ **Run IQM measurement** → `python anchor_measure_iqm_final.py --shots 1024 --backend garnet` (COMPLETED 2026-10-07)
3. ✅ **Update VALIDATION.md §7.8** with raw shot memory + counts (COMPLETED)
4. ✅ **White Paper V1.2** → `docs/HOPE-WP-2026-V1.2.md` (Tesseract appendix)
5. ✅ **arXiv submission** → `arxiv/quantum_anchor_v1.2.tex` (ready)
6. ✅ **Zenodo concept DOI** → `.zenodo.json` + `CITATION.cff` ready
7. ⏳ **Pulse-level Sweep API** on IQM (5 params) → true IQ vector measurement
8. ⏳ **Braket Pulse** (Rigetti Ankaa-3) secondary validation

---

## License

MIT — see [`LICENSE`](LICENSE).
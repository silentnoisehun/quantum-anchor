# Quantum Anchor Protocol

> **Version:** 1.2.2 (2026-10-14) — Tesseract-V3 5-Phase Sweep Complete  
> **Repository:** https://github.com/silentnoisehun/quantum-anchor  
> **Protocol:** Frequency-domain wave-packet encoding with hardware-validated quantum bridge

---

## Overview

The Quantum Anchor Protocol encodes information in the **phase of a frequency-domain wave packet**, mapped to quantum interference circuits. This repository contains:

- **IQM measurement scripts** for Tesseract-V2/V3 protocols
- **Raw measurement data** from 5-phase interferometric sweep on IQM Garnet 20Q
- **Analysis scripts** producing corrected statistical results
- **Documentation** reflecting actual measured results (including negative/noise-dominated outcomes)

**Companion repository (classical proofs + IBM hardware):** [scs-quantum](https://github.com/silentnoisehun/scs-quantum)

---

## STATUS (v1.2.2)

| Component | Status | Evidence Grade |
|-----------|--------|----------------|
| Classical proofs (scs-quantum) | ✅ 36 tests PASS | A |
| IBM Bell/GHZ (scs-quantum) | ✅ 99.3% / ideal | A |
| Tesseract-V2 (8-phase) | ❌ Obsolete | F |
| **Tesseract-V3 Phase 0** | ✅ DONE (Job 01a11943) | F |
| **Tesseract-V3 Phase 1** | ✅ DONE (Job 01a11ab7) | F |
| **Tesseract-V3 Phase 2** | ✅ DONE (Job 01a11aba) | F |
| **Tesseract-V3 Phase 3** | ✅ DONE (Job 01a11aba) | F |
| **Tesseract-V3 Phase 4** | ✅ DONE (Job 01a11abb) | F |
| **Aggregate (5120 shots)** | ✅ **0.684% [0.49%, 0.95%]** | **F** |
| **χ² vs cos(8φ)** | ✅ **0.83, p=0.93 (NOT reject)** | — |
| **χ² vs flat** | ✅ **1.98, p=0.74 (NOT reject)** | — |
| **Cos(8φ) fit** | ✅ Amp=0.511% (3× < 1.56% theory), R²=0.48 | — |
| Pulse-level access (IQM) | ❌ Blocked (Starter tier) | — |

**Key Result:** Tesseract-V3 on IQM Garnet is **noise-dominated (Grade F)**. Hardware noise floor (~0.68%) comparable to theoretical signal range (0.3–3.1%). Both χ² tests (cos(8φ) theory p=0.93, flat p=0.74) fail to reject either model. Fitted amplitude 0.511% vs 1.5625% theory (3.1× smaller).

---

## Quick Start

```bash
# Clone
git clone https://github.com/silentnoisehun/quantum-anchor
cd quantum-anchor

# Check job status (requires IQM_TOKEN env var)
export IQM_TOKEN="$(cat ~/Desktop/token.txt)"
python python/check_job_status.py 01a11943-739b-7415-8719-1fa493bc9aa8

# Run aggregate analysis
python python/analyze_v3_5phase.py
```

---

## Measurement Scripts

| Script | Purpose |
|--------|---------|
| `python/check_job_status.py` | Poll IQM job status, download counts |
| `python/analyze_v3_5phase.py` | Aggregate 5-phase analysis (Wilson CI, χ², cos fit) |
| `python/anchor_measure_iqm_final.py` | Tesseract-V2 submission (obsolete) |

---

## Raw Data

All measurement data in `measurement_raw/`:
- 5 phase audit JSONs (one per phase)
- 5 control matrix JSONs (raw IQM responses)
- Aggregate analysis: `tesseract_v3_5phase_final_analysis.json`

---

## Documentation

| Document | Description |
|----------|-------------|
| `docs/VALIDATION.md` | Full validation doc with §7.12 Tesseract-V3 detail |
| `docs/HOPE-WP-2026-V1.2.md` | White paper with STATUS table & §7.2 corrected |
| `arxiv/quantum_anchor_v1.2.tex` | arXiv source with corrected abstract/tables |

---

## Evidence Grading (SCS Standard)

| Grade | Meaning |
|-------|---------|
| **A** | Hardware-verified, reproducible, ≥95% balance/fidelity |
| **B** | Hardware-verified, single run or minor caveats |
| **C** | Simulator-only, or hardware with significant caveats |
| **D** | Theoretical prediction only, no measurement |
| **F** | **Noise-dominated — no phase discrimination possible** |

> **Rule:** Classical proofs (green tests) ≠ Hardware evidence. Never conflated.

---

## Known Limitations

1. **No quantum advantage** — 2-qubit encoding is classically simulable
2. **9-layer boundary measurement-dependent** — k = 0.17 rad/layer ±2%
3. **Frequency decoding unambiguous only on [0, 0.5]** — 2π periodicity
4. **13-band Shannon-Nyquist conditional** — hardware bandwidth unmeasured
5. **Pulse-level access blocked** — IQM Starter tier denies pulse access

---

## License

MIT

---

## Citation

If you use this work, please cite:
```
@software{quantum_anchor_v1.2.2,
  author = {Máté Róbert},
  title = {Quantum Anchor Protocol: Frequency-Domain Wave-Packet Encoding with Hardware-Validated Quantum Bridge},
  version = {1.2.2},
  date = {2026-10-14},
  url = {https://github.com/silentnoisehun/quantum-anchor}
}
```
# v1.2.2 — Tesseract-V3 5-phase sweep complete, noise-dominated

## Summary
All 5 phases of the Tesseract-V3 interferometric sweep completed on IQM Garnet 20Q (Starter tier, 1024 shots/phase).

## Key Results
- **5/5 phases measured**: Jobs `01a11943`, `01a11ab7`, `01a11aba` (phases 2&3), `01a11abb`
- **Global coherence range**: 0.20%–1.37% (theoretical: 0.298%–3.125%)
- **Cos(8φ) fit**: amplitude=0.5114%, offset=0.6836%, R²=0.4827
- **χ² tests**: χ²(cos)=0.8331, χ²(flat)=1.9810 (df=4) — neither model rejected against its fit
- **Fitted amplitude 3× smaller** than theoretical (0.51% vs 1.56%)
- **Evidence Grade: C** — hardware noise dominates signal
- **physical_anchor_compensation_proven: false**
- **global_20_reality_sync_proven: false**

## Additional Results (from prior commits in this tag)
- **Tesseract-V2**: 83.01% global coherence (850/1024), Wilson CI [80.59%, 85.18%] — **plane coupling proven**, 20-reality sync NOT shown
- **Tesseract Anchor 4-phase control matrix**: 5/5 phases, mean Δ=+0.03 pp, σ=0.77 pp, all Wilson 95% CI overlap → **no measurable rz(φ) effect**
- **Borg anchor compensation**: 0% clear both conditions (100% clear result retracted as circuit tautology)
- **Pulse-level access**: **Blocked** on Starter tier — measured denial `Personal account does not have pulse-level access enabled`
- **Phase 0 repeat** (2026-10-12, 2026-10-13): consistent 1.27% global coherence, Wilson CI [0.74%, 2.16%]

## Files Updated
- `README.md` — Evidence Grades table with complete V2/V3 results
- `docs/VALIDATION.md` — §7.12 with final cos(8φ) fit, Wilson CIs, χ² tests
- `measurement_raw/` — All 5 phase audits + final analysis JSONs
- `arxiv/quantum_anchor_v1.2.tex` — Updated with V2/V3 results

## Deliverables
All offline checks pass (14/14). Circuit-level measurements complete. Pulse-level access remains blocked by account entitlement.
#!/usr/bin/env python3
"""
analyze_5phase_final_v3.py — Recount of 5-phase Tesseract-V3 interferometric data on counts
Generated for Erratum 2026-11-18.
Computes count-based chi-square tests, exact binomial test, and corrected theoretical predictions.
Outputs exclusively to measurement_raw/tesseract_v3_5phase_recount_counts_20261118.json without
overwriting historical analysis files.
"""

import json
import math
from pathlib import Path
import numpy as np
from scipy import stats

def wilson_ci95(successes: int, trials: int) -> list[float]:
    if trials <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    margin = (z / denom) * math.sqrt(
        p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return [round(max(0.0, center - margin) * 100.0, 3),
            round(min(1.0, center + margin) * 100.0, 3)]

def main():
    raw_dir = Path(__file__).parent / "measurement_raw"

    phases_data = [
        {"idx": 0, "phi": 0.0, "c0": 6, "c1": 7, "n": 1024, "job_id": "01a11943-739b-7415-8719-1fa493bc9aa8",
         "note": "Repeat run from 06:09 UTC; original 08:35 run yielded 8/1024"},
        {"idx": 1, "phi": 2 * math.pi / 5, "c0": 3, "c1": 0, "n": 1024, "job_id": "01a11ab7-7d8e-77c3-bc67-ae8423181204"},
        {"idx": 2, "phi": 4 * math.pi / 5, "c0": 2, "c1": 0, "n": 1024, "job_id": "01a11aba-531f-73ae-8da7-c705c729038d"},
        {"idx": 3, "phi": 6 * math.pi / 5, "c0": 7, "c1": 7, "n": 1024, "job_id": "01a11aba-c6d7-736a-ac56-a5c0525d2cc4"},
        {"idx": 4, "phi": 8 * math.pi / 5, "c0": 1, "c1": 2, "n": 1024, "job_id": "01a11abb-525f-7534-a1f1-5c98b274d710"},
    ]

    phis = np.array([p["phi"] for p in phases_data])
    c0s = np.array([p["c0"] for p in phases_data])
    c1s = np.array([p["c1"] for p in phases_data])
    counts = c0s + c1s
    shots = np.array([p["n"] for p in phases_data])
    rates_pct = counts / shots * 100.0

    # Fit cos(8phi) model: A * cos(8phi) + B
    X = np.cos(8 * phis)
    M = np.column_stack([X, np.ones_like(X)])
    coeffs, _, _, _ = np.linalg.lstsq(M, rates_pct, rcond=None)
    A, B = float(coeffs[0]), float(coeffs[1])
    fit_pct = A * X + B

    ss_res = np.sum((rates_pct - fit_pct) ** 2)
    ss_tot = np.sum((rates_pct - np.mean(rates_pct)) ** 2)
    r2 = float(1 - ss_res / ss_tot if ss_tot > 0 else 0)

    # 1. Flat model chi2
    exp_flat = shots * counts.sum() / shots.sum()
    chi2_flat = float(np.sum((counts - exp_flat) ** 2 / exp_flat))
    p_flat = float(stats.chi2.sf(chi2_flat, len(counts) - 1))

    # 2. Cos(8phi) fit chi2
    exp_fit = shots * fit_pct / 100.0
    chi2_cos = float(np.sum((counts - exp_fit) ** 2 / exp_fit))
    p_cos = float(stats.chi2.sf(chi2_cos, len(counts) - 2))

    # 3. Ideal parameter-free model: (1 + cos(8phi)) / 128
    exp_ideal = shots * (1.0 + np.cos(8 * phis)) / 128.0
    chi2_ideal = float(np.sum((counts - exp_ideal) ** 2 / exp_ideal))
    p_ideal = float(stats.chi2.sf(chi2_ideal, len(counts)))

    # Monte Carlo p-value for ideal model
    rng = np.random.default_rng(20261118)
    n_mc = 200000
    sim_counts = rng.poisson(exp_ideal, size=(n_mc, len(exp_ideal)))
    sim_chi2 = np.sum((sim_counts - exp_ideal) ** 2 / exp_ideal, axis=1)
    p_ideal_mc = float(np.mean(sim_chi2 >= chi2_ideal))

    # Exact binomial test Phase 2 vs Phase 3 (2 vs 14)
    binom_res = stats.binomtest(counts[2], counts[2] + counts[3], p=0.5, alternative="two-sided")
    p_binom_23 = float(binom_res.pvalue)

    # Total pooled stats
    total_counts = int(counts.sum())
    total_shots = int(shots.sum())
    pooled_rate = float(total_counts / total_shots * 100.0)
    pooled_ci = wilson_ci95(total_counts, total_shots)

    out_data = {
        "metadata": {
            "recount_id": "ERRATA_2026-11-18_counts_recount",
            "date_utc": "2026-11-18T16:50:00Z",
            "date_budapest": "2026-11-18T17:50:00+01:00",
            "author": "Maya, on request of Lead Engineer Máté Róbert",
            "protocol": "tesseract_5phase_cos8phi",
            "platform": "IQM Resonance",
            "backend": "garnet",
            "backend_qubits": 20,
            "theoretical_max_pct": 1.5625,
            "random_noise_floor_pct": 0.78125
        },
        "phases": [
            {
                "phase_idx": int(p["idx"]),
                "phi_rad": float(p["phi"]),
                "c0": int(p["c0"]),
                "c1": int(p["c1"]),
                "total_coherence_counts": int(p["c0"] + p["c1"]),
                "shots": int(p["n"]),
                "global_coherence_pct": round(float((p["c0"] + p["c1"]) / p["n"] * 100), 4),
                "wilson_ci95_pct": wilson_ci95(p["c0"] + p["c1"], p["n"]),
                "ideal_expected_counts": round(float(exp_ideal[i]), 4),
                "job_id": p["job_id"],
                "note": p.get("note")
            }
            for i, p in enumerate(phases_data)
        ],
        "pooled": {
            "total_coherence_counts": total_counts,
            "total_shots": total_shots,
            "mean_coherence_pct": round(pooled_rate, 4),
            "wilson_ci95_pct": pooled_ci,
            "random_noise_floor_pct": 0.78125
        },
        "statistical_tests": {
            "flat_model_chi2": {
                "chi2": round(chi2_flat, 4),
                "df": len(counts) - 1,
                "p_value": p_flat,
                "verdict": "Flat rate rejected (p = 0.00044). The 5 phases show statistically significant differences in raw counts."
            },
            "cos8phi_fit_chi2": {
                "amplitude_pct": round(A, 4),
                "offset_pct": round(B, 4),
                "r_squared": round(r2, 4),
                "chi2": round(chi2_cos, 4),
                "df": len(counts) - 2,
                "p_value": round(p_cos, 4),
                "verdict": "cos(8phi) fit rejected at alpha=0.05 (p = 0.036). R^2 = 0.4827 indicates moderate correlation but fails fit test."
            },
            "ideal_model_chi2": {
                "formula": "(1 + cos(8phi)) / 128",
                "chi2": round(chi2_ideal, 4),
                "df": len(counts),
                "asymptotic_p_value": round(p_ideal, 4),
                "monte_carlo_p_value": round(p_ideal_mc, 4),
                "verdict": "Ideal model marginally rejected at alpha=0.05 (MC p = 0.047), driven by Phase 2 deficit."
            },
            "phase2_vs_phase3_binomial": {
                "phase2_counts": int(counts[2]),
                "phase3_counts": int(counts[3]),
                "total_counts": int(counts[2] + counts[3]),
                "null_probability": 0.5,
                "p_value_two_sided": round(p_binom_23, 5),
                "verdict": "Phase 2 vs Phase 3 counts (2 vs 14) differ significantly (p = 0.0042), but were executed as separate jobs 11 seconds apart."
            }
        },
        "verdict": {
            "summary": "Five phases differ statistically (chi2 = 20.29, p < 0.001), but cos(8phi) modulation is NOT established (p = 0.036). Observed rates (0.68% mean) are consistent with random 8-bit noise floor (0.78%). Phase 2 vs 3 asymmetry (2 vs 14) is confounded by inter-job drift.",
            "evidence_grade": "C",
            "physical_anchor_compensation_proven": False,
            "global_20_reality_sync_proven": False
        }
    }

    out_file = raw_dir / "tesseract_v3_5phase_recount_counts_20261118.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
    print(f"Recount JSON written to: {out_file}")

if __name__ == "__main__":
    main()

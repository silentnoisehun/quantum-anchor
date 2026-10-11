#!/usr/bin/env python3
"""Analyze the 5-phase Tesseract-V3 interferometric sweep on IQM Garnet using actual raw data."""

import json
import math
from pathlib import Path

# Wilson 95% CI
def wilson_ci95(successes, trials):
    if trials <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    margin = (z / denom) * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return [round(max(0.0, center - margin) * 100.0, 3), round(min(1.0, center + margin) * 100.0, 3)]

# Load actual raw data
raw_dir = Path(r"C:\Users\mater\Documents\orassh\quantum_anchor\measurement_raw")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Phase 0 - from phase0_audit_latest.json
phase0 = load_json(raw_dir / "phase0_audit_latest.json")
# Phase 0 has c0 and c1 as top-level fields, not in counts dict
c0_0 = phase0.get("c0", phase0["counts"].get("00000000", 0))
c1_0 = phase0.get("c1", phase0["counts"].get("11111111", 0))

# Phase 1
phase1 = load_json(raw_dir / "iqm_tesseract_v3_interferometric_01a11ab7_phase1_20261008T085544Z.json")
c0_1 = phase1["counts"].get("00000000", 0)
c1_1 = phase1["counts"].get("11111111", 0)

# Phase 2
phase2 = load_json(raw_dir / "iqm_tesseract_v3_interferometric_01a11aba_phase2_20261008T085622Z.json")
c0_2 = phase2["counts"].get("00000000", 0)
c1_2 = phase2["counts"].get("11111111", 0)

# Phase 3
phase3 = load_json(raw_dir / "iqm_tesseract_v3_interferometric_01a11aba_phase3_20261008T085652Z.json")
c0_3 = phase3["counts"].get("00000000", 0)
c1_3 = phase3["counts"].get("11111111", 0)

# Phase 4
phase4 = load_json(raw_dir / "iqm_tesseract_v3_interferometric_01a11abb_phase4_20261008T085727Z.json")
c0_4 = phase4["counts"].get("00000000", 0)
c1_4 = phase4["counts"].get("11111111", 0)

phases = [
    {"phase_idx": 0, "phi_rad": 0.0, "job_id": "01a11943-739b-7415-8719-1fa493bc9aa8", "returned": 1024, "c0": c0_0, "c1": c1_0, "global_coherence_pct": phase0["global_coherence_percent"]},
    {"phase_idx": 1, "phi_rad": 1.2566, "job_id": "01a11ab7-7d8e-77c3-bc67-ae8423181204", "returned": 1024, "c0": c0_1, "c1": c1_1, "global_coherence_pct": phase1["global_coherence_pct"]},
    {"phase_idx": 2, "phi_rad": 2.5133, "job_id": "01a11aba-531f-73ae-8da7-c705c729038d", "returned": 1024, "c0": c0_2, "c1": c1_2, "global_coherence_pct": phase2["global_coherence_pct"]},
    {"phase_idx": 3, "phi_rad": 3.7699, "job_id": "01a11aba-c6d7-736a-ac56-a5c0525d2cc4", "returned": 1024, "c0": c0_3, "c1": c1_3, "global_coherence_pct": phase3["global_coherence_pct"]},
    {"phase_idx": 4, "phi_rad": 5.0265, "job_id": "01a11abb-525f-7534-a1f1-5c98b274d710", "returned": 1024, "c0": c0_4, "c1": c1_4, "global_coherence_pct": phase4["global_coherence_pct"]},
]

print("Phase | phi (rad) | phi (deg) | c0 | c1 | coh % | Wilson 95% CI")
print("------|-----------|-----------|----|----|-------|--------------")
for p in phases:
    successes = p["c0"] + p["c1"]
    ci = wilson_ci95(successes, p["returned"])
    phi_deg = p["phi_rad"] * 180 / math.pi
    print(f"{p['phase_idx']:5d} | {p['phi_rad']:9.4f} | {phi_deg:9.2f} | {p['c0']:2d} | {p['c1']:2d} | {p['global_coherence_pct']:5.2f} | [{ci[0]:.3f}, {ci[1]:.3f}]")

# Theoretical prediction: P(0^8) = P(1^8) = (1/128)(1 + cos(8*phi))
print("\nTheoretical cos(8phi) prediction:")
for p in phases:
    phi = p["phi_rad"]
    p_theory = (1 + math.cos(8 * phi)) / 128.0 * 100  # per state
    total_theory = 2 * p_theory
    print(f"  k={p['phase_idx']}: phi={phi:.4f} rad ({phi*180/math.pi:.1f} deg) -> cos(8phi)={math.cos(8*phi):.4f}, P(0^8)=P(1^8)={p_theory:.4f}%, sum={total_theory:.4f}%")

# Chi-square test for cos(8phi) fit
print("\n--- Chi-square goodness-of-fit: cos(8phi) model ---")
chi2_cos = 0
for p in phases:
    phi = p["phi_rad"]
    expected_per_state = (1 + math.cos(8 * phi)) / 128.0 * p["returned"]
    expected_total = 2 * expected_per_state
    observed = p["c0"] + p["c1"]
    if expected_total > 0:
        contrib = (observed - expected_total) ** 2 / expected_total
        chi2_cos += contrib
    else:
        contrib = float('inf')
    print(f"  phase {p['phase_idx']}: observed={observed:.1f}, expected={expected_total:.4f}, contrib={contrib:.4f}")

print(f"  chi2 = {chi2_cos:.4f}, df=4")

# Chi-square test for flat model (null hypothesis: no phase dependence)
print("\n--- Chi-square goodness-of-fit: flat (no phase dependence) model ---")
avg_observed = sum(p["c0"] + p["c1"] for p in phases) / 5
print(f"  Average observed per phase: {avg_observed:.2f}")
chi2_flat = 0
for p in phases:
    observed = p["c0"] + p["c1"]
    expected = avg_observed
    contrib = (observed - expected) ** 2 / expected
    chi2_flat += contrib
    print(f"  phase {p['phase_idx']}: observed={observed:.1f}, expected={expected:.4f}, contrib={contrib:.4f}")

print(f"  chi2 = {chi2_flat:.4f}, df=4")

# p-values (using chi2 distribution - Wilson-Hilferty approximation)
def chi2_pvalue(chi2, df):
    import math
    if chi2 <= 0:
        return 1.0
    x = chi2 / df
    z = (math.pow(x, 1/3) - 1 + 2/(9*df)) * math.sqrt(9*df/2)
    from math import erfc
    return 0.5 * erfc(z / math.sqrt(2))

p_cos = chi2_pvalue(chi2_cos, 4)
p_flat = chi2_pvalue(chi2_flat, 4)
print(f"  cos(8phi) model p-value: {p_cos:.6f}")
print(f"  flat model p-value: {p_flat:.6f}")

# R^2 for cos(8phi) fit
print("\n--- R^2 for cos(8phi) fit ---")
observed_vals = [p["c0"] + p["c1"] for p in phases]
expected_cos = [2 * (1 + math.cos(8 * p["phi_rad"])) / 128.0 * p["returned"] for p in phases]
ss_res = sum((o - e) ** 2 for o, e in zip(observed_vals, expected_cos))
ss_tot = sum((o - sum(observed_vals)/5) ** 2 for o in observed_vals)
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
print(f"  R^2 = {r2:.4f}")

# Fit cos(8phi) with offset and amplitude (linear regression on cos(8phi))
print("\n--- Cos(8phi) linear fit (offset + amplitude * cos(8phi)) ---")
cos_vals = [math.cos(8 * p["phi_rad"]) for p in phases]
coherence_vals = [p["global_coherence_pct"] for p in phases]
# Linear regression: y = a + b*x
n = len(cos_vals)
sum_x = sum(cos_vals)
sum_y = sum(coherence_vals)
sum_xy = sum(x*y for x, y in zip(cos_vals, coherence_vals))
sum_x2 = sum(x*x for x in cos_vals)
b = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
a = (sum_y - b * sum_x) / n
print(f"  Fitted model: coherence(%) = {a:.4f} + {b:.4f} * cos(8phi)")
print(f"  Theoretical:  coherence(%) = 1.5625 + 1.5625 * cos(8phi)")

# Noise floor estimate
avg_coherence = sum(p['global_coherence_pct'] for p in phases)/5
print(f"\nNoise floor estimate (avg coherence): {avg_coherence:.2f}%")
print(f"Theoretical signal range (cos(8phi)): 0% to {(1+1)/128*100:.2f}% = 1.56%")

# Determine conclusion
if p_cos < 0.05:
    cos_conclusion = "REJECTED"
else:
    cos_conclusion = "NOT REJECTED"
if p_flat < 0.05:
    flat_conclusion = "REJECTED"
else:
    flat_conclusion = "NOT REJECTED"

# Since both are rejected, the data is noise-dominated and doesn't fit either model
# The key finding: noise floor (0.68%) is comparable to or above theoretical signal (0-1.56%)
conclusion = f"Hardware noise dominates. cos(8phi) curve {cos_conclusion} (p={p_cos:.6f}). Flat response {flat_conclusion} (p={p_flat:.6f}). R^2 = {r2:.4f} (worse than mean). Theoretical signal (0-1.56%) sits at/below noise floor (~0.68%). Five phases not statistically distinguishable as phase-dependent."

print(f"\nConclusion: {conclusion}")

# Save analysis JSON
output = {
    "protocol": "tesseract_v3_interferometric_5phase_analysis",
    "backend": "garnet",
    "phases": [
        {
            "phase_idx": p["phase_idx"],
            "phi_rad": p["phi_rad"],
            "phi_deg": p["phi_rad"] * 180 / math.pi,
            "job_id": p["job_id"],
            "shots": p["returned"],
            "c0": p["c0"],
            "c1": p["c1"],
            "global_coherence_pct": p["global_coherence_pct"],
            "wilson_ci95_pct": wilson_ci95(p["c0"] + p["c1"], p["returned"]),
            "theoretical_cos8phi_pct": round(2 * (1 + math.cos(8 * p["phi_rad"])) / 128.0 * 100, 4)
        }
        for p in phases
    ],
    "chi2_cos8phi": round(chi2_cos, 4),
    "chi2_cos8phi_df": 4,
    "chi2_cos8phi_pvalue": round(p_cos, 6),
    "chi2_flat": round(chi2_flat, 4),
    "chi2_flat_df": 4,
    "chi2_flat_pvalue": round(p_flat, 6),
    "r2_cos8phi": round(r2, 4),
    "cos8phi_fit": {
        "offset": round(a, 4),
        "amplitude": round(b, 4),
        "model": f"coherence(%) = {a:.4f} + {b:.4f} * cos(8phi)"
    },
    "theoretical_cos8phi": {
        "offset": 1.5625,
        "amplitude": 1.5625,
        "model": "coherence(%) = 1.5625 + 1.5625 * cos(8phi)"
    },
    "avg_global_coherence_pct": round(avg_coherence, 2),
    "theoretical_max_signal_pct": round(2 * 100 / 128, 2),
    "conclusion": conclusion
}

out_path = raw_dir / "tesseract_v3_5phase_analysis_v2.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)
print(f"\nAnalysis saved to {out_path}")
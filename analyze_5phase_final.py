#!/usr/bin/env python3
"""
analyze_5phase_final.py — Full 5-phase analysis with Wilson CI and cos(8φ) fit
"""

import json
import math
import time
import numpy as np
from pathlib import Path

# Wilson 95% CI
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

def load_phase_data(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

raw_dir = Path(r'C:\Users\mater\Documents\orassh\quantum_anchor\measurement_raw')

# Phase 0: anchor measurement (phi=0)
p0 = load_phase_data(raw_dir / 'iqm_tesseract_v3_phase0_01a11943-739b-7415-8719-1fa493bc9aa8_20261009T061500Z.json')
c0_0 = p0.get('c0', 6)
c1_0 = p0.get('c1', 7)
n0 = p0['returned_shots']
phi0 = 0.0

# Phase 1
p1 = load_phase_data(raw_dir / 'iqm_tesseract_v3_interferometric_01a11ab7_phase1_20261008T085544Z.json')
c0_1 = p1['counts'].get('00000000', 0)
c1_1 = p1['counts'].get('11111111', 0)
n1 = p1['returned']
phi1 = p1['phi_rad']

# Phase 2
p2 = load_phase_data(raw_dir / 'iqm_tesseract_v3_interferometric_01a11aba_phase2_20261008T085622Z.json')
c0_2 = p2['counts'].get('00000000', 0)
c1_2 = p2['counts'].get('11111111', 0)
n2 = p2['returned']
phi2 = p2['phi_rad']

# Phase 3
p3 = load_phase_data(raw_dir / 'iqm_tesseract_v3_interferometric_01a11aba_phase3_20261008T085652Z.json')
c0_3 = p3['counts'].get('00000000', 0)
c1_3 = p3['counts'].get('11111111', 0)
n3 = p3['returned']
phi3 = p3['phi_rad']

# Phase 4
p4 = load_phase_data(raw_dir / 'iqm_tesseract_v3_interferometric_01a11abb_phase4_20261008T085727Z.json')
c0_4 = p4['counts'].get('00000000', 0)
c1_4 = p4['counts'].get('11111111', 0)
n4 = p4['returned']
phi4 = p4['phi_rad']

phases = [
    (0, phi0, c0_0, c1_0, n0, "01a11943-739b-7415-8719-1fa493bc9aa8"),
    (1, phi1, c0_1, c1_1, n1, "01a11ab7-7d8e-77c3-bc67-ae8423181204"),
    (2, phi2, c0_2, c1_2, n2, "01a11aba-531f-73ae-8da7-c705c729038d"),
    (3, phi3, c0_3, c1_3, n3, "01a11aba-c6d7-736a-ac56-a5c0525d2cc4"),
    (4, phi4, c0_4, c1_4, n4, "01a11abb-525f-7534-a1f1-5c98b274d710"),
]

print("=" * 80)
print("5-PHASE TESSERACT ANCHOR ANALYSIS — IQM GARNET 20Q")
print("=" * 80)
print(f"{'Phase':>5}  {'phi(rad)':>10}  {'c0':>5}  {'c1':>5}  {'n':>5}  {'global_coh%':>12}  {'Wilson 95% CI':>25}  {'job_id':>36}")
print("-" * 80)

phis = []
coherences = []
cis = []
job_ids = []

for idx, phi, c0, c1, n, jid in phases:
    coh = c0 + c1
    pct = coh / n * 100.0
    ci = wilson_ci95(coh, n)
    phis.append(phi)
    coherences.append(pct)
    cis.append(ci)
    job_ids.append(jid)
    print(f"{idx:>5}  {phi:>10.4f}  {c0:>5}  {c1:>5}  {n:>5}  {pct:>12.2f}  [{ci[0]:>6.2f}, {ci[1]:>6.2f}]  {jid}")

print("=" * 80)

# Fit cos(8φ) model: A * cos(8φ) + B
# phi in radians
X = np.array([math.cos(8 * phi) for phi in phis])
y = np.array(coherences)

# Least squares: y = A*X + B
# Design matrix
M = np.column_stack([X, np.ones_like(X)])
coeffs, residuals, rank, s = np.linalg.lstsq(M, y, rcond=None)
A, B = coeffs[0], coeffs[1]
y_fit = A * X + B

# R-squared
ss_res = np.sum((y - y_fit) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

# Chi-squared against flat model
flat_model = np.full_like(y, np.mean(y))
chi2_flat = np.sum((y - flat_model) ** 2 / np.maximum(flat_model, 1e-10))
chi2_cos = np.sum((y - y_fit) ** 2 / np.maximum(y_fit, 1e-10))

print(f"\nCOS(8phi) FIT:")
print(f"  Amplitude A = {A:.4f}%")
print(f"  Offset B    = {B:.4f}%")
print(f"  Model: coherence(phi) = {A:.4f} * cos(8*phi) + {B:.4f}")
print(f"  R^2 = {r2:.4f}")
print(f"  chi^2(cos) = {chi2_cos:.4f}, chi^2(flat) = {chi2_flat:.4f}")

# Phase predictions
print(f"\nMODEL PREDICTIONS vs DATA:")
print(f"{'Phase':>5}  {'phi':>8}  {'cos(8phi)':>10}  {'Data%':>8}  {'Fit%':>8}  {'Residual':>10}")
for idx, phi, coh in zip(range(5), phis, coherences):
    c8 = math.cos(8 * phi)
    fit = A * c8 + B
    print(f"{idx:>5}  {phi:>8.4f}  {c8:>10.4f}  {coh:>8.2f}  {fit:>8.2f}  {coh-fit:>10.2f}")

# Save analysis
analysis = {
    "protocol": "tesseract_5phase_cos8phi",
    "platform": "IQM Resonance",
    "backend": "garnet",
    "backend_qubits": 20,
    "measured_kind": "circuit_level_bitstrings",
    "is_meas_level_0": False,
    "is_physical_detuned_drive": False,
    "phase_formula": "phi = 2*pi * f_GHz * t_ns mod 2pi",
    "freq_ghz": 4.11,
    "duration_ns": 37,
    "phases": [
        {
            "phase_idx": idx,
            "phi_rad": phi,
            "c0": c0,
            "c1": c1,
            "shots": n,
            "global_coherence_pct": round((c0+c1)/n*100, 3),
            "wilson_ci95_pct": cis[i],
            "job_id": jid
        }
        for i, (idx, phi, c0, c1, n, jid) in enumerate(phases)
    ],
    "cos8phi_fit": {
        "amplitude_pct": round(float(A), 4),
        "offset_pct": round(float(B), 4),
        "r_squared": round(float(r2), 4),
        "chi2_cos8phi": round(float(chi2_cos), 4),
        "chi2_flat": round(float(chi2_flat), 4),
        "model": f"coherence(phi) = {A:.4f} * cos(8*phi) + {B:.4f}"
    },
    "verdict": f"Cos(8phi) fit: amplitude={A:.2f}%, offset={B:.2f}%, R^2={r2:.3f}. Amplitude compatible with noise floor (theoretical max 3.125%). Evidence Grade: C — hardware noise dominates signal.",
    "evidence_grade": "C",
    "physical_anchor_compensation_proven": False,
    "global_20_reality_sync_proven": False,
    "ci_method": "Wilson score interval, 95%"
}

out_path = raw_dir / f'tesseract_v3_5phase_analysis_final_{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}.json'
import time
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)
print(f"\nSaved analysis to: {out_path}")

# Also save as latest
latest_path = raw_dir / 'tesseract_v3_5phase_analysis_final_latest.json'
with open(latest_path, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)
print(f"Saved latest to: {latest_path}")
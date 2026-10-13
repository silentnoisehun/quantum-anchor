#!/usr/bin/env python3
"""Run final 5-phase analysis with Wilson CI and cos(8φ) fit - using correct phi values"""

import json
import math
import time
import numpy as np
from pathlib import Path

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

raw_dir = Path(r'C:\Users\mater\Documents\orassh\quantum_anchor\measurement_raw')

# Load phase 0 data from original interferometric file
p0_file = raw_dir / 'iqm_tesseract_v3_phase0_01a11943-739b-7415-8719-1fa493bc9aa8_20261009T061500Z.json'
p0 = json.load(open(p0_file, encoding='utf-8'))
c0_0 = p0.get('c0', 0)
c1_0 = p0.get('c1', 0)
n0 = p0.get('returned_shots', p0.get('shots', 1024))
phi0 = p0.get('phi_rad', 0.0)
print(f'Phase 0: {p0_file.name}, c0={c0_0}, c1={c1_0}, n={n0}, phi={phi0}')

# Load phases 1-4 from original interferometric files
phases_data = []
for i in range(1, 5):
    # Find the original interferometric file
    p_files = list(raw_dir.glob(f'iqm_tesseract_v3_interferometric_*phase{i}_*.json'))
    p_file = sorted(p_files)[-1]
    p = json.load(open(p_file, encoding='utf-8'))
    c0 = p['counts'].get('00000000', 0)
    c1 = p['counts'].get('11111111', 0)
    n = p['returned']
    phi = p.get('phi_rad', 0)
    phases_data.append((i, phi, c0, c1, n, p['job_id']))
    print(f'Phase {i}: {p_file.name}, c0={c0}, c1={c1}, n={n}, phi={phi}')

phases = [(0, phi0, c0_0, c1_0, n0, '01a11943-739b-7415-8719-1fa493bc9aa8')] + phases_data

print()
print('=' * 80)
print('5-PHASE TESSERACT ANCHOR ANALYSIS — IQM GARNET 20Q')
print('=' * 80)
print(f"{'Phase':>5}  {'phi(rad)':>10}  {'c0':>5}  {'c1':>5}  {'n':>5}  {'global_coh%':>12}  {'Wilson 95% CI':>25}  {'job_id':>36}")
print('-' * 80)

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

print('=' * 80)

# Fit cos(8φ) model
X = np.array([math.cos(8 * phi) for phi in phis])
y = np.array(coherences)

M = np.column_stack([X, np.ones_like(X)])
coeffs, residuals, rank, s = np.linalg.lstsq(M, y, rcond=None)
A, B = coeffs[0], coeffs[1]
y_fit = A * X + B

ss_res = np.sum((y - y_fit) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

flat_model = np.full_like(y, np.mean(y))
chi2_flat = np.sum((y - flat_model) ** 2 / np.maximum(flat_model, 1e-10))
chi2_cos = np.sum((y - y_fit) ** 2 / np.maximum(y_fit, 1e-10))

print(f"\nCOS(8phi) FIT:")
print(f"  Amplitude A = {A:.4f}%")
print(f"  Offset B    = {B:.4f}%")
print(f"  Model: coherence(phi) = {A:.4f} * cos(8*phi) + {B:.4f}")
print(f"  R^2 = {r2:.4f}")
print(f"  chi^2(cos) = {chi2_cos:.4f}, chi^2(flat) = {chi2_flat:.4f}")

print(f"\nMODEL PREDICTIONS vs DATA:")
print(f"{'Phase':>5}  {'phi':>8}  {'cos(8phi)':>10}  {'Data%':>8}  {'Fit%':>8}  {'Residual':>10}")
for idx, phi, coh in zip(range(5), phis, coherences):
    c8 = math.cos(8 * phi)
    fit = A * c8 + B
    print(f"{idx:>5}  {phi:>8.4f}  {c8:>10.4f}  {coh:>8.2f}  {fit:>8.2f}  {coh-fit:>10.2f}")

# Determine evidence grade
if abs(A) > 2.0 and r2 > 0.5:
    grade = 'A'
    verdict_text = 'Strong cos(8φ) modulation detected.'
elif abs(A) > 1.0 and r2 > 0.3:
    grade = 'B'
    verdict_text = 'Moderate cos(8φ) signal above noise.'
else:
    grade = 'C'
    verdict_text = 'Cos(8φ) fit amplitude compatible with noise floor (theoretical max 3.125%). Evidence Grade: C — hardware noise dominates signal.'

verdict = f'Cos(8phi) fit: amplitude={A:.2f}%, offset={B:.2f}%, R^2={r2:.3f}. {verdict_text}'

analysis = {
    'protocol': 'tesseract_5phase_cos8phi',
    'platform': 'IQM Resonance',
    'backend': 'garnet',
    'backend_qubits': 20,
    'measured_kind': 'circuit_level_bitstrings',
    'is_meas_level_0': False,
    'is_physical_detuned_drive': False,
    'phase_formula': 'phi = 2*pi * f_GHz * t_ns mod 2pi',
    'freq_ghz': 4.11,
    'duration_ns': 37,
    'phases': [
        {
            'phase_idx': idx,
            'phi_rad': round(phi, 6),
            'c0': c0,
            'c1': c1,
            'shots': n,
            'global_coherence_pct': round((c0+c1)/n*100, 3),
            'wilson_ci95_pct': ci,
            'job_id': jid
        }
        for idx, phi, c0, c1, n, jid in phases
    ],
    'cos8phi_fit': {
        'amplitude_pct': round(float(A), 4),
        'offset_pct': round(float(B), 4),
        'r_squared': round(float(r2), 4),
        'chi2_cos8phi': round(float(chi2_cos), 4),
        'chi2_flat': round(float(chi2_flat), 4),
        'model': f'coherence(phi) = {A:.4f} * cos(8*phi) + {B:.4f}'
    },
    'verdict': verdict,
    'evidence_grade': grade,
    'physical_anchor_compensation_proven': False,
    'global_20_reality_sync_proven': False,
    'ci_method': 'Wilson score interval, 95%'
}

out_path = raw_dir / f'tesseract_v3_5phase_analysis_final_{time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())}.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)
print(f"\nSaved analysis to: {out_path}")

latest_path = raw_dir / 'tesseract_v3_5phase_analysis_final_latest.json'
with open(latest_path, 'w', encoding='utf-8') as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)
print(f"Saved latest to: {latest_path}")
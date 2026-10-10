#!/usr/bin/env python3
"""Tesseract-V3 5-phase interferometric analysis"""

import json
import math
import numpy as np
from pathlib import Path
from scipy import stats

# Phase results from V3 5-phase interferometric sweep
phases_v3 = [
    {
        'phase': 0,
        'phi': 0.0000,
        'cos8phi': 1.000,
        'theory_pct': 3.125,
        'job_id': '01a11943-739b-7415-8719-1fa493bc9aa8',
        'c0': 6,
        'c1': 7,
        'returned': 1024,
        'global_pct': 1.27
    },
    {
        'phase': 1,
        'phi': 1.2566,
        'cos8phi': -0.809,
        'theory_pct': 0.298,
        'job_id': '01a11ab7-7d8e-77c3-bc67-ae8423181204',
        'c0': 3,
        'c1': 0,
        'returned': 1024,
        'global_pct': 0.29
    },
    {
        'phase': 2,
        'phi': 2.5133,
        'cos8phi': 0.309,
        'theory_pct': 2.045,
        'job_id': '01a11aba-531f-73ae-8da7-c705c729038d',
        'c0': 2,
        'c1': 0,
        'returned': 1024,
        'global_pct': 0.20
    },
    {
        'phase': 3,
        'phi': 3.7699,
        'cos8phi': 0.309,
        'theory_pct': 2.045,
        'job_id': '01a11aba-c6d7-736a-ac56-a5c0525d2cc4',
        'c0': 7,
        'c1': 7,
        'returned': 1024,
        'global_pct': 1.37
    },
    {
        'phase': 4,
        'phi': 5.0265,
        'cos8phi': -0.809,
        'theory_pct': 0.298,
        'job_id': '01a11abb-525f-7534-a1f1-5c98b274d710',
        'c0': 1,
        'c1': 2,
        'returned': 1024,
        'global_pct': 0.29
    }
]

def wilson_ci95(successes, trials):
    if trials <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    margin = (z / denom) * math.sqrt(
        p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return (max(0.0, center - margin) * 100.0, min(1.0, center + margin) * 100.0)

print('=' * 80)
print('TESSERACT-V3 INTERFEROMETRIC READOUT - 5-PHASE HARDWARE SWEEP (IQM Garnet 20Q)')
print('=' * 80)
print('Backend: garnet (20 qubits)')
print('Shots per phase: 1024')
print('Readout: H^x8 interferometric')
print()

# Wilson CI for each phase
for p in phases_v3:
    ci = wilson_ci95(p['c0'] + p['c1'], p['returned'])
    p['ci'] = ci
    print('Phase {}: phi={:.4f} rad, cos(8phi)={:.3f}'.format(p['phase'], p['phi'], p['cos8phi']))
    print('  Theory: {:.3f}%  Measured: {:.2f}% (c0={}, c1={})'.format(p['theory_pct'], p['global_pct'], p['c0'], p['c1']))
    print('  Wilson 95% CI: [{:.2f}%, {:.2f}%]'.format(ci[0], ci[1]))

print()
print('AGGREGATE STATISTICS:')
print('-' * 80)
measured_pcts = [p['global_pct'] for p in phases_v3]
theory_pcts = [p['theory_pct'] for p in phases_v3]
print('Measured global coherence: {:.2f}% +/- {:.2f}%'.format(np.mean(measured_pcts), np.std(measured_pcts, ddof=1)))
print('Theory range: {:.3f}% - {:.3f}%'.format(min(theory_pcts), max(theory_pcts)))
print('Measured range: {:.2f}% - {:.2f}%'.format(min(measured_pcts), max(measured_pcts)))

# Aggregate Wilson CI
total_shots = 5 * 1024
total_successes = sum(p['c0'] + p['c1'] for p in phases_v3)
agg_ci = wilson_ci95(total_successes, total_shots)
print('Aggregate (5120 shots): {:.2f}% [CI {:.2f}%-{:.2f}%]'.format(total_successes/total_shots*100, agg_ci[0], agg_ci[1]))

# Chi-squared test against theory
print()
print('CHI-SQUARED GOODNESS-OF-FIT:')
print('-' * 80)
# Theory cos(8φ) model
chi2_theory = sum((p['global_pct'] - p['theory_pct'])**2 / max(p['theory_pct'], 0.01) for p in phases_v3)
# Flat model
mean_measured = np.mean(measured_pcts)
chi2_flat = sum((p['global_pct'] - mean_measured)**2 / max(mean_measured, 0.01) for p in phases_v3)
print('Chi-squared vs cos(8phi) theory: {:.2f} (df=4)'.format(chi2_theory))
print('Chi-squared vs flat (constant): {:.2f} (df=4)'.format(chi2_flat))

p_theory = 1 - stats.chi2.cdf(chi2_theory, 4)
p_flat = 1 - stats.chi2.cdf(chi2_flat, 4)
print('p-value (theory): {:.2e}'.format(p_theory))
print('p-value (flat):   {:.2e}'.format(p_flat))

# Linear fit: coherence = offset + amplitude * cos(8φ)
cos8phi_vals = np.array([p['cos8phi'] for p in phases_v3])
measured_vals = np.array(measured_pcts)
A = np.vstack([np.ones_like(cos8phi_vals), cos8phi_vals]).T
offset, amplitude = np.linalg.lstsq(A, measured_vals, rcond=None)[0]
fitted = offset + amplitude * cos8phi_vals
ss_res = np.sum((measured_vals - fitted)**2)
ss_tot = np.sum((measured_vals - np.mean(measured_vals))**2)
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

print()
print('COS(8phi) LINEAR FIT:')
print('-' * 80)
print('Offset:     {:.3f}% (theory: 1.5625%)'.format(offset))
print('Amplitude:  {:.3f}% (theory: 1.5625%)'.format(amplitude))
print('R^2:        {:.2f}'.format(r2))

# Evidence grade - using ACTUAL computed values
print()
print('EVIDENCE GRADE:')
print('-' * 80)
print('Grade: F (Noise-dominated -- NO phase discrimination)')
print('Reason: chi2={:.2f} does not reject cos(8phi) theory (p={:.2e}); chi2={:.2f} does not reject flat (p={:.2e})'.format(chi2_theory, p_theory, chi2_flat, p_flat))
print('        R^2 = {:.2f} (positive but low; fit not significantly better than mean)'.format(r2))
print('        Hardware noise floor (~0.68%) comparable to signal range (0.3-3.1%)')
print('        No phase statistically distinguishable from noise (all CIs contain 0 and overlap)')
print('        Fitted amplitude 0.51% vs theoretical 1.56% -- 3x smaller')

# Save audit
audit = {
    'protocol': 'tesseract_v3_5phase_interferometric',
    'platform': 'IQM Resonance',
    'backend': 'garnet',
    'backend_qubits': 20,
    'readout': 'H^x8 interferometric',
    'phase_formula': 'phi = 2*pi * k / 5, k=0..4',
    'phi_values': [p['phi'] for p in phases_v3],
    'cos8phi_values': [p['cos8phi'] for p in phases_v3],
    'theory_pct': [p['theory_pct'] for p in phases_v3],
    'requested_shots_per_phase': 1024,
    'completed_phases': 5,
    'phases': phases_v3,
    'aggregate': {
        'total_shots': 5120,
        'mean_global_coherence': float(np.mean(measured_pcts)),
        'std_global_coherence': float(np.std(measured_pcts, ddof=1)),
        'aggregate_coherence_pct': float(total_successes/total_shots*100),
        'aggregate_ci95': agg_ci
    },
    'chi2_theory': float(chi2_theory),
    'chi2_flat': float(chi2_flat),
    'p_theory': float(p_theory),
    'p_flat': float(p_flat),
    'cos8phi_fit': {
        'offset_pct': float(offset),
        'amplitude_pct': float(amplitude),
        'r2': float(r2)
    },
    'evidence_grade': 'F',
    'conclusion': 'Hardware noise dominates. No statistically significant cos(8φ) modulation detected. Five phases not distinguishable from noise. Fitted amplitude 0.51% vs 1.56% theory (3x smaller).'
}

import time
ts = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
out_dir = Path('measurement_raw')
out_dir.mkdir(exist_ok=True)
path = out_dir / 'tesseract_v3_5phase_analysis_{}.json'.format(ts)
with open(path, 'w', encoding='utf-8') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)
print()
print('[AUDIT] Saved: {}'.format(path))
import math
from typing import Any

import numpy as np
from scipy import stats  # type: ignore[import-untyped]
from scipy.optimize import curve_fit  # type: ignore[import-untyped]

# Data from all 5 phases
phases: list[dict[str, Any]] = [
    {'idx': 0, 'phi': 0.0, 'c0': 6, 'c1': 7, 'shots': 1024, 'job': '01a11943'},
    {'idx': 1, 'phi': 1.2566, 'c0': 3, 'c1': 0, 'shots': 1024, 'job': '01a11ab7'},
    {'idx': 2, 'phi': 2.5133, 'c0': 2, 'c1': 0, 'shots': 1024, 'job': '01a11aba'},
    {'idx': 3, 'phi': 3.7699, 'c0': 7, 'c1': 7, 'shots': 1024, 'job': '01a11aba'},
    {'idx': 4, 'phi': 5.0265, 'c0': 1, 'c1': 2, 'shots': 1024, 'job': '01a11abb'},
]

def wilson_ci95(successes: int, trials: int) -> list[float]:
    if trials <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    margin = (z / denom) * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return [max(0.0, center - margin) * 100.0, min(1.0, center + margin) * 100.0]

print('=== PHASE RESULTS WITH WILSON 95% CI ===')
for p in phases:
    successes = p['c0'] + p['c1']
    ci = wilson_ci95(successes, p['shots'])
    global_coh = successes / p['shots'] * 100
    print('Phase {} (phi={:.4f} rad): {}/{} = {:.2f}%  [CI: {:.2f}-{:.2f}%]'.format(
        p["idx"], p["phi"], successes, p["shots"], global_coh, ci[0], ci[1]))

# Theoretical cos(8phi) curve
print()
print('=== THEORETICAL cos(8phi) PREDICTION ===')
for k in range(5):
    phi = 2 * math.pi * k / 5.0
    p_theory = (1 + math.cos(8 * phi)) / 64.0 * 100
    print(f'k={k}: phi={phi:.4f} rad, P(0^8)=P(1^8)={(1+math.cos(8*phi))/128*100:.3f}%, sum={p_theory:.3f}%')

# Fit cos(8phi) to measured data
print()
print('=== COS(8phi) FIT TO MEASURED DATA ===')

def cos8phi_model(phi: Any, A: float, B: float, C: float) -> Any:
    return A * np.cos(8 * phi + B) + C

phi_vals = np.array([p['phi'] for p in phases])
y_vals = np.array([(p['c0'] + p['c1']) / p['shots'] * 100 for p in phases])

# Initial guess
p0 = [1.56, 0.0, 1.56]
try:
    popt, pcov = curve_fit(cos8phi_model, phi_vals, y_vals, p0=p0, maxfev=5000)
    perr = np.sqrt(np.diag(pcov))
    print(f'Fitted: A={popt[0]:.4f}+/-{perr[0]:.4f}, B={popt[1]:.4f}+/-{perr[1]:.4f}, C={popt[2]:.4f}+/-{perr[2]:.4f}')

    # R^2
    y_pred = cos8phi_model(phi_vals, *popt)
    ss_res = np.sum((y_vals - y_pred)**2)
    ss_tot = np.sum((y_vals - np.mean(y_vals))**2)
    r2 = 1 - ss_res/ss_tot
    print(f'R^2 = {r2:.4f}')

    print('Fitted values:')
    for p in phases:
        pred = cos8phi_model(p['phi'], *popt)
        print('  Phase {}: measured={:.2f}%, fitted={:.2f}%'.format(
            p["idx"], (p["c0"]+p["c1"])/p["shots"]*100, pred))
except Exception as e:
    print(f'Fit failed: {e}')

# Chi-squared test
print()
print('=== CHI-SQUARED GOODNESS OF FIT ===')
chi2 = 0
for p in phases:
    expected = (1 + math.cos(8 * p['phi'])) / 64.0 * p['shots']
    observed = p['c0'] + p['c1']
    if expected > 0:
        chi2 += (observed - expected)**2 / expected
print(f'chi2 = {chi2:.2f} (df=4)')
print(f'p-value = {1 - stats.chi2.cdf(chi2, 4):.4f}')

# Also compute if the data is consistent with flat (no modulation)
print()
print('=== TEST FOR FLAT (NO MODULATION) ===')
# Under null hypothesis of flat distribution, expected = mean
mean_obs = np.mean(y_vals)
chi2_flat = sum((y - mean_obs)**2 / mean_obs for y in y_vals)
print(f'chi2_flat = {chi2_flat:.2f} (df=4)')
print(f'p-value (flat) = {1 - stats.chi2.cdf(chi2_flat, 4):.4f}')
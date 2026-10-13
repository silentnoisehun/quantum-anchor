import math

# Wilson 95% CI function
def wilson_ci95(successes, trials):
    if trials <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    margin = (z / denom) * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return [round(max(0.0, center - margin) * 100.0, 3), round(min(1.0, center + margin) * 100.0, 3)]

# Phase data
phases = [
    {'idx': 0, 'c0': 6, 'c1': 7, 'shots': 1024, 'phi': 0.0},
    {'idx': 1, 'c0': 3, 'c1': 0, 'shots': 1024, 'phi': 1.256637},
    {'idx': 2, 'c0': 2, 'c1': 0, 'shots': 1024, 'phi': 2.513274},
    {'idx': 3, 'c0': 7, 'c1': 7, 'shots': 1024, 'phi': 3.769911},
    {'idx': 4, 'c0': 1, 'c1': 2, 'shots': 1024, 'phi': 5.026548},
]

print('=== Per-Phase Wilson 95% CI ===')
for p in phases:
    s = p['c0'] + p['c1']
    ci = wilson_ci95(s, p['shots'])
    print('Phase {}: sum={}, coherence={:.2f}%, CI={}%'.format(p['idx'], s, s/p['shots']*100, ci))

print()
print('=== Aggregate (5120 shots) ===')
total_shots = sum(p['shots'] for p in phases)
total_successes = sum(p['c0'] + p['c1'] for p in phases)
ci_agg = wilson_ci95(total_successes, total_shots)
print('Total: sum={}, coherence={:.2f}%, CI={}%'.format(total_successes, total_successes/total_shots*100, ci_agg))

print()
print('=== Theoretical cos(8*phi) prediction ===')
for p in phases:
    phi = p['phi']
    p_theory = (1 + math.cos(8 * phi)) / 128.0 * 100
    print('Phase {}: phi={:.4f}, 8*phi={:.4f}, cos={:.4f}, P(0^8)=P(1^8)={:.4f}%, sum={:.4f}%'.format(p['idx'], phi, 8*phi, math.cos(8*phi), p_theory, 2*p_theory))

print()
print('=== cos(8*phi) least squares fit ===')
y_data = [(p['c0'] + p['c1']) / p['shots'] * 100 for p in phases]
x_data = [math.cos(8 * p['phi']) for p in phases]

n = len(x_data)
sum_x = sum(x_data)
sum_y = sum(y_data)
sum_xy = sum(x_data[i] * y_data[i] for i in range(n))
sum_x2 = sum(x_data[i]**2 for i in range(n))

A = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
B = (sum_y - A * sum_x) / n

print('Fitted: amplitude A = {:.4f}%, offset B = {:.4f}%'.format(A, B))

y_pred = [A * x_data[i] + B for i in range(n)]
ss_res = sum((y_data[i] - y_pred[i])**2 for i in range(n))
y_mean = sum_y / n
ss_tot = sum((y_data[i] - y_mean)**2 for i in range(n))
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
print('R^2 = {:.4f}'.format(r2))

print('Theoretical: amplitude = {:.4f}%, offset = {:.4f}%'.format(1.5625, 1.5625))

print()
print('=== Chi-squared tests (df=4) ===')
chi2_cos = sum((y_data[i] - y_pred[i])**2 / max(y_pred[i], 0.01) for i in range(n))
flat_pred = y_mean
chi2_flat = sum((y_data[i] - flat_pred)**2 / max(flat_pred, 0.01) for i in range(n))

print('chi2(cos) = {:.2f}'.format(chi2_cos))
print('chi2(flat) = {:.2f}'.format(chi2_flat))

# p-values without scipy - use Wilson-Hilferty approximation
def chi2_pvalue(chi2, df):
    # Wilson-Hilferty approximation
    z = ((chi2/df)**(1/3) - (1 - 2/(9*df))) / math.sqrt(2/(9*df))
    from math import erf, sqrt
    return 1 - 0.5 * (1 + erf(z/sqrt(2)))

p_cos = chi2_pvalue(chi2_cos, 4)
p_flat = chi2_pvalue(chi2_flat, 4)
print('p(cos) = {:.2e}'.format(p_cos))
print('p(flat) = {:.2e}'.format(p_flat))

# Save results to JSON for use in documentation
import json
results = {
    'per_phase': [],
    'aggregate': {
        'total_shots': total_shots,
        'total_successes': total_successes,
        'coherence_pct': total_successes/total_shots*100,
        'ci95': ci_agg
    },
    'fit': {
        'amplitude_pct': A,
        'offset_pct': B,
        'r_squared': r2,
        'theoretical_amplitude': 1.5625,
        'theoretical_offset': 1.5625
    },
    'chi2': {
        'cos_model': chi2_cos,
        'flat_model': chi2_flat,
        'p_cos': p_cos,
        'p_flat': p_flat,
        'df': 4
    }
}
for p in phases:
    s = p['c0'] + p['c1']
    ci = wilson_ci95(s, p['shots'])
    results['per_phase'].append({
        'phase_idx': p['idx'],
        'phi_rad': p['phi'],
        'c0': p['c0'],
        'c1': p['c1'],
        'sum': s,
        'coherence_pct': s/p['shots']*100,
        'ci95': ci
    })

with open('measurement_raw/tesseract_v3_5phase_final_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print()
print('Results saved to measurement_raw/tesseract_v3_5phase_final_analysis.json')
import math

# Phase data
phases = [
    {'idx': 0, 'c0': 6, 'c1': 7, 'shots': 1024, 'phi': 0.0},
    {'idx': 1, 'c0': 3, 'c1': 0, 'shots': 1024, 'phi': 1.256637},
    {'idx': 2, 'c0': 2, 'c1': 0, 'shots': 1024, 'phi': 2.513274},
    {'idx': 3, 'c0': 7, 'c1': 7, 'shots': 1024, 'phi': 3.769911},
    {'idx': 4, 'c0': 1, 'c1': 2, 'shots': 1024, 'phi': 5.026548},
]

# Measured coherence percentages
y_measured = [(p['c0'] + p['c1']) / p['shots'] * 100 for p in phases]

# Theoretical expected (cos(8phi) model)
y_theory = []
for p in phases:
    phi = p['phi']
    p_theory = (1 + math.cos(8 * phi)) / 128.0 * 100
    y_theory.append(2 * p_theory)  # sum of P(0^8) + P(1^8)

print("Measured:", ["{:.2f}%".format(v) for v in y_measured])
print("Theory:  ", ["{:.2f}%".format(v) for v in y_theory])

# Chi-squared vs theoretical model
chi2_theory = sum((y_measured[i] - y_theory[i])**2 / max(y_theory[i], 0.01) for i in range(5))
print("\nChi-squared vs THEORETICAL cos(8phi) model: {:.2f}".format(chi2_theory))

# Chi-squared vs flat model (mean of measured)
y_flat = sum(y_measured) / 5
chi2_flat = sum((y_measured[i] - y_flat)**2 / max(y_flat, 0.01) for i in range(5))
print("Chi-squared vs FLAT model (mean={:.2f}%): {:.2f}".format(y_flat, chi2_flat))

# p-values using Wilson-Hilferty
def chi2_pvalue(chi2, df):
    z = ((chi2/df)**(1/3) - (1 - 2/(9*df))) / math.sqrt(2/(9*df))
    from math import erf, sqrt
    return 1 - 0.5 * (1 + erf(z/sqrt(2)))

p_theory = chi2_pvalue(chi2_theory, 4)
p_flat = chi2_pvalue(chi2_flat, 4)
print("p(theory) = {:.2e}".format(p_theory))
print("p(flat) = {:.2e}".format(p_flat))

# Also compute with absolute counts (better for chi-squared)
print("\n=== Chi-squared with absolute counts ===")
y_counts = [p['c0'] + p['c1'] for p in phases]
expected_counts = [y_theory[i] / 100 * 1024 for i in range(5)]
flat_counts = sum(y_counts) / 5

print("Observed counts:", y_counts)
print("Expected (theory):", ["{:.1f}".format(v) for v in expected_counts])
print("Expected (flat):", ["{:.1f}".format(flat_counts)] * 5)

chi2_theory_counts = sum((y_counts[i] - expected_counts[i])**2 / max(expected_counts[i], 0.1) for i in range(5))
chi2_flat_counts = sum((y_counts[i] - flat_counts)**2 / max(flat_counts, 0.1) for i in range(5))

print("Chi-squared vs THEORY (counts): {:.2f}".format(chi2_theory_counts))
print("Chi-squared vs FLAT (counts): {:.2f}".format(chi2_flat_counts))

p_theory_c = chi2_pvalue(chi2_theory_counts, 4)
p_flat_c = chi2_pvalue(chi2_flat_counts, 4)
print("p(theory) = {:.2e}".format(p_theory_c))
print("p(flat) = {:.2e}".format(p_flat_c))

# Now let's check what the existing docs claim - maybe they used different data
print("\n=== Checking existing doc claims ===")
# The docs say: chi2(cos)=30.72, chi2(flat)=20.29, R2=-4.41
# R2 negative means fit is worse than mean - this is possible with some definitions
# Let's check if the data in the docs is different

# The docs table shows:
# Phase 0: c0=6, c1=7 -> 13 (1.27%) -- matches!
# Phase 1: c0=3, c1=0 -> 3 (0.29%) -- matches!
# Phase 2: c0=2, c1=0 -> 2 (0.20%) -- matches!
# Phase 3: c0=7, c1=7 -> 14 (1.37%) -- matches!
# Phase 4: c0=1, c1=2 -> 3 (0.29%) -- matches!

# So data is the same. Let me recompute R2 differently.
# R2 = 1 - SS_res / SS_tot
# SS_res = sum of squared residuals from fitted model
# SS_tot = sum of squared deviations from mean

# My fitted model: y = 0.5113 * cos(8phi) + 0.6836
y_fitted = [0.5113 * math.cos(8 * p['phi']) + 0.6836 for p in phases]
print("\nFitted values:", ["{:.2f}%".format(v) for v in y_fitted])

ss_res = sum((y_measured[i] - y_fitted[i])**2 for i in range(5))
y_mean = sum(y_measured) / 5
ss_tot = sum((y_measured[i] - y_mean)**2 for i in range(5))
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
print("R2 (my fit): {:.4f}".format(r2))
print("SS_res: {:.4f}, SS_tot: {:.4f}".format(ss_res, ss_tot))

# What if they fit differently? Or use different formula?
# Let's try fitting: coherence = A * cos(8phi) + B
# But maybe they constrain B = A (theoretical relationship)?
# Theoretical: offset = amplitude = 1.5625%
# So let's fit with B = A (constrained)
# y = A * (cos(8phi) + 1)
# This is the same as y = 2A * P(0^8) -- no, wait

# Theoretical model: y = (1/128)(1 + cos(8phi)) * 100 * 2
# = (1/64)(1 + cos(8phi)) * 100
# = 1.5625 + 1.5625 * cos(8phi)
# So offset = amplitude = 1.5625%

# Let's fit with constrained offset = amplitude
# y = A * (1 + cos(8phi))
# A = sum(y_i * (1+cos_i)) / sum((1+cos_i)^2)
x_cos = [math.cos(8 * p['phi']) for p in phases]
num = sum(y_measured[i] * (1 + x_cos[i]) for i in range(5))
den = sum((1 + x_cos[i])**2 for i in range(5))
A_constrained = num / den
print("\nConstrained fit (offset=amplitude): A = {:.4f}%".format(A_constrained))
y_constrained = [A_constrained * (1 + x_cos[i]) for i in range(5)]
print("Constrained fitted:", ["{:.2f}%".format(v) for v in y_constrained])

ss_res_c = sum((y_measured[i] - y_constrained[i])**2 for i in range(5))
r2_c = 1 - ss_res_c / ss_tot
print("R2 (constrained): {:.4f}".format(r2_c))

# Chi-squared with theoretical model but using counts and expected = theoretical
print("\n=== Chi-squared: theoretical expected counts (1024 shots each) ===")
# Theoretical expected counts for 1024 shots:
# Phase 0: 3.125% of 1024 = 32
# Phase 1: 0.298% of 1024 = 3.06
# Phase 2: 2.045% of 1024 = 20.94
# Phase 3: 2.045% of 1024 = 20.94
# Phase 4: 0.298% of 1024 = 3.06

theory_counts = [32, 3.06, 20.94, 20.94, 3.06]
obs_counts = [13, 3, 2, 14, 3]
chi2_theory_exact = sum((obs_counts[i] - theory_counts[i])**2 / max(theory_counts[i], 0.1) for i in range(5))
chi2_flat_exact = sum((obs_counts[i] - sum(obs_counts)/5)**2 / max(sum(obs_counts)/5, 0.1) for i in range(5))
print("Theory expected counts: {}".format(theory_counts))
print("Observed counts: {}".format(obs_counts))
print("Chi-squared vs THEORY (exact): {:.2f}".format(chi2_theory_exact))
print("Chi-squared vs FLAT (exact): {:.2f}".format(chi2_flat_exact))
p_te = chi2_pvalue(chi2_theory_exact, 4)
p_fe = chi2_pvalue(chi2_flat_exact, 4)
print("p(theory exact) = {:.2e}".format(p_te))
print("p(flat exact) = {:.2e}".format(p_fe))
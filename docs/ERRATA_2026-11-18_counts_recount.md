# Erratum 2026-11-18: Chi-square on Counts, Corrected Theoretical Prediction, and Job-Confounded Phase Analysis

**Document ID:** `ERRATA_2026-11-18_counts_recount`  
**Date:** 2026-11-18, 16:50 UTC (17:50 Budapest)  
**Author:** Maya, on request of Lead Engineer Máté Róbert (Rongyász)  
**Repository:** `quantum-anchor` (Zenodo DOI: [10.5281/zenodo.23407123](https://doi.org/10.5281/zenodo.23407123))  
**Base commit:** `33342cd`

---

## 1. Executive Summary

This erratum corrects statistical test methodologies, ideal theoretical predictions, and interpretation notes for the 5-phase Tesseract-V3 interferometric readout experiment performed on the IQM Garnet 20-qubit processor.

**Key conclusions remain fully in agreement with standard textbook quantum mechanics:**
1. No physical quantum memory effect or physical anchor reality stabilization is proven.
2. The $\cos(8\phi)$ modulation hypothesis is **not established** on hardware ($R^2 = 0.48$, $\chi^2 = 8.53$, $df = 3$, $p = 0.036$).
3. The observed mean extremal bitstring rate ($0.684\%$, 35/5120 counts) is consistent with the uniform random 8-bit noise floor ($2/256 = 0.781\%$).
4. Rejection of a uniform rate model across the 5 phases ($\chi^2 = 20.29$, $df = 4$, $p = 4.4 \times 10^{-4}$) indicates inter-phase differences, but these runs were submitted as independent hardware jobs separated in time, confounding any physical phase dependence with temporal calibration drift.

---

## 2. Issues Corrected

### A. Chi-Square Computed on Percentage Variances (Fixed to Raw Counts)
- **Previous state:** Previous analysis scripts calculated $\chi^2_\text{flat} = 1.981$ and $\chi^2_{\cos(8\phi)} = 0.833$ by dividing squared differences in percentage points by the percentage mean. This metric lacks a valid chi-square sampling distribution under multinomial / Poisson sampling.
- **Correction:** Chi-square tests are now calculated strictly on integer count frequencies ($k_i = c_{0,i} + c_{1,i}$, $N_i = 1024$, total $K = 35$, $N = 5120$):
  - **Flat model ($df = 4$):** Expected $E_i = 7.0$ per phase.
    $$\chi^2_\text{flat} = \sum_{i=0}^4 \frac{(k_i - 7.0)^2}{7.0} = \frac{36}{7} + \frac{16}{7} + \frac{25}{7} + \frac{49}{7} + \frac{16}{7} = \frac{142}{7} \approx 20.2857$$
    $$p = 4.39 \times 10^{-4} \quad (\text{exact multinomial } p = 4.9 \times 10^{-4})$$
  - **Fitted $\cos(8\phi)$ model ($df = 3$):** Two fitted parameters ($A = 0.5113\%$, $B = 0.6836\%$). Expected counts $E = [12.24, 3.86, 7.82, 7.82, 3.86]$.
    $$\chi^2_{\cos(8\phi)} = 8.5312, \quad p = 0.0362$$
    The fitted $\cos(8\phi)$ model is rejected at $\alpha = 0.05$.
  - **Parameter-free ideal model ($df = 5$):** Expected counts $E = [16.00, 1.53, 10.47, 10.47, 1.53]$.
    $$\chi^2_\text{ideal} = 11.4420, \quad \text{asymptotic } p = 0.0433, \quad \text{Monte Carlo } p = 0.047$$

### B. Factor-of-Two Error in Theoretical Maxima
- **Previous state:** Documentation cited theoretical coherence as $P(0^8) = P(1^8) = \frac{1}{128}(1+\cos 8\phi)$, giving an erroneous theoretical maximum of $3.125\%$.
- **Correction:** The state prior to measurement is:
  $$H^{\otimes 8}|\text{GHZ}(\phi)\rangle = \sum_{x \in \{0,1\}^8} \frac{1}{\sqrt{512}} \left[ 1 + (-1)^{|x|} e^{i8\phi} \right] |x\rangle$$
  The probabilities are:
  $$P(0^8) = P(1^8) = \frac{1}{512} |1 + e^{i8\phi}|^2 = \frac{1}{256}(1 + \cos 8\phi)$$
  $$P(0^8) + P(1^8) = \frac{1}{128}(1 + \cos 8\phi)$$
  The theoretical maximum per phase is $\frac{2}{128} = 1.5625\%$ (at $\phi = 0$). Ideal predictions across the 5 phases are:
  - Phase 0 ($\phi = 0.000$): $1.563\%$ ($16.0$ expected counts)
  - Phase 1 ($\phi = 1.257$): $0.149\%$ ($1.53$ expected counts)
  - Phase 2 ($\phi = 2.513$): $1.023\%$ ($10.47$ expected counts)
  - Phase 3 ($\phi = 3.770$): $1.023\%$ ($10.47$ expected counts)
  - Phase 4 ($\phi = 5.027$): $0.149\%$ ($1.53$ expected counts)

### C. Phase 2 vs Phase 3 Asymmetry and Job Confounding
- Exact two-sided binomial test on Phase 2 ($k=2$) vs Phase 3 ($k=14$):
  $$p = 2 \times \sum_{j=0}^2 \binom{16}{j} 0.5^{16} = \frac{2 \times (1 + 16 + 120)}{65536} = \frac{274}{65536} \approx 0.00418$$
- **Confounding:** Phase 2 (job `01a11aba-531f-73ae-8da7-c705c729038d`) and Phase 3 (job `01a11aba-c6d7-736a-ac56-a5c0525d2cc4`) were executed as independent QPU submissions 11 seconds apart. In superconducting architectures, calibration fluctuations, two-level system (TLS) shifts, and readout bias across jobs can produce variations of this magnitude. This cannot be claimed as phase-induced evidence without interleaved circuit execution within the same job.

### D. Phase 0 Calibration Provenance
- Phase 0 in the 5-phase analysis was taken from a repeat job at 06:09 UTC (counts 13/1024, $1.27\%$), whereas the original 08:35 UTC anchor run yielded 8/1024 ($0.78\%$). This difference is recorded as experimental provenance.

---

## 3. Recount Data Artifact

All count-level calculations, test statistics, and exact $p$-values are preserved in:
`measurement_raw/tesseract_v3_5phase_recount_counts_20261118.json`

Historical analysis files in `measurement_raw/` were preserved without modification.

---

## 4. Modified Files

- `CITATION.cff`
- `arxiv/quantum_anchor_v1.2.tex`
- `arxiv/jote_manuscript.tex`
- `docs/JOTE_COVER_LETTER.md`
- `docs/HOPE-WP-2026-V1.2.md`
- `docs/VALIDATION.md`
- `README.md`
- `analyze_5phase_final.py`
- `analyze_5phase_final_v3.py`
- `run_analysis_final.py`
- `run_analysis_final2.py`
- `tesseract_v3_interferometric.py`
- `docs/ERRATA_2026-11-18_counts_recount.md` (this file)

# Cover Letter: Journal of Trial and Error (JOTE)

**Date:** November 2026  
**To:** The Editorial Board, *Journal of Trial and Error* (ISSN: 2667-1204)  
**From:** Máté Róbert, Independent Quantum Researcher, Budapest, Hungary (`materobi86@gmail.com`)  
**Subject:** Submission of Manuscript: *"Methodological Obstacles, API Deprecations, and Empirical Null-Results in Weak-Drive Coherence Anchoring on Superconducting Processors"*

---

Dear Editors of the *Journal of Trial and Error*,

I am submitting our empirical research manuscript, titled **"Methodological Obstacles, API Deprecations, and Empirical Null-Results in Weak-Drive Coherence Anchoring on Superconducting Processors"**, for consideration as a Research Article in the *Journal of Trial and Error*.

### 1. The Context & The Hypothesis
In superconducting quantum computing, isolating qubits from environmental dephasing ($T_2^*$) and thermal relaxation ($T_1$) remains a paramount challenge. The "Quantum Anchor" hypothesis proposed that applying a continuous or periodic, off-resonant weak microwave tone during idling periods could autonomously anchor the qubit's relative phase without triggering wave-function collapse.

### 2. Methodological Pitfalls & API Deprecations
Originally designed for low-level analog pulse schedules (`qiskit.pulse`, `meas_level=0`), our attempts to experimentally validate this hypothesis on commercial cloud processors encountered five critical obstacles:
1. **The Disconnect in Cloud Access:** IBM officially phased out direct OpenPulse programming on standard cloud tiers, and IQM restricted pulse-level sweep definitions to enterprise accounts.
2. **The Amplitude Rotation Trap:** In our initial analytical formulation, an anchor pulse amplitude of $\text{amp} = 0.08$ with duration $\tau = 37\,\text{ns}$ was labeled a "weak perturbation." However, recalculating the Bloch sphere trajectory revealed $\theta = \text{amp} \times \tau = 2.96\,\text{rad} \approx 94.2\%$ of a $\pi$-pulse—turning a nominal perturbation into an almost complete spin inversion.

### 3. Hardware Null-Results & Retraction of a False Positive
To provide empirical resolution, we ported the protocol to fractional gate primitives and evaluated it on a 156-qubit IBM Heron processor (`ibm_marrakesh`) and a 20-qubit IQM processor (`garnet`):
- **On IBM Heron:** Both the unperturbed control and the active anchor condition decayed to 0% clear state retention. 
- **Retraction of Circuit Tautology:** We explicitly retract an earlier reported positive result ("100% state preservation"), demonstrating that it was an artifact of circuit-level self-inversion ($\hat{U}^\dagger \hat{U} = \hat{I}$) rather than physical stabilization.
- **On IQM Garnet:** An interferometric 5-phase sweep (5120 shots total) revealed that the signal (0.20% to 1.37%) was entirely dominated by the device's $\sim 0.68\%$ noise floor. Goodness-of-fit testing soundly rejected the theoretical modulation curve ($\chi^2 = 30.72, p = 6.4 \times 10^{-6}$).

### 4. Why This Fits JOTE
Negative findings and methodological pitfalls in quantum computing are chronically under-reported due to publication bias favoring positive claims. By transparently detailing the API barriers, compiler traps, and empirical null results, this article offers concrete, actionable guidance for researchers attempting to implement dynamic stabilization protocols on cloud-hosted superconducting processors.

All raw measurement files, execution timestamps, job IDs, and validation scripts are publicly available in our repository under an open MIT license:  
https://github.com/silentnoisehun/quantum-anchor

Thank you for considering our work for publication in the *Journal of Trial and Error*.

Sincerely,  
**Máté Róbert**  
Independent Quantum Researcher  
Budapest, Hungary  
Email: `materobi86@gmail.com`  
GitHub: [`silentnoisehun`](https://github.com/silentnoisehun)


---
**Contact & Collaboration:** Máté Róbert — `materobi86@gmail.com`  
*Open to research collaborations and academic partnerships / Nyitott vagyok kutatási együttműködésekre.*

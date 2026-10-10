#!/usr/bin/env python3
"""
Analyze the 4 successful phases of the Tesseract Anchor experiment on IQM Garnet 20Q.
Compute Wilson 95% CI for each phase, fit cos(8φ) curve, update documentation.
"""

import json
import math
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

# Phase results from console output (4 successful phases)
phases = [
    {
        "phase": 1,
        "bell": {"mean_plane": 95.90, "ci": [92.97, 97.70], "global": 10.94, "global_ci": [9.17, 13.00]},
        "anchor": {"mean_plane": 96.92, "ci": [93.84, 98.66], "global": 10.35, "global_ci": [8.63, 12.37]},
        "delta": +1.02,
        "verdict": "OVERLAP - no measurable anchor effect"
    },
    {
        "phase": 2,
        "bell": {"mean_plane": 96.19, "ci": [92.31, 98.10], "global": 10.84, "global_ci": [9.08, 12.89]},
        "anchor": {"mean_plane": 96.39, "ci": [93.84, 97.78], "global": 11.52, "global_ci": [9.71, 13.62]},
        "delta": +0.20,
        "verdict": "OVERLAP - no measurable anchor effect"
    },
    {
        "phase": 3,
        "bell": {"mean_plane": 96.48, "ci": [93.51, 98.26], "global": 11.04, "global_ci": [9.26, 13.10]},
        "anchor": {"mean_plane": 96.14, "ci": [91.67, 98.26], "global": 11.52, "global_ci": [9.71, 13.62]},
        "delta": -0.34,
        "verdict": "OVERLAP - no measurable anchor effect"
    },
    {
        "phase": 4,
        "bell": {"mean_plane": 96.75, "ci": [93.18, 98.66], "global": 12.40, "global_ci": [10.52, 14.56]},
        "anchor": {"mean_plane": 96.00, "ci": [92.53, 98.02], "global": 9.86, "global_ci": [8.18, 11.84]},
        "delta": -0.75,
        "verdict": "OVERLAP - no measurable anchor effect"
    }
]

# The phase angle used: 4.11 GHz × 37 ns = 0.4398 rad
# For cos(8φ) fit, the phase varies across phases? 
# Actually, the phases are repeated runs at the SAME φ. 
# A cos(8φ) fit would need multiple φ values.
# But we can analyze the stability across repeated runs at fixed φ.

PHI = 0.4398  # rad

def wilson_ci95(successes: int, trials: int) -> Tuple[float, float]:
    """95% Wilson score interval."""
    if trials <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    margin = (z / denom) * math.sqrt(
        p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return (max(0.0, center - margin) * 100.0, min(1.0, center + margin) * 100.0)

def compute_detailed_stats():
    """Compute detailed statistics from the 4 phases."""
    print("=" * 80)
    print("TESSERACT ANCHOR - 4-PHASE HARDWARE RESULTS ANALYSIS (IQM Garnet 20Q)")
    print("=" * 80)
    print(f"phi = 4.11 GHz x 37 ns = {PHI:.4f} rad (VIRTUAL Z, no physical drive)")
    print(f"Backend: garnet (20 qubits)")
    print(f"Shots per run: 1024")
    print(f"Planes: 4 (8 qubits)")
    print()
    
    # Per-phase delta statistics
    deltas = [p["delta"] for p in phases]
    mean_delta = np.mean(deltas)
    std_delta = np.std(deltas, ddof=1)
    
    print("PHASE-BY-PHASE RESULTS:")
    print("-" * 80)
    for p in phases:
        print(f"Phase {p['phase']}: bell={p['bell']['mean_plane']:.2f}% "
              f"[{p['bell']['ci'][0]:.2f}-{p['bell']['ci'][1]:.2f}]  "
              f"anchor={p['anchor']['mean_plane']:.2f}% "
              f"[{p['anchor']['ci'][0]:.2f}-{p['anchor']['ci'][1]:.2f}]  "
              f"Delta={p['delta']:+.2f} pp  -> {p['verdict']}")
    
    print()
    print("AGGREGATE STATISTICS:")
    print("-" * 80)
    print(f"Mean delta (anchor - bell): {mean_delta:+.3f} pp")
    print(f"Std deviation of delta:     {std_delta:.3f} pp")
    print(f"Range: [{min(deltas):+.3f}, {max(deltas):+.3f}] pp")
    
    # Wilson CI for aggregate
    # Total shots across 4 phases for bell and anchor
    total_shots = 4 * 1024
    # Approximate total successes from mean plane balances
    bell_successes = sum(p['bell']['mean_plane'] / 100 * 1024 for p in phases)
    anchor_successes = sum(p['anchor']['mean_plane'] / 100 * 1024 for p in phases)
    
    bell_ci = wilson_ci95(int(bell_successes), total_shots)
    anchor_ci = wilson_ci95(int(anchor_successes), total_shots)
    
    print()
    print(f"Bell (aggregate 4096 shots):   {bell_successes/total_shots*100:.2f}% "
          f"[CI {bell_ci[0]:.2f}-{bell_ci[1]:.2f}%]")
    print(f"Anchor (aggregate 4096 shots): {anchor_successes/total_shots*100:.2f}% "
          f"[CI {anchor_ci[0]:.2f}-{anchor_ci[1]:.2f}%]")
    
    # Check overlap
    overlap = not (anchor_ci[0] > bell_ci[1] or anchor_ci[1] < bell_ci[0])
    print(f"95% CI Overlap: {'YES' if overlap else 'NO'}")
    
    # Stability analysis
    print()
    print("STABILITY ANALYSIS:")
    print("-" * 80)
    print(f"Phase-to-phase variation (std): {std_delta:.3f} pp")
    print(f"Maximum single-phase delta:   {max(deltas, key=abs):+.3f} pp")
    print(f"Consistency: All 4 phases show CI overlap -> NO measurable anchor effect")
    
    # Evidence grade
    print()
    print("EVIDENCE GRADE:")
    print("-" * 80)
    print("Grade: C (Inconclusive - virtual Z, no physical drive)")
    print("Reason: All 4 phases show anchor-bell delta within Wilson 95% CI overlap.")
    print("        Virtual Z rotation (rz) is a compiler-level phase adjustment,")
    print("        not a physical drive. No T1/T2 compensation demonstrated.")
    print("        Pulse-level access required for physical anchor drive (Starter tier blocked).")
    
    return {
        "phases": phases,
        "mean_delta": float(mean_delta),
        "std_delta": float(std_delta),
        "bell_aggregate": {"pct": float(bell_successes/total_shots*100), "ci": bell_ci},
        "anchor_aggregate": {"pct": float(anchor_successes/total_shots*100), "ci": anchor_ci},
        "overlap": overlap,
        "phi": PHI,
        "evidence_grade": "C",
        "conclusion": "No measurable anchor effect at virtual Z level. Physical drive not accessible on Starter tier."
    }

def fit_cos8phi():
    """
    Note: The 4 phases are REPEATED runs at the SAME phi (0.4398 rad).
    A cos(8*phi) fit requires multiple phi values. We can only analyze stability.
    """
    print()
    print("cos(8*phi) FIT NOTES:")
    print("-" * 80)
    print(f"All 4 phases at fixed phi = {PHI:.4f} rad")
    print(f"cos(8*phi) = cos(8 x {PHI:.4f}) = cos({8*PHI:.4f}) = {math.cos(8*PHI):.4f}")
    print("To fit cos(8*phi) curve, need data at multiple phi values.")
    print("Current data: 4 repeated measures at single phi -> stability analysis only.")
    
    # We can still report the stability as the "amplitude" of variation
    deltas = [p["delta"] for p in phases]
    amp = (max(deltas) - min(deltas)) / 2
    print(f"Observed variation amplitude: +/-{amp:.2f} pp (not a cos(8*phi) fit)")

def generate_audit_json(stats):
    """Generate audit JSON for measurement_raw/"""
    audit = {
        "protocol": "tesseract_anchor_5phase_summary",
        "platform": "IQM Resonance",
        "backend": "garnet",
        "backend_qubits": 20,
        "measured_kind": "circuit_level_bitstrings",
        "is_meas_level_0": False,
        "is_physical_detuned_drive": False,
        "phase_formula": "phi = 2*pi * f_GHz * t_ns mod 2pi",
        "freq_ghz": 4.11,
        "duration_ns": 37,
        "phase_rad": PHI,
        "n_planes": 4,
        "n_qubits": 8,
        "requested_shots_per_phase": 1024,
        "completed_phases": 4,
        "failed_phases": 1,
        "failure_reason": "Not enough credits (Starter tier)",
        "phases": phases,
        "aggregate": {
            "total_shots": 4096,
            "bell_balance_pct": stats["bell_aggregate"]["pct"],
            "bell_balance_ci95_pct": stats["bell_aggregate"]["ci"],
            "anchor_balance_pct": stats["anchor_aggregate"]["pct"],
            "anchor_balance_ci95_pct": stats["anchor_aggregate"]["ci"],
            "mean_delta_pp": stats["mean_delta"],
            "delta_std_pp": stats["std_delta"],
            "ci_overlap": stats["overlap"]
        },
        "cos8phi_note": f"All phases at fixed phi={PHI:.4f}; cos(8*phi)={math.cos(8*PHI):.4f}. Multiple phi needed for curve fit.",
        "evidence_grade": "C",
        "conclusion": "No measurable anchor effect at virtual Z level. Physical drive not accessible on Starter tier.",
        "physical_anchor_compensation_proven": False,
        "global_20_reality_sync_proven": False,
        "ci_method": "Wilson score interval, 95%. Conservative envelope of per-plane CIs for mean-plane."
    }
    return audit

if __name__ == "__main__":
    stats = compute_detailed_stats()
    fit_cos8phi()
    audit = generate_audit_json(stats)
    
    # Save audit
    out_dir = Path("measurement_raw")
    out_dir.mkdir(exist_ok=True)
    import time
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = out_dir / f"tesseract_5phase_audit_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False)
    print(f"\n[AUDIT] Saved: {path}")
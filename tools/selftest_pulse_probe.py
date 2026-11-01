#!/usr/bin/env python3
"""
selftest_pulse_probe.py — offline proof that the pulse-probe layer works
=============================================================================

The pulse-probe script (`anchor_measure_iqm.py`) can never run end to end: the
IQM account was MEASURED as lacking the pulse-level entitlement. That makes it
easy to let the pure code rot unnoticed — nothing would ever call it.

This self-test exercises the parts that CAN be proven offline, with NO
network, NO token, NO IQM client call:

  1. the module imports with IQM_TOKEN unset
  2. the sampling-rate arithmetic (37 ns @ 2 GHz -> 74 -> 72, granularity 8)
  3. the `n_samples < 8` guard for sub-granularity durations
  4. the Gaussian samples stay finite and normalised to max == 1.0, even at
     sigma extremes where `samples / np.max(samples)` would otherwise be NaN
  5. `virtual_z_phase` is correct and mod-2pi wrapped
  6. `--token` is GONE from the CLI (it is a secret-handling regression)
  7. the retracted Borg text is not asserted as hardware-proven

Assertions 6 and 7 are documentation-integrity assertions: they are the
regression guards for defects that already existed in this file.

No temp files, no deletions, no network. Runs entirely in memory.
"""
from __future__ import annotations

import math
import os
import re
import sys
from pathlib import Path

# The Windows console defaults to cp1250 and cannot encode the ✓/π/φ
# characters the module prints. Reconfigure BEFORE importing it, so a
# successful check does not die with UnicodeEncodeError on a print.
for _name in ("stdout", "stderr"):
    _stream = getattr(sys, _name, None)
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "anchor_measure_iqm.py"

sys.path.insert(0, str(ROOT))

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'OK  ' if ok else 'FAIL'}  {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)
    return ok


# ---------------------------------------------------------------------------
# 1. import without IQM_TOKEN
# ---------------------------------------------------------------------------
print("=== 1. module imports with IQM_TOKEN unset ===")

had_token = "IQM_TOKEN" in os.environ
saved_token: str | None = os.environ.pop("IQM_TOKEN", None)
try:
    import anchor_measure_iqm as amp_mod

    src = MODULE_PATH.read_text(encoding="utf-8")
    check("import anchor_measure_iqm with no IQM_TOKEN in env", True)
    check("IQM_TOKEN absent during import", "IQM_TOKEN" not in os.environ)
finally:
    if had_token and saved_token is not None:
        os.environ["IQM_TOKEN"] = saved_token

# ---------------------------------------------------------------------------
# 2. sampling-rate arithmetic
# ---------------------------------------------------------------------------
print()
print("=== 2. sampling-rate arithmetic ===")

n37 = amp_mod.sample_count(37, 2e9)
check("37 ns @ 2 GHz -> 74 samples", int(37 * 1e-9 * 2e9) == 74)
check("rounded DOWN to a multiple of 8 -> 72", n37 == 72, f"got {n37}")
check("72 % 8 == 0", n37 % 8 == 0)

# ---------------------------------------------------------------------------
# 3. sub-granularity guard
# ---------------------------------------------------------------------------
print()
print("=== 3. sub-granularity duration still yields >= 8 samples ===")

n_sub = amp_mod.sample_count(1.0, 2e9)          # 2 raw samples -> 0 after rounding
check("1 ns @ 2 GHz -> 8 samples (n_samples < 8 guard)", n_sub == 8, f"got {n_sub}")
n_zero = amp_mod.sample_count(0.0, 2e9)
check("0 ns @ 2 GHz -> 8 samples", n_zero == 8, f"got {n_zero}")
check("guard never returns fewer than 8",
      all(amp_mod.sample_count(float(d), 2e9) >= 8 for d in (0, 0.1, 1, 3, 3.9)))

# ---------------------------------------------------------------------------
# 4. Gaussian samples: finite, non-empty, normalised to max == 1.0
# ---------------------------------------------------------------------------
print()
print("=== 4. Gaussian samples finite, non-empty, max == 1.0 ===")

import numpy as np

n, samples = amp_mod.compute_samples(37, 0.1)
check("sample array non-empty", samples.size == n and n > 0, f"n={n}")
check("all values finite", bool(np.isfinite(samples).all()))
check("max normalised to exactly 1.0",
      abs(float(np.max(samples)) - 1.0) < 1e-12,
      f"max={float(np.max(samples))!r}")
check("no NaN / inf in the normal case",
      not bool(np.isnan(samples).any()) and not bool(np.isinf(samples).any()))

# The real NaN risk: at a very small sigma every exp() underflows to 0, so
# samples / np.max(samples) is 0/0.
sigma_extremes_ok = True
sigma_detail = []
for sigma in (1e-9, 1e-12, 1e-18, 0.0, -0.1, 1e6):
    n2, s2 = amp_mod.compute_samples(37, sigma)
    finite = bool(np.isfinite(s2).all())
    peak_ok = abs(float(np.max(s2)) - 1.0) < 1e-12
    size_ok = s2.size == n2 and n2 >= 8
    if not (finite and peak_ok and size_ok):
        sigma_extremes_ok = False
        sigma_detail.append(
            f"sigma={sigma}: finite={finite} max={float(np.max(s2))!r} n={n2}")
check("no NaN / inf and still normalised at sigma extremes",
      sigma_extremes_ok, "; ".join(sigma_detail))

# ---------------------------------------------------------------------------
# 5. virtual_z_phase
# ---------------------------------------------------------------------------
print()
print("=== 5. virtual_z_phase ===")

phi = amp_mod.virtual_z_phase(4.11, 37)
check("4.11 GHz x 37 ns -> ~0.4398 rad", abs(phi - 0.4398) < 1e-3, f"{phi:.6f}")
check("wrapped into [0, 2pi)", 0.0 <= phi < 2.0 * math.pi)

# Regression guard: the old formula multiplied GHz*ns by 1e-9, which gives
# 9.555e-7 rad (~0) instead of 0.4398 rad.
wrong = 2 * math.pi * 4.11 * 37 * 1e-9
check("the 1e-9 error factor is NOT used", abs(phi - wrong) > 1e-6,
      f"old formula would give {wrong:.3e} rad")

wrapped = [amp_mod.virtual_z_phase(f, 37) for f in (0.0, 1.0, 4.11, 12.5, 100.0)]
check("all outputs wrapped into [0, 2pi)",
      all(0.0 <= v < 2.0 * math.pi for v in wrapped))

# ---------------------------------------------------------------------------
# 6. --token is gone
# ---------------------------------------------------------------------------
print()
print("=== 6. --token is gone from the CLI ===")

help_text = amp_mod.build_parser().format_help()
check("'--token' not in --help output", "--token" not in help_text)

option_strings = [o for act in amp_mod.build_parser()._actions
                  for o in act.option_strings]
check("no --token option registered on the parser",
      "--token" not in option_strings, f"options={option_strings}")

# The scanner rule is `--token "YOUR_TOKEN"`. Assert neither half survives.
check("no inline token literal in the source",
      re.search(r"--token\s+[\"']?YOUR_TOKEN", src, re.IGNORECASE) is None)
check("source mentions IQM_TOKEN as the only token channel",
      "IQM_TOKEN" in src)

# run_iqm_measurement must not accept a `token` parameter.
import inspect

run_params = list(inspect.signature(amp_mod.run_iqm_measurement).parameters)
check("run_iqm_measurement() has no 'token' parameter",
      "token" not in run_params, f"params={run_params}")

# ---------------------------------------------------------------------------
# 7. retracted Borg text is not asserted as hardware-proven
# ---------------------------------------------------------------------------
print()
print("=== 7. retracted Borg claims are not asserted as proven ===")

RETRACTION_MARKERS = re.compile(
    r"visszavon|retract|tautol|hamis| téves|NEM igazolt|NOT PROVEN|"
    r"NEM MÉRT|NOT MEASURED", re.IGNORECASE)

lines = src.splitlines()

hard_proven_hits = [i + 1 for i, ln in enumerate(lines) if "HARDWARE PROVEN" in ln]
check("no 'HARDWARE PROVEN' in the module source", not hard_proven_hits,
      f"lines={hard_proven_hits}")

# A bare 'anchor ... PROVEN' assertion is the same defect in Hungarian-free form.
anchor_proven = [i + 1 for i, ln in enumerate(lines)
                 if re.search(r"anchor (?:drive )?(?:compensation )?(?:IS )?PROVEN",
                              ln, re.IGNORECASE)]
check("no 'anchor ... PROVEN' assertion", not anchor_proven,
      f"lines={anchor_proven}")


def unretracted_clear(lines: list[str]) -> list[int]:
    """Lines mentioning 'clear %' that carry no retraction marker nearby."""
    bad = []
    for i, ln in enumerate(lines):
        if not re.search(r"\d+(?:[.,]\d+)?\s*%?\s*clear", ln, re.IGNORECASE):
            continue
        window = "\n".join(lines[max(0, i - 2):i + 3])
        if not RETRACTION_MARKERS.search(window):
            bad.append(i + 1)
    return bad


bad_clear = unretracted_clear(lines)
check("no un-retracted 'clear %' claim", not bad_clear, f"lines={bad_clear}")

# And the headline phrasing from the original defect.
check("no 'Borg 16 cap clear 100%' string",
      re.search(r"Borg\s+16\s+cap\s+clear\s+100\s*%", src, re.IGNORECASE) is None)

# The refusal message must be present and quoted as measured.
check("measured entitlement refusal is documented",
      "pulse-level access enabled" in src)
check("device qubit count matches the live SDK (20, not 19)",
      "Garnet 20Q" in src and "Garnet 19Q" not in src)
check("no meas_level=0 equivalence claim",
      re.search(r"meas[_ ]level\s*=\s*0 (?:equivalent|ekvivalens)", src, re.IGNORECASE) is None)

# ---------------------------------------------------------------------------
print()
print("=" * 74)
if failures:
    print(f"RESULT: FAIL ({len(failures)} problem(s))")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("RESULT: PASS — pulse-probe layer verified offline "
      "(sampling math, Gaussian normalisation, phase formula, "
      "no --token, no retracted claim asserted)")
sys.exit(0)
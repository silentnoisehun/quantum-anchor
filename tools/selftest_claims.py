#!/usr/bin/env python3
"""
selftest_claims.py — prove the claim scanner actually detects defects
===================================================================

A linter that never fires is indistinguishable from a broken linter. This file
feeds check_claims.py a fixture containing every known-bad phrasing as a LIVE
(uncorrected) assertion, and asserts the scanner flags all of them.

It also feeds a CORRECTED fixture — the same claims correctly marked as
retracted or not-shown — and asserts the scanner stays silent. The second half
matters as much as the first: a scanner that fires on correct documentation
gets disabled within a week.

No temp files, no deletions, no network. Runs entirely in memory.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_claims as cc  # noqa: E402

BROKEN = """# Broken fixture

Anchor drive compensation IS PROVEN on real hardware.
Pulse-level access available since the account was upgraded.
This is a meas_level=0 equivalent measurement.
The 1024 bitstrings captured confirm the anchor.
phase = 2 * pi * 4.11 * 37e-9
doi: 10.5281/zenodo.XXXXXXX
"""

CORRECTED = """# Corrected fixture

Anchor drive compensation is NOT PROVEN; both conditions gave 0% clear.
Pulse-level access is unavailable: the account lacks the entitlement.
This is NOT a meas_level=0 equivalent; get_memory returns bitstrings.
Only the first 10 of 1024 bitstrings were saved to the audit file.
phase = 2 * pi * 4.11 * 37  # GHz*ns already dimensionless
doi: omitted until Zenodo mints it
"""


def run(name: str, text: str) -> set[str]:
    with tempfile.TemporaryDirectory() as td:
        rel = Path(td).relative_to(Path(td))  # unused; scan via absolute shim
        target = Path(td) / "fixture.md"
        target.write_text(text, encoding="utf-8")
        original_root = cc.ROOT
        try:
            cc.ROOT = Path(td)
            findings = cc.scan_file("fixture.md")
        finally:
            cc.ROOT = original_root
    return {f[0] for f in findings}


def main() -> int:
    failures = 0

    print("=== part 1: scanner MUST fire on broken claims ===")
    detected = run("broken", BROKEN)
    expected = {
        "anchor-proven",
        "pulse-level-available",
        "meas-level-0-equivalent",
        "full-memory-claim",
        "phase-formula-1e-9",
        "placeholder-doi",
    }
    for rule in sorted(expected):
        hit = rule in detected
        print(f"  {'OK ' if hit else 'FAIL'}  {rule}")
        if not hit:
            failures += 1

    extra = detected - expected
    if extra:
        print(f"  note: also flagged {sorted(extra)}")

    print()
    print("=== part 2: scanner MUST stay silent on corrected claims ===")
    still = run("corrected", CORRECTED)
    if still:
        print(f"  FAIL  false positives: {sorted(still)}")
        failures += 1
    else:
        print("  OK    no false positives on correctly-marked text")

    print()
    if failures:
        print(f"RESULT: FAIL ({failures} problem(s))")
        return 1
    print("RESULT: PASS — scanner detects defects and respects retractions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
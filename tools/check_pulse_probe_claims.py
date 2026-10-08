#!/usr/bin/env python3
"""
check_pulse_probe_claims.py — guard the pulse-probe script's wording
======================================================================

`anchor_measure_iqm.py` was the last file in the repository still asserting
retracted and unproven claims in plain sight:

  * a `--token` CLI argument, i.e. an invitation to pass a secret on the
    command line where it persists in shell history;
  * `Borg 16 cap clear 100%` graded `HARDWARE PROVEN` — a result since
    retracted as a circuit tautology;
  * `get_memory() is a meas_level=0 equivalent` — it returns decoded
    bitstrings, not an IQ vector;
  * `Garnet 19Q` — the live SDK reports 20 qubits; the 19Q figure was a
    remembered value that had propagated through four documents;
  * a balance computation divided by the REQUESTED shot count, which is the
    exact arithmetic that produced the mis-reported 11.62% figure.

These are statements about text, so this is a text check. Its one non-obvious
rule is the last one: `100% clear` is ALLOWED to appear, provided the
surrounding lines mark it retracted. A rule that forbade the phrase outright
would forbid documenting the retraction — and a checker that punishes correct
documentation gets switched off within a week.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _name in ("stdout", "stderr"):
    _stream = getattr(sys, _name, None)
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parent.parent
TARGET = "anchor_measure_iqm.py"

RETRACTION_NEAR = re.compile(
    r"VISSZAVONVA|RETRACTED|tautol|TAUTOL|visszavonva", re.IGNORECASE)


def check() -> list[str]:
    path = ROOT / TARGET
    if not path.exists():
        return [f"missing file: {TARGET}"]

    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    bad: list[str] = []

    if re.search(r"""add_argument\(\s*["']--token""", src):
        bad.append(f"{TARGET}: still defines a --token CLI option; the secret "
                   f"must come only from the IQM_TOKEN environment variable")

    if "YOUR_TOKEN" in src:
        bad.append(f"{TARGET}: contains an inline token literal")

    if re.search(r"token\s*=\s*(?!os\.getenv|None|token\b)\w", src):
        bad.append(f"{TARGET}: passes a token= argument to a client; read it "
                   f"from the environment instead")

    if "HARDWARE PROVEN" in src:
        bad.append(f"{TARGET}: asserts 'HARDWARE PROVEN'; the Borg 100% clear "
                   f"result was retracted as a circuit tautology")

    for i, line in enumerate(lines):
        if "100% clear" not in line:
            continue
        window = "\n".join(lines[max(0, i - 3):i + 6])
        if not RETRACTION_NEAR.search(window):
            bad.append(f"{TARGET}:{i + 1}: states '100% clear' without marking "
                       f"it retracted")

    if re.search(r"meas_level=0\s*(?:equivalent|ekvivalens)", src, re.IGNORECASE):
        bad.append(f"{TARGET}: calls get_memory() a meas_level=0 equivalent; it "
                   f"returns decoded bitstrings, not an IQ vector")

    if re.search(r"(?:Garnet|garnet)[^\n]{0,40}?\b19\s*Q\b", src):
        bad.append(f"{TARGET}: mentions Garnet 19Q; the live SDK reports "
                   f"20 qubits (measured 2026-10-07)")

    return bad


def main() -> int:
    print("=" * 74)
    print(f"PULSE-PROBE WORDING — {TARGET}")
    print("=" * 74)
    print()

    bad = check()
    if bad:
        print(f"FINDINGS ({len(bad)})")
        for b in bad:
            print(f"  ! {b}")
        print()
        print("RESULT: FAIL — the pulse-probe script regressed")
        return 1

    print("OK  no --token CLI option; the secret is read from IQM_TOKEN")
    print("OK  no retracted claim asserted as proven")
    print("OK  no meas_level=0 equivalence claim")
    print("OK  device size consistent with the measured Garnet backend")
    print()
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())


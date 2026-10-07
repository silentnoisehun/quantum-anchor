#!/usr/bin/env python3
"""
run_checks.py — one command to verify the whole repository
===========================================================

Runs every offline check that does NOT need hardware, network, or a token:

  1. IQM circuit construction + analysis logic (--validate)
  2. LaTeX structure (check_tex.py)
  3. Claim consistency across published files (check_claims.py)
  4. Claim-scanner self-test (selftest_claims.py)
  5. Working-tree secret leak audit (audit_secrets.py)
  6. Git-history secret leak audit (audit_git_history.py)
  7. Pure-stdlib import smoke test of the offline modules

Exit code is non-zero if ANY check fails. This is the command to run before
tagging a release or claiming the repository is in a consistent state.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# The collected subprocess output is UTF-8 (the child scripts force UTF-8 on
# their own stdout because the Windows console defaults to cp1250 and cannot
# encode the ✓/π/φ characters they print). Without reconfiguring here, printing
# that output raises UnicodeEncodeError and the whole suite crashes on a
# SUCCESSFUL check.
for _name in ("stdout", "stderr"):
    _stream = getattr(sys, _name, None)
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        try:
            _reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parent.parent

CHECKS: list[tuple[str, list[str]]] = [
    ("IQM circuit validation",
     [sys.executable, "anchor_measure_iqm_final.py", "--validate"]),
    ("LaTeX structure",
     [sys.executable, "tools/check_tex.py"]),
    ("Claim consistency",
     [sys.executable, "tools/check_claims.py"]),
    ("Claim scanner self-test",
     [sys.executable, "tools/selftest_claims.py"]),
    ("Working-tree secret audit",
     [sys.executable, "tools/audit_secrets.py"]),
    ("Git-history secret audit",
     [sys.executable, "tools/audit_git_history.py"]),
    ("Stdlib import smoke test",
     [sys.executable, "-c",
      "import src.anchor_model, src.anchor_measure, src.check_no_dependencies;"
      "print('offline modules import cleanly')"]),
]


def main() -> int:
    print("=" * 74)
    print("QUANTUM ANCHOR — FULL OFFLINE CHECK SUITE")
    print("=" * 74)
    print()

    results: list[tuple[str, int]] = []
    for name, cmd in CHECKS:
        print(f"--- {name} " + "-" * max(0, 60 - len(name)))
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        # Show only the tail so the summary stays readable.
        out = (res.stdout or "").strip().splitlines()
        tail = out[-4:]
        for line in tail:
            print(f"    {line}")
        if res.returncode != 0:
            err = (res.stderr or "").strip().splitlines()
            for line in err[-6:]:
                print(f"    ! {line}")
        results.append((name, res.returncode))
        print()

    print("=" * 74)
    print("SUMMARY")
    print("=" * 74)
    failed = [n for n, rc in results if rc != 0]
    for name, rc in results:
        print(f"  {'PASS' if rc == 0 else 'FAIL'}  {name}")
    print()
    if failed:
        print(f"RESULT: FAIL — {len(failed)} check(s) failed: {failed}")
        return 1
    print("RESULT: PASS — all offline checks green")
    print()
    print("NOT covered by this suite (requires hardware or external account):")
    print("  - the actual IQM control-matrix measurement run")
    print("  - Zenodo DOI minting")
    print("  - arXiv upload")
    print("  - pulse-level Sweep access (measured as unavailable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
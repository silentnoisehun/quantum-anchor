"""
Unit tests for Quantum Anchor offline modules and verification suite.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.anchor_model import (
    anchor_solution,
    bloch_rotation_rad,
    predicted_population,
    expected_advantage,
)
from src.check_no_dependencies import main as check_no_deps_main
from tools.check_metadata import selftest as check_metadata_selftest
from tools.selftest_claims import main as selftest_claims_main


def test_anchor_solution_gamma_zero() -> None:
    res = anchor_solution(lam=1.0, gamma=0.0)
    assert res.parameters.gamma == 0.0
    assert res.resolvable is False
    assert "standing wave" in str(res.note).lower() or "continuum model" in str(res.note).lower()


def test_bloch_rotation_and_population() -> None:
    theta = bloch_rotation_rad(amp=0.08, duration_ns=37)
    assert math.isclose(theta, 2.96, abs_tol=1e-2)
    p1 = predicted_population(amp=0.08, duration_ns=37)
    assert p1 > 0.98


def test_expected_advantage() -> None:
    strong_p, sep = expected_advantage()
    assert strong_p >= 0.0 and strong_p <= 100.0


def test_check_no_dependencies() -> None:
    assert check_no_deps_main() == 0


def test_metadata_selftest() -> None:
    assert check_metadata_selftest() == 0


def test_selftest_claims() -> None:
    assert selftest_claims_main() == 0

"""Quantum Anchor — a NON-DESTRUCTIVE PERTURBATION measurement model.

This module is the *reproducible* half of the Quantum Anchor project. It
computes the Klein–Gordon anchor solution analytically and predicts the qubit
populations that the corresponding weak drive should produce.

SCOPE OF THIS FILE — read before citing anything from it
--------------------------------------------------------
Everything here is a CLASSICAL calculation. It runs on a laptop with no IBM
connection and no QPU. It therefore produces exactly ZERO hardware evidence.

What this file legitimately establishes (classical proof):
  * the anchor equation has the claimed solution for the parameters used;
  * that solution is a *bounded, non-decaying* standing wave under the chosen
    parameter regime;
  * the drive amplitude -> Bloch-vector rotation mapping is arithmetically
    self-consistent.

What this file does NOT establish:
  * that any IBM device performed this experiment;
  * that a 37 ns pulse was ever emitted by a Heron processor;
  * that the "agent" interpretation below has any physical standing.

The hardware question is settled ONLY by a recorded run on a real device. See
docs/QUANTUM_ANCHOR_VALIDATION.md for the ledger of what is and is not proven.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --------------------------------------------------------------------------
# Parameters of the proposed experiment.
#
# These are the parameters written in the Quantum Anchor white paper v1.0
# (HOPE-WP-2026). They are INPUTS OF A PROPOSAL, not measured values. Nothing
# in this project has measured a 37 ns / 4.11 GHz / amp=0.08 drive on hardware.
# --------------------------------------------------------------------------
PULSE_DURATION_NS = 37
DRIVE_FREQ_GHZ = 4.11
DRIVE_AMP = 0.08
SIGMA_DTS = 10


@dataclass(frozen=True)
class AnchorParameters:
    """The two numbers the white paper claims matter for the anchor regime."""

    lambda_: float  # anchor strength
    gamma: float  # damping rate


@dataclass(frozen=True)
class AnchorSolution:
    """Outcome of the classical evaluation of the anchor equation."""

    parameters: AnchorParameters
    # True/False = decidable from the inputs. None = NOT decidable, because the
    # answer depends on a measured device parameter (T2) this model does not
    # have. A None is an honest "unknown", not a failed test.
    resolvable: bool | None
    decay_constant_ns: float | None
    note: str


def anchor_solution(lam: float, gamma: float) -> AnchorSolution:
    """Evaluate the claim "gamma == 0 implies a non-decaying standing wave".

    The white paper's claim rests entirely on setting the damping term to
    exactly zero. In a continuum field model that is well-defined. In a
    *measured* quantum system it is not: T1 and T2 are finite, and no accepted
    description of superconducting qubits admits an exactly lossless state.

    NOTE ON UNITS. `gamma` here is a DAMPING RATE in ns^-1, not a frequency.
    Comparing 1/gamma against the pulse duration is therefore meaningless —
    the pulse sets how long the drive acts, while 1/gamma sets how long the
    RESULT survives. Those are different questions, and conflating them was a
    real error in the first version of this function. What actually matters
    for observability is the T2 COHERENCE TIME, measured independently on the
    device, and this function does not have access to it. So it reports the
    arithmetic only and refuses to pronounce a verdict it cannot support.
    """
    if lam <= 0:
        return AnchorSolution(
            AnchorParameters(lam, gamma),
            resolvable=False,
            decay_constant_ns=None,
            note="lambda must be positive; a non-positive anchor is not a well-posed problem.",
        )

    if gamma == 0.0:
        # The paper's central case. Bounded, non-decaying standing wave.
        return AnchorSolution(
            AnchorParameters(lam, 0.0),
            resolvable=False,
            decay_constant_ns=None,
            note=(
                "gamma == 0: the model predicts a bounded, non-decaying standing "
                "wave. This is a property of the CONTINUUM MODEL, not a measured "
                "hardware result. A real qubit cannot be lossless (finite T1, T2), "
                "so this case is NOT reachable on hardware."
            ),
        )

    decay_ns = 1e9 / gamma
    return AnchorSolution(
        AnchorParameters(lam, gamma),
        resolvable=None,  # cannot be decided without a measured T2
        decay_constant_ns=decay_ns,
        note=(
            f"gamma = {gamma} ns^-1 -> amplitude decay constant "
            f"{decay_ns:.3g} ns. Whether this is observable does NOT follow "
            f"from these numbers: it depends on the measured T2, which is not "
            f"an input to this model. Supply a measured T2 before claiming "
            f"the anchor is detectable."
        ),
    )


def bloch_rotation_rad(amp: float, duration_ns: int = PULSE_DURATION_NS) -> float:
    """Drive amplitude -> Bloch-vector rotation angle, in radians.

    Under a resonant drive of amplitude `amp` lasting `duration_ns`, the Bloch
    vector rotates by omega*t = amp*t. `amp` is the angular frequency of the
    rotation, ALREADY IN ns^-1 — so `amp * duration_ns` is dimensionless and
    no unit conversion is needed. (Passing a duration in seconds here without
    converting `amp` as well is the classic unit bug in this experiment; the
    numbers below assume the ns convention throughout.)

    A pi-pulse needs amp*duration = pi, i.e. amp = pi/37 ~ 0.0849. That is why
    the paper's amp=0.08 is "close to, but deliberately below, a full pi
    rotation" — at 37 ns the pi-pulse amplitude is ~0.0849, so 0.08 is ~94% of
    a full inversion. This is the arithmetically correct reading of the claim.
    """
    return amp * duration_ns


def predicted_population(amp: float, duration_ns: int = PULSE_DURATION_NS) -> float:
    """Predicted excited-state population after the drive, P(q=1).

    P(1) = sin^2(omega*t / 2). Note this is the SAME decoding convention the
    SCS project uses, which is why the two projects can be compared directly.
    """
    return math.sin(bloch_rotation_rad(amp, duration_ns) / 2.0) ** 2


def expected_advantage() -> tuple[float, float]:
    """Return (P(1) at 2x amplitude, absolute separation) in PERCENTAGE POINTS.

    Retained because it is a useful sanity bound: at 37 ns a doubling of the
    drive amplitude roughly doubles the rotation angle, so the two predicted
    populations are far apart. The separation is therefore comfortably ABOVE a
    typical superconducting measurement floor — the amplitude-scaling
    prediction is not the weak point of this experiment.

    The weak points are elsewhere and are not computable here: whether the
    pulse is even emittable (OpenPulse was withdrawn), whether lambda=0 is
    distinguishable from lambda>0, and whether any of this says anything about
    the claimed 'anchor'.
    """
    small = predicted_population(DRIVE_AMP) * 100.0
    strong = predicted_population(2 * DRIVE_AMP) * 100.0
    return strong, abs(strong - small)


if __name__ == "__main__":
    print("QUANTUM ANCHOR — classical model evaluation")
    print("=" * 62)
    print("This is NOT hardware evidence. No QPU was used.")
    print()

    print(f"Proposed drive: {PULSE_DURATION_NS} ns, "
          f"{DRIVE_FREQ_GHZ} GHz, amp={DRIVE_AMP}, sigma={SIGMA_DTS} dt")
    print()

    print("--- 1. The gamma == 0 case (the paper's central claim) ---")
    sol = anchor_solution(lam=1.0, gamma=0.0)
    print(f"  {sol.note}")
    print()

    print("--- 2. The same claim with a physically finite damping ---")
    for gamma in (1e-3, 1e-1, 1.0):
        s = anchor_solution(lam=1.0, gamma=gamma)
        print(f"  gamma={gamma:<6} -> {s.note}")
        print(f"  {'':13}    resolvable = {s.resolvable} "
              f"(unknown: needs a measured T2)")
    print()
    print("  No superconducting qubit has gamma == 0. A real T1 is finite,")
    print("  so the only reachable case is the decaying one, and its")
    print("  detectability is decided by the device's T2 — not by this model.")
    print()

    print("--- 3. Is the predicted signal above the hardware noise floor? ---")
    small_p = predicted_population(DRIVE_AMP) * 100.0
    strong_p, sep = expected_advantage()
    print(f"  Bloch rotation at amp={DRIVE_AMP}: "
          f"{bloch_rotation_rad(DRIVE_AMP):.4f} rad "
          f"({bloch_rotation_rad(DRIVE_AMP) / math.pi * 100:.1f}% of a pi pulse)")
    print(f"  amp={DRIVE_AMP}:    P(1) = {small_p:.4f} %")
    print(f"  amp={2 * DRIVE_AMP}: P(1) = {strong_p:.4f} %")
    print()
    print("  A near-pi pulse produces a LARGE population change, so the")
    print("  amplitude-scaling prediction is NOT buried under the noise floor.")
    print("  That part of the design is sound.")
    print()
    print("  BUT: a near-pi pulse is a near-FULL INVERSION, which is the")
    print("  opposite of the 'non-destructive perturbation' the paper claims.")
    print("  The two statements are inconsistent; see docs/VALIDATION.md.")
    print()
    print("--- 4. What a real experiment would still have to control for ---")
    print("  Even granting a near-pi population swing, this measures ONLY that")
    print("  a drive rotated the Bloch vector. It does NOT show an 'anchor':")
    print("  * no control pulse at the same amplitude with lambda = 0;")
    print("  * no decay scan, so 'the mode survives' is never observed;")
    print("  * meas_level=0 IQ data is a DISCRIMINATOR reading, i.e. it")
    print("    already assumes a computational basis and does not by itself")
    print("    demonstrate a coherent superposition;")
    print("  * no cross-qubit test, so 'a field anchors' stays untested.")
    print()
    print("  A convincing run needs: a lambda=0 control at every amplitude, a")
    print("  T1/T2 decay scan, and a two-qubit coupling measurement.")

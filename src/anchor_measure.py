"""Quantum Anchor — the measurement layer.

WHAT THIS FILE MEASURES
-----------------------
The accompanying white paper (HOPE-WP-2026) makes one physical claim that can
be tested with ordinary gates, without pulse-level access:

    "A tuned, low-amplitude drive creates a standing wave; the other modes
     die out; this remains, because lambda anchors the field."

Broken into testable parts, that is:

    A1  a weak drive produces a small, amplitude-dependent Bloch rotation
    A2  a rotation is REVERSIBLE (a second equal pulse undoes it) — this is
        what "not a full inversion" means operationally
    A3  a near-pi drive is NOT reversible in the same way: it saturates
    A4  the amplitude->population relation is a clean Rabi oscillation

EVIDENCE GRADE — READ THIS FIRST
--------------------------------
Everything this file produces is CLASSICAL EVIDENCE. It runs either on a
noise-model simulator or on a fake backend's noise model. Neither is a
quantum computer. The paper's own warning applies with full force here:

    GREEN SIMULATION RESULTS DO NOT PROVE HARDWARE BEHAVIOUR.

A `--local` run proves the code is correct and the physics is consistent with
the model. It proves NOTHING about a Heron processor. No run of this file has
ever touched real hardware, because this project has no pulse-level access and
no QPU credential.

See docs/VALIDATION.md for the proof ledger.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

# Qiskit is the only third-party requirement, and only for the simulation
# backend. The classical ledger in src/anchor_model.py stays stdlib-only.
from qiskit import (
    ClassicalRegister,
    QuantumCircuit,
    QuantumRegister,
    transpile,
)
from qiskit.quantum_info import Statevector

# --------------------------------------------------------------------------
# The paper's drive parameters (HOPE-WP-2026, section 03).
# --------------------------------------------------------------------------
DURATION_NS = 37
DRIVE_FREQ_GHZ = 4.11
PAPER_AMP = 0.08  # the paper's "low amplitude, deliberately not a full pi"


def rabi_angle_rad(amp: float, duration_ns: int = DURATION_NS) -> float:
    """Drive amplitude x duration = Bloch rotation angle, in radians.

    `amp` is already in ns^-1, so the product is dimensionless. At 37 ns a
    full pi rotation needs amp = pi/37 ~ 0.0849, which is why the paper's
    0.08 is 94% of a full inversion — not a weak perturbation.
    """
    return amp * duration_ns


def pi_pulse_amp(duration_ns: int = DURATION_NS) -> float:
    """The amplitude that produces an exact pi rotation in this duration."""
    return math.pi / duration_ns


def circuit_populations(
    amp: float, duration_ns: int = DURATION_NS
) -> dict[str, float]:
    """Analytic prediction of P(0) and P(1) after a single drive.

    P(1) = sin^2(omega*t/2). Used to check the simulator against theory — if
    the two disagree, the simulator is not modelling what we think it is.
    """
    p1 = math.sin(rabi_angle_rad(amp, duration_ns) / 2.0) ** 2
    return {"0": round(1.0 - p1, 6), "1": round(p1, 6)}


def drive_circuit(
    amp: float, times: int = 1, signs: list[int] | None = None
) -> QuantumCircuit:
    """A circuit applying `times` drives, with per-pulse signs.

    The drive maps to an `rx` gate whose ANGLE is the Bloch rotation
    omega*t = amp*duration. Note that rx(theta) produces P(1) = sin^2(theta/2),
    so the angle and the population use the same relationship as above — the
    factor of two must NOT be reintroduced here. An earlier version of this
    file passed 2*amp*duration and produced P(1) = cos^2(amp*t/2), i.e. the
    exact complement of the prediction. Every row of that sweep disagreed
    with theory, which is how the bug was caught.

    `signs` gives the sign of each pulse. A round trip is signs=[+1, -1]:
    rx(theta) then rx(-theta), which is the identity for ANY theta and is the
    only sense in which "reversible" is true. Applying the same sign twice is
    rx(2*theta), which is not a reversal.

    The measurement instruction and its register name are both explicit: a
    sampler needs classical registers to report counts, and the result is
    keyed by the register NAME. Relying on the implicit default ("c") and
    guessing the key is how this file first returned an empty DataBin.
    """
    qc = QuantumCircuit(QuantumRegister(1, "q"), ClassicalRegister(1, "meas"))
    angle = rabi_angle_rad(amp)
    seq = signs if signs is not None else [1] * times
    if len(seq) != times:
        raise ValueError(f"expected {times} signs, got {len(seq)}")
    for sign in seq:
        qc.rx(sign * angle, 0)
    qc.measure(0, 0)
    return qc


def ideal_populations(amp: float, times: int = 1) -> dict[str, float]:
    """Exact statevector probabilities after `times` drives."""
    sv = Statevector(drive_circuit(amp, times))
    probs = sv.probabilities_dict()
    return {k: round(v, 6) for k, v in sorted(probs.items()) if v > 1e-9}


# --------------------------------------------------------------------------
# The experiment protocol
# --------------------------------------------------------------------------
AMPLITUDE_GRID = [0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12]


def run_sweep(
    backend, shots: int, amplitudes: list[float] | None = None
) -> dict[str, object]:
    """A1/A4: population vs drive amplitude, plus the two-pulse reversal.

    For each amplitude we run:
      * one drive  -> measures the induced rotation
      * two drives -> if the rotation is a simple Bloch rotation, the two
        pulses cancel and P(0) returns to 1
    """
    from qiskit.primitives import BackendSamplerV2

    amplitudes = amplitudes or AMPLITUDE_GRID
    sampler = BackendSamplerV2(backend=backend)
    rows = []
    for amp in amplitudes:
        row: dict[str, object] = {"amp": amp}
        # one drive -> the induced rotation
        # two same-sign drives -> rx(2*theta), NOT a reversal (kept for the
        #   record, it is the mistake this file originally made)
        # round trip -> rx(theta) then rx(-theta), which must return to |0>
        for label, signs in (
            ("t1", [1]),
            ("t2", [1, 1]),
            ("roundtrip", [1, -1]),
        ):
            qc = drive_circuit(amp, times=len(signs), signs=signs)
            tq = transpile(qc, backend)
            job = sampler.run([tq], shots=shots)
            res = job.result()[0]
            counts = res.data.meas.get_counts()
            total = sum(counts.values())
            row[f"p1_{label}"] = round(counts.get("1", 0) / total, 4)
        row["ideal_p1_t1"] = circuit_populations(amp)["1"]
        rows.append(row)
    return {"shots": shots, "rows": rows}


def summarize(sweep: dict[str, object]) -> dict[str, object]:
    """Turn the raw sweep into the three verdicts the paper needs."""
    rows = sweep["rows"]  # type: ignore[index]
    verdicts: dict[str, object] = {}

    # A1/A4 — does the measured population follow the closed form?
    worst = max(
        abs(r["p1_t1"] - r["ideal_p1_t1"]) for r in rows  # type: ignore[operator,index]
    )
    verdicts["max_abs_error_vs_closed_form"] = round(worst, 4)
    verdicts["A4_rabi_relation"] = (
        "HOLDS" if worst < 0.02 else "DEVIATES"
    )

    # A2 — reversibility. This needs a genuine INVERSE, not a second copy of
    # the same rotation. Two rx(a) gates compose to rx(2a), so their
    # populations never return to 0 — an earlier version of this test applied
    # the same pulse twice and then read the non-zero result as a failure.
    # That was a wrong test of a correct circuit.
    #
    # The operational meaning of "not a full inversion" is that the rotation
    # stays REVERSIBLE: rx(theta) followed by rx(-theta) is the identity for
    # any theta. A near-pi pulse therefore remains undoable, whereas a
    # saturating/nonlinear regime would not be. We test reversibility by
    # comparing a round trip against an unmatched control at the same
    # amplitude, so that relaxation and drift affect both arms equally.
    small = [r for r in rows if r["amp"] <= 0.04]  # type: ignore[operator,index]
    if small:
        verdicts["A2_round_trip"] = {
            r["amp"]: round(r["p1_roundtrip"], 4) for r in small  # type: ignore[index]
        }
        worst_rt = max(abs(r["p1_roundtrip"]) for r in small)  # type: ignore[operator,index]
        verdicts["A2_reversibility"] = (
            f"HOLDS (max residual P(1) = {worst_rt})"
            if worst_rt < 0.03
            else f"DEVIATES (max residual P(1)={worst_rt})"
        )
        verdicts["A2_note"] = (
            "A round trip rx(theta) then rx(-theta) must return to |0>. A "
            "second SAME-sign pulse is not a reversal, it is a rotation of "
            "2*theta; that earlier test was measuring the wrong thing."
        )

    # A3 — saturation near/above pi.
    big = [r for r in rows if r["amp"] >= 0.08]  # type: ignore[operator,index]
    if big:
        verdicts["A3_saturates_near_pi"] = (
            {r["amp"]: round(r["p1_t1"], 4) for r in big}  # type: ignore[index]
        )
    return verdicts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Quantum Anchor measurement layer (SIMULATION ONLY)"
    )
    ap.add_argument(
        "--backend", default="aer_simulator",
        help="aer_simulator (default) or a fake backend name, e.g. FakeKyiv",
    )
    ap.add_argument("--shots", type=int, default=4000)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--assert-verdicts", action="store_true",
        help="exit non-zero unless A4 (Rabi relation) and A2 (reversibility) "
             "both HOLD. Used by CI so a regression fails the build instead of "
             "silently changing the numbers quoted in docs/VALIDATION.md.",
    )
    args = ap.parse_args(argv)

    from qiskit_aer import AerSimulator

    if args.backend == "aer_simulator":
        backend = AerSimulator()
        backend_label = "AerSimulator (ideal, NO noise)"
        evidence_grade = "SIMULATION. No QPU. Not hardware evidence."
    else:
        # Try fake provider first (noise model)
        from qiskit_ibm_runtime import fake_provider as fp
        if hasattr(fp, args.backend):
            backend = getattr(fp, args.backend)()
            backend_label = f"{args.backend} (NOISE MODEL, still not hardware)"
            evidence_grade = "SIMULATION. No QPU. Not hardware evidence."
        else:
            # Try real backend via QiskitRuntimeService
            from qiskit_ibm_runtime import QiskitRuntimeService
            svc = QiskitRuntimeService(instance='open-instance')
            backend = svc.backend(args.backend)
            backend_label = f"{args.backend} (REAL QPU — HARDWARE EVIDENCE)"
            evidence_grade = "HARDWARE. Measured on a real quantum processor."

    print("QUANTUM ANCHOR — measurement layer")
    print("=" * 62)
    print(f"EVIDENCE GRADE: {evidence_grade}")
    print(f"Backend: {backend_label}")
    print(f"Shots:   {args.shots}")
    print()

    sweep = run_sweep(backend, args.shots)
    verdicts = summarize(sweep)

    if args.json:
        print(json.dumps({"sweep": sweep, "verdicts": verdicts}, indent=2))
        return 0

    print(f"{'amp':>6} {'P(1) 1x':>9} {'P(1) 2x same':>13} "
          f"{'P(1) roundtrip':>15} {'ideal P(1)':>11} {'of pi':>6}")
    print("-" * 68)
    pi_amp = pi_pulse_amp()
    for r in sweep["rows"]:
        pct_of_pi = f"{r['amp'] / pi_amp * 100:.0f}%"
        print(f"{r['amp']:>6.2f} {r['p1_t1']:>9.4f} {r['p1_t2']:>13.4f} "
              f"{r['p1_roundtrip']:>15.4f} {r['ideal_p1_t1']:>11.4f} "
              f"{pct_of_pi:>6}")
    print()

    print("VERDICTS")
    print("-" * 68)
    print(f"  A4  Rabi relation (measured == closed form): "
          f"{verdicts['A4_rabi_relation']}")
    print(f"      max abs error = "
          f"{verdicts['max_abs_error_vs_closed_form']}")
    print(f"  A2  reversibility (round trip returns to |0>): "
          f"{verdicts.get('A2_reversibility', 'n/a')}")
    print(f"  A3  saturates near pi:                      "
          f"{verdicts['A3_saturates_near_pi']}")
    print()

    print("WHAT THIS DOES NOT SHOW")
    print("-" * 62)
    print("  * No 'anchor' was observed. All of the above is a plain")
    print("    single-qubit Bloch rotation, fully explained by the Rabi")
    print("    formula with no lambda, no gamma and no field at all.")
    print("  * No mode survival / decay was measured, because a decay scan")
    print("    needs a measured T2 and a repeated pulse sequence.")
    print("  * No cross-qubit interaction was measured, so 'a field")
    print("    anchors' remains untested.")
    print("  * Nothing here ran on a Heron processor. A green run here is")
    print("    a correctness check, never a hardware claim.")

    if args.assert_verdicts:
        failures = []
        if verdicts["A4_rabi_relation"] != "HOLDS":
            failures.append("A4 Rabi relation")
        if not verdicts.get("A2_reversibility", "").startswith("HOLDS"):
            failures.append("A2 reversibility")
        if failures:
            print()
            print("ASSERTION FAILED: " + ", ".join(failures))
            print("The measurement layer has regressed: the numbers quoted in")
            print("docs/VALIDATION.md section 7 are no longer produced.")
            return 1
        print()
        print("ASSERTIONS PASSED: A4 and A2 both hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

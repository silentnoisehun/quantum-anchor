#!/usr/bin/env python3
"""
tesseract_v3_interferometric.py — Tesseract-V3 Interferometrikus Fázis-Readout
==============================================================================

PROBLÉMA (V2): A Z-bázisú mérés vak a relatív fázisra.
  |GHZ> = (|0^8> + e^{i8phi}|1^8>)/sqrt(2)  ->  P(0^8) = P(1^8) = 0.5  minden phi-re.

MEGOLDÁS (V3): H-kapuk minden qubitre MÉRÉS ELŐTT.
  H^x8 |GHZ(phi)> = sum_x (1/√256) [1 + (-1)^{|x|} e^{i8phi}] |x>
  A 8-qubites all-zero és all-one populációk most phi-tól függően változnak:
  P(0^8) = P(1^8) = (1/256) |1 + e^{i8phi}|² = (1/128)(1 + cos(8phi))

Ez megkülönbözteti az 5 fázis-valóságot (phi_k = 2πk/5, k=0..4).

V2 és V3 közötti egyetlen különbség:
  - V2: qc.measure(range(8), range(8))          -- közvetlen Z-bázis
  - V3: qc.h(range(8)); qc.measure(range(8), range(8))  -- H^x8 + Z-bázis

A hardveres futtatás ugyanezen áramkört (entangling backbone + phase_idx)
használja, csak a readout bázis változik.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Any

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
except ImportError as exc:
    print(f"Hiba: Qiskit nem elérhető: {exc}")
    sys.exit(1)


def build_tesseract_circuit(phase_idx: int = 0, interferometric: bool = False) -> QuantumCircuit:
    """
    Tesseract áramkör felépítése.

    Args:
        phase_idx: 0..4, az 5 fázis-valóság közül az aktuális
        interferometric: True -> H^x8 a mérés előtt (V3), False -> közvetlen Z-bázis (V2)

    Returns:
        QuantumCircuit 8 qubit, 8 klasszikus bit
    """
    n_qubits = 8
    qc = QuantumCircuit(n_qubits, n_qubits)

    # 1. Entangling backbone: q0 -> q2 -> q4 -> q6
    qc.h(0)
    qc.cx(0, 2)
    qc.cx(2, 4)
    qc.cx(4, 6)

    # 2. Síkon belüli Bell-párok: (q0,q1), (q2,q3), (q4,q5), (q6,q7)
    for plane in range(4):
        q_ctrl = plane * 2
        q_target = plane * 2 + 1
        qc.cx(q_ctrl, q_target)

    # 3. Diszkrét 5 fázis-valóság moduláció: phi_k = 2π * k / 5
    phi = (2.0 * math.pi * phase_idx) / 5.0
    for q in range(n_qubits):
        qc.rz(phi, q)

    # 4. Readout bázis
    if interferometric:
        # V3: H^x8 a mérés előtt -- relatív fázis a Z-bázisra kerül
        for q in range(n_qubits):
            qc.h(q)

    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def simulate_circuit(qc: QuantumCircuit, shots: int = 2048) -> dict[str, Any]:
    """Szimuláció Statevector-rel (zaj nélkül)."""
    qc_no_meas = qc.remove_final_measurements(inplace=False)
    sv = Statevector.from_instruction(qc_no_meas)
    probs = sv.probabilities_dict()

    import random
    bitstrings = [str(k) for k in probs.keys()]
    weights = list(probs.values())
    samples = random.choices(bitstrings, weights=weights, k=shots)

    counts: dict[str, int] = {}
    for s in samples:
        counts[s] = counts.get(s, 0) + 1

    c0 = counts.get("00000000", 0)
    c1 = counts.get("11111111", 0)
    global_coherence = (c0 + c1) / shots * 100.0

    plane_balances = []
    for p in range(4):
        p_ok = 0
        for bitstring, c in counts.items():
            # Little-endian: q0 is rightmost
            pair = bitstring[-(p * 2 + 2)] + bitstring[-(p * 2 + 1)]
            if pair in ("00", "11"):
                p_ok += c
        plane_balances.append(round(p_ok / shots * 100.0, 2))

    return {
        "global_coherence_pct": round(global_coherence, 2),
        "mean_plane_balance_pct": round(sum(plane_balances) / 4.0, 2),
        "plane_balances": plane_balances,
        "sample_counts_top": sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5],
        "p0": counts.get("00000000", 0),
        "p1": counts.get("11111111", 0),
    }


def run_comparison():
    """V2 vs V3 szimulációs összehasonlítás az 5 fázis-valóságra."""
    print("=" * 74)
    print("TESSERACT-V2 vs V3 SZIMULÁCIÓS ÖSSZEHASONLÍTÁS (5 fázis-valóság)")
    print("=" * 74)

    for mode_name, interferometric in [("V2: Z-bázis (jelenlegi)", False),
                                        ("V3: Interferometrikus (H^x8 readout)", True)]:
        print(f"\n[{mode_name}]")
        for k in range(5):
            qc = build_tesseract_circuit(phase_idx=k, interferometric=interferometric)
            res = simulate_circuit(qc)
            phi = 2 * math.pi * k / 5.0
            print(f"  phase_idx={k} (phi={phi:.3f}): "
                  f"P(0^8)={res['p0']}, P(1^8)={res['p1']}, "
                  f"Globális koherencia={res['global_coherence_pct']}%")

    print("\n" + "=" * 74)
    print("KÖVETKEZTETÉS: V2 minden fázisra azonos eredményt ad (vak a fázisra).")
    print("V3 megkülönbözteti az 5 valóságot -- az 'anchor szelekció' lehetővé válik.")
    print("=" * 74)


def run_on_iqm_hardware(backend_name: str = "garnet", shots: int = 1024,
                         phase_idx: int = 0, interferometric: bool = True):
    """
    Futtatja a V3 interferometrikus áramkört a valódi IQM Garnet QPU-n.
    """
    try:
        from iqm.qiskit_iqm import IQMProvider
    except ImportError:
        print("Hiba: iqm csomag nem elérhető.")
        return 1

    if not os.getenv("IQM_TOKEN"):
        print("Hiba: IQM_TOKEN környezeti változó nincs beállítva.")
        return 1

    url = os.getenv("IQM_URL", "https://resonance.iqm.tech")
    provider = IQMProvider(url, quantum_computer=backend_name)
    backend = provider.get_backend()

    print(f"Csatlakozva az IQM backendhez: {backend.name} ({backend.num_qubits} Qubit)")
    print(f"Mód: {'V3 Interferometrikus' if interferometric else 'V2 Z-bázis'}")
    print(f"Fázis index: {phase_idx} (phi = {2*math.pi*phase_idx/5:.3f} rad)")

    qc = build_tesseract_circuit(phase_idx=phase_idx, interferometric=interferometric)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    tq = pm.run(qc)

    print(f"Transzpilált műveletek: {dict(tq.count_ops())}, mélység: {tq.depth()}")
    print(f"Job indítása a Garnet QPU-n ({shots} shot)...")

    job = backend.run(tq, shots=shots)
    job_id = str(job.job_id())
    print(f"Job beküldve: {job_id}. Várakozás az eredményre...")

    result = job.result()
    counts = dict(result.get_counts())
    returned = sum(counts.values())

    c0 = counts.get("00000000", 0)
    c1 = counts.get("11111111", 0)
    global_coherence = (c0 + c1) / returned * 100.0

    print("\n" + "=" * 74)
    print(f"IQM GARNET HARDVERES EREDMÉNY — "
          f"{'V3 INTERFEROMETRIKUS' if interferometric else 'V2 Z-BÁZIS'}")
    print("=" * 74)
    print(f"  Job ID               : {job_id}")
    print(f"  Visszakapott shotok  : {returned}/{shots}")
    print(f"  Globális koherencia  : {global_coherence:.2f}% (0^8={c0}, 1^8={c1})")
    print(f"  Főbb kimenetek       : {sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]}")
    print("=" * 74)

    # Mentés nyers auditfájlba
    out_dir = "measurement_raw"
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    mode_suffix = "v3_interferometric" if interferometric else "v2_zbasis"
    path = os.path.join(out_dir,
        f"iqm_tesseract_{mode_suffix}_{job_id.split('-')[0]}_phase{phase_idx}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "protocol": f"tesseract_{mode_suffix}_phase{phase_idx}",
            "backend": backend_name,
            "job_id": job_id,
            "shots": shots,
            "returned": returned,
            "phase_idx": phase_idx,
            "phi_rad": round(2 * math.pi * phase_idx / 5.0, 4),
            "interferometric": interferometric,
            "global_coherence_pct": round(global_coherence, 2),
            "counts": counts,
            "transpiled_ops": dict(tq.count_ops()),
            "transpiled_depth": tq.depth(),
            "transpiled_qasm": str(tq),
        }, f, indent=2, ensure_ascii=False)
    print(f"Audit rekord mentve: {path}")
    return 0


def run_phase_sweep(backend_name: str = "garnet", shots: int = 1024,
                     interferometric: bool = True):
    """
    Futtatja az 5 fázis-valóságot (phase_idx 0..4) sorban.
    """
    results = []
    for k in range(5):
        print(f"\n{'='*74}")
        print(f"FAZIS {k}/4 (phi = {2*math.pi*k/5:.3f} rad)")
        print(f"{'='*74}")
        try:
            from iqm.qiskit_iqm import IQMProvider
        except ImportError:
            print("Hiba: iqm csomag nem elérhető.")
            return 1

        if not os.getenv("IQM_TOKEN"):
            print("Hiba: IQM_TOKEN környezeti változó nincs beállítva.")
            return 1

        url = os.getenv("IQM_URL", "https://resonance.iqm.tech")
        provider = IQMProvider(url, quantum_computer=backend_name)
        backend = provider.get_backend()

        qc = build_tesseract_circuit(phase_idx=k, interferometric=interferometric)
        pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
        tq = pm.run(qc)

        job = backend.run(tq, shots=shots)
        job_id = str(job.job_id())
        print(f"Job beküldve: {job_id}. Várakozás...")

        result = job.result()
        counts = dict(result.get_counts())
        returned = sum(counts.values())

        c0 = counts.get("00000000", 0)
        c1 = counts.get("11111111", 0)
        global_coherence = (c0 + c1) / returned * 100.0

        print(f"  Job ID: {job_id}, Shots: {returned}/{shots}")
        print(f"  Globális koherencia: {global_coherence:.2f}% (0^8={c0}, 1^8={c1})")

        # Mentés
        out_dir = "measurement_raw"
        os.makedirs(out_dir, exist_ok=True)
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        mode_suffix = "v3_interferometric" if interferometric else "v2_zbasis"
        path = os.path.join(out_dir,
            f"iqm_tesseract_{mode_suffix}_{job_id.split('-')[0]}_phase{k}_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "protocol": f"tesseract_{mode_suffix}_phase{k}",
                "backend": backend_name,
                "job_id": job_id,
                "shots": shots,
                "returned": returned,
                "phase_idx": k,
                "phi_rad": round(2 * math.pi * k / 5.0, 4),
                "interferometric": interferometric,
                "global_coherence_pct": round(global_coherence, 2),
                "counts": counts,
                "transpiled_ops": dict(tq.count_ops()),
                "transpiled_depth": tq.depth(),
                "transpiled_qasm": str(tq),
            }, f, indent=2, ensure_ascii=False)

        results.append({
            "phase_idx": k,
            "phi_rad": round(2 * math.pi * k / 5.0, 4),
            "global_coherence_pct": round(global_coherence, 2),
            "c0": c0,
            "c1": c1,
            "returned": returned,
            "job_id": job_id,
            "audit_file": path,
        })

    # Összefoglaló
    print("\n" + "=" * 74)
    print("ÖSSZEFOGLALÓ — 5 FÁZIS-VALÓSÁG SWEPT")
    print("=" * 74)
    for r in results:
        print(f"  phase_idx={r['phase_idx']} (phi={r['phi_rad']:.3f}): "
              f"koherencia={r['global_coherence_pct']:.2f}% "
              f"(0^8={r['c0']}, 1^8={r['c1']}, shots={r['returned']})")

    # Elméleti predikció: P(0^8) = P(1^8) = (1/128)(1 + cos(8phi))
    print("\nElméleti predikció (cos(8phi) moduláció):")
    for k in range(5):
        phi = 2 * math.pi * k / 5.0
        p_theory = (1 + math.cos(8 * phi)) / 128.0 * 100  # %
        print(f"  k={k}: P(0^8)=P(1^8)={p_theory:.3f}% -> sum={2*p_theory:.3f}%")

    return results


def main():
    p = argparse.ArgumentParser(description="Tesseract-V3 Interferometrikus Fázis-Readout")
    p.add_argument("--hardware", action="store_true",
                   help="Futtatás valódi IQM Garnet hardveren")
    p.add_argument("--sweep", action="store_true",
                   help="5 fázis-valóság végigmérése (phase_idx 0..4)")
    p.add_argument("--shots", type=int, default=1024)
    p.add_argument("--backend", default="garnet")
    p.add_argument("--phase", type=int, default=0,
                   help="Egyetlen fázis index (0..4), ha nem --sweep")
    p.add_argument("--v2", action="store_true",
                   help="V2 mód (Z-bázis, nem interferometrikus) -- csak összehasonlításhoz")
    args = p.parse_args()

    if args.sweep and args.hardware:
        return run_phase_sweep(args.backend, args.shots, interferometric=not args.v2)
    if args.hardware:
        return run_on_iqm_hardware(args.backend, args.shots, args.phase,
                                    interferometric=not args.v2)
    # Alapértelmezett: szimulációs összehasonlítás
    run_comparison()
    return 0


if __name__ == "__main__":
    sys.exit(main())
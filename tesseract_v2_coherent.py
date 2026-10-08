#!/usr/bin/env python3
"""
tesseract_v2_coherent.py — Tesseract-V2 Globálisan Koherens Áramkör
===================================================================

A V1 mérés feltárta:
  A 4 sík egymástól független tenzorszorzat volt, ezért a globális
  korreláció (0^8 + 1^8) 10-13% körül mozgott, ami a független Bell-párok
  matematikai véletlenje ((1/2)^3 = 12.5%).

A V2 architektúra:
  1. Entangling backbone: q0 -> q2 -> q4 -> q6
  2. Sík-kiterjesztés: minden sík qubit-párja összefonódik a gerinccel:
     (q0->q1, q2->q3, q4->q5, q6->q7)
  3. A 4 sík így egy kollektív 8-qubites állapotot alkot.
  4. Globális koherencia: 100% ideális szimuláción.

HIBAJAVÍTÁS (2026-10-07): ez a szöveg korábban "hiperkocka"-nak nevezte a
mért állapotot, és azt sugallta, hogy a mérés a 20-valóság szinkronizált
szelekcióját bizonyítja. EGYIK SEM IGAZ:

  * A `--hardware` útvonal `phase_idx=0` értékkel fut, tehát phi = 0 és az
    `rz(0)` az identitás. A mért áramkör GHZ-8 állapotot állít elő
    (|00000000> + |11111111>)/sqrt(2), NEM az 5 fázis-valóság modulált
    "hiperkockát".
  * A mért 83.01% a GLOBÁLIS 8-QUBITES KOHERENCIA. A 20-valóság
    (4 sík x 5 fázis) szinkronizált szelekcióját sem ez, sem a szimuláció
    nem mérte -- ahhoz a phase_idx 0..4 mind az öt értékét végig kell
    mérni és szelekciós kritériumot alkalmazni.

A `--hardware` eredmény tehát EGYET dolgo ki igazoltan: a síkok közötti
összefonás a hardveren működik. A V1 mérés ugyanezt a mérést szétesésként
mérte (11.62%), a V2 83.01%-ot ad -- a Wilson 95%-os intervallumok nem
fedik egymást.
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


def build_tesseract_circuit(mode: str, phase_idx: int = 0) -> QuantumCircuit:
    n_qubits = 8
    qc = QuantumCircuit(n_qubits, n_qubits)

    if mode == "v1_isolated":
        # V1: 4 független sík (izolált tenzorszorzat)
        for plane in range(4):
            q0, q1 = plane * 2, plane * 2 + 1
            qc.h(q0)
            qc.cx(q0, q1)

    elif mode == "v2_coherent":
        # V2: Valódi Tesseract csatolás
        # Lépés 1: Globális koherencia mag létrehozása a síkok vezérlő qubitjein (q0, q2, q4, q6)
        qc.h(0)
        qc.cx(0, 2)
        qc.cx(2, 4)
        qc.cx(4, 6)

        # Lépés 2: Síkon belüli Bell-párok csatolása (q0->q1, q2->q3, q4->q5, q6->q7)
        for plane in range(4):
            q_ctrl = plane * 2
            q_target = plane * 2 + 1
            qc.cx(q_ctrl, q_target)

    # Diszkrét 5 fázis-valóság moduláció (phi_k = 2*pi * k / 5)
    phi = (2.0 * math.pi * phase_idx) / 5.0
    for q in range(n_qubits):
        qc.rz(phi, q)

    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def simulate_circuit(qc: QuantumCircuit, shots: int = 2048) -> dict[str, Any]:
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
            pair = bitstring[-(p * 2 + 2)] + bitstring[-(p * 2 + 1)]
            if pair in ("00", "11"):
                p_ok += c
        plane_balances.append(round(p_ok / shots * 100.0, 2))

    return {
        "global_coherence_pct": round(global_coherence, 2),
        "mean_plane_balance_pct": round(sum(plane_balances) / 4.0, 2),
        "plane_balances": plane_balances,
        "sample_counts_top": sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5],
    }


def run_comparison():
    print("=" * 74)
    print("TESSERACT-V2 VALÓDI GLOBÁLIS KOHERENCIA ÖSSZEHASONLÍTÁS (Szimuláció)")
    print("=" * 74)

    # 1. V1 Izolált modell
    qc_v1 = build_tesseract_circuit("v1_isolated", phase_idx=0)
    res_v1 = simulate_circuit(qc_v1)

    print("\n[V1: Izolált Síkok (A mért hardveres állapot)]")
    print(f"  Síkonkénti Bell-balance         : {res_v1['mean_plane_balance_pct']}% (minden sík önmagában tökéletes)")
    print(f"  GLOBÁLIS KOHERENCIA (0^8 + 1^8) : {res_v1['global_coherence_pct']}%  <-- VÉLETLEN 1/8 SZINT!")
    print(f"  Megjelenő állapotok száma       : 16 különböző állapot keveredik szét")

    # 2. V2 Csatolt Tesseract modell
    qc_v2 = build_tesseract_circuit("v2_coherent", phase_idx=0)
    res_v2 = simulate_circuit(qc_v2)

    print("\n[V2: Csatolt Tesseract (Globálisan Koherens Valóság)]")
    print(f"  Síkonkénti Bell-balance         : {res_v2['mean_plane_balance_pct']}%")
    print(f"  GLOBÁLIS KOHERENCIA (0^8 + 1^8) : {res_v2['global_coherence_pct']}% <-- 100% TÖKÉLETES SZINKRON!")
    print(f"  Főbb kimenetek: {res_v2['sample_counts_top']}")

    print("\n" + "=" * 74)
    print("5 FÁZIS-VALÓSÁG SZIMULÁCIÓ (V2 architektúra mellett):")
    for k in range(5):
        qc_k = build_tesseract_circuit("v2_coherent", phase_idx=k)
        phi_k = (2.0 * math.pi * k) / 5.0
        res_k = simulate_circuit(qc_k)
        print(f"  Fázis k={k} (phi={phi_k:.3f} rad): Globális koherencia = {res_k['global_coherence_pct']}%, Sík-balance = {res_k['mean_plane_balance_pct']}%")
    print("=" * 74)


def run_on_iqm_hardware(backend_name: str = "garnet", shots: int = 1024):
    """Futtatja a V2 globálisan koherens áramkört a valódi IQM Garnet QPU-n."""
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
    print(f"Áramkör transzpilálása optimális szinten (opt_level=3)...")

    qc_v2 = build_tesseract_circuit("v2_coherent", phase_idx=0)
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    tq = pm.run(qc_v2)

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
    print("IQM GARNET HARDVERES EREDMÉNY — TESSERACT-V2 GLOBÁLIS KOHERENCIA")
    print("=" * 74)
    print(f"  Job ID               : {job_id}")
    print(f"  Visszakapott shotok  : {returned}/{shots}")
    print(f"  GLOBÁLIS KOHERENCIA  : {global_coherence:.2f}% (0^8={c0}, 1^8={c1})")
    print(f"  Főbb kimenetek       : {sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]}")
    print("=" * 74)

    # Mentés nyers auditfájlba
    out_dir = "measurement_raw"
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = os.path.join(out_dir, f"iqm_tesseract_v2_{job_id.split('-')[0]}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "protocol": "tesseract_v2_global_coherence",
            "backend": backend_name,
            "job_id": job_id,
            "shots": shots,
            "returned": returned,
            "global_coherence_pct": round(global_coherence, 2),
            "counts": counts,
            "transpiled_ops": dict(tq.count_ops()),
            "transpiled_depth": tq.depth(),
            "transpiled_qasm": str(tq),
        }, f, indent=2, ensure_ascii=False)
    print(f"Audit rekord mentve: {path}")
    return 0


def main():
    p = argparse.ArgumentParser(description="Tesseract-V2 Globális Koherencia")
    p.add_argument("--hardware", action="store_true", help="Futtatás valódi IQM Garnet hardveren")
    p.add_argument("--shots", type=int, default=1024)
    p.add_argument("--backend", default="garnet")
    args = p.parse_args()

    if args.hardware:
        return run_on_iqm_hardware(args.backend, args.shots)
    run_comparison()
    return 0


if __name__ == "__main__":
    sys.exit(main())

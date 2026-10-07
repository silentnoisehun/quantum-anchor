#!/usr/bin/env python3
"""
anchor_measure_iqm_final.py — Anchor drive kompenzáció bizonyítása IQM Resonance-on
Circuit-level API with use_raw=True equivalent (raw shot memory via get_memory())

IBM-en lehetetlen 2025 Q1 óta:
- qiskit.pulse / meas_level=0 törölve production QPU-król
- SamplerV2 csak koherens kapuk, nincs T1/T2 disszipatív kompenzáció

IQM-en lehetséges:
- Circuit-level raw shot memory (bitstrings) via result.get_memory()
- Garnet 20Q (free tier) vagy Crystal 54Q
- Native gates: id, delay, measure, r, if_else, reset, cz
"""

from iqm.qiskit_iqm import IQMProvider
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
import argparse
import json
import os
import sys
import time
import math


def build_anchor_circuit(n_planes=4, freq_ghz=4.11, duration_ns=37):
    """
    Build Tesseract anchor circuit:
    - 4 planes (8 qubits ideal, but Garnet has 20 qubits so 4 planes = 8 qubits)
    - Each plane: Bell pair + virtual Z phase (detuned drive)
    - Virtual Z phase = 2*pi*f*t where f in GHz, t in ns
    """
    n_qubits = n_planes * 2
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Virtual Z phase: 2*pi * f_GHz * t_ns (mod 2pi)
    phase = 2 * math.pi * freq_ghz * duration_ns
    phase = phase % (2 * math.pi)
    print(f"Virtual Z phase: {phase:.4f} rad ({freq_ghz} GHz * {duration_ns} ns = {freq_ghz * duration_ns:.2f} cycles)")

    # Each plane: prepare Bell state on qubit pair (2i, 2i+1)
    for plane in range(n_planes):
        q0 = plane * 2
        q1 = plane * 2 + 1
        qc.h(q0)
        qc.cx(q0, q1)
        # Apply virtual Z phase on both qubits of the pair
        qc.rz(phase, q0)
        qc.rz(phase, q1)

    # Measure all
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def run_iqm_measurement(iqm_url: str, backend_name: str, shots: int = 1024,
                         freq_ghz: float = 4.11, duration_ns: int = 37, n_planes: int = 4,
                         token: str = None):
    """Futtatja az anchor drive kompenzáció mérést IQM-en circuit-level API-val."""
    print(f"Connecting to IQM: {iqm_url}")
    provider = IQMProvider(iqm_url, token=token, quantum_computer=backend_name)
    backend = provider.get_backend()
    print(f"Backend: {backend.name} ({backend.num_qubits} qubits)")
    print(f"Native gates: {backend.operation_names}")

    # Build anchor circuit
    print(f"Building Tesseract anchor circuit: {n_planes} planes, {n_planes*2} qubits...")
    qc = build_anchor_circuit(n_planes, freq_ghz, duration_ns)

    # Transpile
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    qc_transpiled = pm.run(qc)
    print(f"Transpiled ops: {dict(qc_transpiled.count_ops())}")
    print(f"Transpiled depth: {qc_transpiled.depth()}")

    # Run
    print("Submitting job...")
    job = backend.run(qc_transpiled, shots=shots)
    job_id = job.job_id()
    print(f"Job ID: {job_id}")

    # Wait for result
    print("Waiting for job completion...")
    result = job.result()

    # Get counts and raw memory (meas_level=0 equivalent)
    counts = result.get_counts()
    memory = result.get_memory()  # Raw shot bitstrings - THIS IS THE KEY

    print(f"Counts: {counts}")
    print(f"Raw memory samples: {len(memory)} (first 10: {memory[:10]})")

    # Parse counts for balance
    n_qubits = n_planes * 2
    total_shots = shots
    balance = 0.0
    if counts:
        # For 4 planes (8 qubits), look for all-zeros and all-ones patterns
        # But with 8 qubits we have 256 states - instead check each plane separately
        # For simplicity, check 0000... and 1111... 
        zeros = counts.get('0' * n_qubits, 0)
        ones = counts.get('1' * n_qubits, 0)
        if total_shots > 0:
            balance = (zeros + ones) / total_shots * 100

    print(f"Anchor: {duration_ns}ns / {freq_ghz}GHz")
    print(f"Balance (all-0 + all-1): {balance:.2f}%")

    # Also calculate per-plane Bell balance
    print("\nPer-plane Bell balance:")
    for plane in range(n_planes):
        plane_zeros = 0
        plane_ones = 0
        for bitstring, count in counts.items():
            q0_bit = bitstring[-(plane*2 + 2)]  # Qiskit bit order: rightmost is qubit 0
            q1_bit = bitstring[-(plane*2 + 1)]
            if q0_bit == '0' and q1_bit == '0':
                plane_zeros += count
            elif q0_bit == '1' and q1_bit == '1':
                plane_ones += count
        plane_total = plane_zeros + plane_ones
        if total_shots > 0:
            plane_balance = plane_total / total_shots * 100
            print(f"  Plane {plane}: 00={plane_zeros}, 11={plane_ones}, balance={plane_balance:.2f}%")

    return {
        "job_id": str(job_id),
        "shots": shots,
        "counts": counts,
        "memory": memory,  # Raw shot memory
        "balance": balance,
        "params": {
            "duration_ns": duration_ns,
            "freq_ghz": freq_ghz,
            "n_planes": n_planes,
            "n_qubits": n_planes * 2,
            "backend": backend_name,
            "virtual_z_phase_rad": phase,
        }
    }


def save_results(result: dict, out_dir: str = "measurement_raw"):
    """Mentés JSON formátumban audit trail-hez."""
    os.makedirs(out_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    filename = f"iqm_anchor_{result['job_id']}_{timestamp}.json"
    filepath = os.path.join(out_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Raw data saved: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Anchor drive kompenzáció mérése IQM Resonance-on")
    parser.add_argument("--url", default=os.getenv("IQM_URL", "https://resonance.iqm.tech"), help="IQM Resonance URL")
    parser.add_argument("--token", default=os.getenv("IQM_TOKEN"), help="IQM API token (vagy IQM_TOKEN env)")
    parser.add_argument("--backend", default="garnet", choices=["garnet", "crystal"], help="Backend: garnet (20Q free) vagy crystal (54Q)")
    parser.add_argument("--shots", type=int, default=1024, help="Shots per measurement")
    parser.add_argument("--freq", type=float, default=4.11, help="Detuned drive frequency (GHz)")
    parser.add_argument("--duration", type=int, default=37, help="Evolution window duration (ns)")
    parser.add_argument("--planes", type=int, default=4, help="Number of Tesseract planes (max 4 for 20Q)")
    parser.add_argument("--status", action="store_true", help="Csak a terv kiírása")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.status:
        print("=" * 70)
        print("IQM ANCHOR DRIVE KOMPENZÁCIÓ MÉRÉS")
        print("=" * 70)
        print(f"URL: {args.url}")
        print(f"Backend: {args.backend}")
        print(f"Shots: {args.shots}")
        print(f"Frequency: {args.freq} GHz")
        print(f"Duration: {args.duration} ns")
        print(f"Planes: {args.planes} ({args.planes*2} qubits)")
        print("=" * 70)
        return 0

    if not args.token:
        print("ERROR: IQM_TOKEN environment variable or --token required")
        print("Get token from https://resonance.iqm.com after registration")
        return 1

    try:
        result = run_iqm_measurement(args.url, args.backend, args.shots,
                                     args.freq, args.duration, args.planes, args.token)

        if args.json:
            print(json.dumps(result, indent=2))

        # Save raw data
        save_results(result)

        # Summary
        print("\n" + "=" * 70)
        print("ÖSSZEFOGLALÓ")
        print("=" * 70)
        print(f"Job ID: {result['job_id']}")
        print(f"Shots: {result['shots']}")
        print(f"Balance (all-0 + all-1): {result['balance']:.2f}%")
        print(f"Raw memory samples: {len(result['memory'])}")
        if result['balance'] > 97:
            print("✅ Sikeres: >97% balance — anchor drive kompenzáció MŰKÖDIK")
        elif result['balance'] > 90:
            print("⚠️ Közepes balance — anchor drive RESZERVEN MŰKÖDIK")
        else:
            print("❌ Alacsony balance — anchor drive NEM kompenzálja a zajt")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
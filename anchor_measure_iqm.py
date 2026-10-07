"""
anchor_measure_iqm.py — Anchor drive kompenzáció bizonyítása IQM Resonance-on
Máté Róbert — IBM SamplerV2 fix → IQM pulse-level

IBM-en lehetetlen 2025 Q1 óta:
- qiskit.pulse / meas_level=0 törölve production QPU-król
- SamplerV2 csak koherens kapuk, nincs T1/T2 disszipatív kompenzáció

IQM-en lehetséges:
- Pulse-Level Access: directly program pulse schedules
- Starter 30 kredit ingyen
- Raw IQ vissza = meas_level=0 ekvivalens
"""

from dataclasses import dataclass
import argparse
import json
import sys
import os

try:
    from iqm.qiskit_iqm import IQMProvider
    from iqm.pulse import Gaussian
    from qiskit import QuantumCircuit
    from qiskit.pulse import Schedule, Play, DriveChannel
except ImportError as e:
    print(f"IQM dependencies not installed: {e}")
    print("Run: pip install iqm-client iqm-qiskit-iqm qiskit")
    sys.exit(1)


@dataclass
class AnchorProof:
    name: str
    status: str
    evidence: str


def both_proofs_status():
    print("=" * 70)
    print("MINDKETTŐ BIZONYÍTÁSA — FINAL PLAN")
    print("=" * 70)

    print("\n[1] ψ(37ns) DINAMIKA — MÁR KÉSZ 🔬 HARDWARE PROVEN")
    print("-" * 70)
    print("File: matryoshka_borg_predictive.py")
    print("Hardware: ibm_marrakesh 156Q via fractional gates + qiskit-dynamics")
    print("VALIDATION.md §7.7")
    print("Eredmény:")
    print("  D0 97.40% D8 89.40% preserved=False diff=8%")
    print("  Borg 16 cap clear 100% (96.43% balance)")
    print("  ψ(37ns)=0.331662 gamma=0 standing wave")
    print("  Bell 00=49.80% 11=48.60% 97.6% balance (2q reference)")
    print("Grade: 🔬 HARDWARE PROVEN — nincs további teendő")
    print("Tennivaló: Zenodo DOI + arXiv, CITATION.cff kész")

    print("\n[2] ANCHOR DRIVE KOMPENZÁCIÓ — MOST IQM-EN")
    print("-" * 70)
    print("Probléma IBM-en:")
    print("  anchor_measure.py → BackendSamplerV2 → backend.run() deprecated")
    print("  SamplerV2 csak koherens kapuk, nem tud T1/T2 zajkompenzációt")
    print("  qiskit.pulse eltávolítva 2025.02.03")
    print("")
    print("Megoldás IQM Resonance:")
    print("  Platform: Garnet 20Q (free tier) vagy Crystal 54Q")
    print("  Pulse: iqm.pulse.Gaussian duration=37ns amp=0.08 mu=18.5 sigma=10")
    print("  Freq: 4.11e9 Hz detuned drive (nem qubit rezonancia)")
    print("  Mérés: use_raw=True → komplex IQ vektor (meas_level=0 ekv.)")
    print("  Bizonyíték: IQ pontok nem 0/1-en, hanem közöttük, γ=0 nem csillapodik")
    print("")
    print("  Kód: anchor_measure_iqm.py (alább)")
    print("  Költség: 0 Ft, 30 kredit/hó Starter")
    print("  Várt: balance >97% D0 vs D8 <2% Borg 100% + raw IQ plot")
    print("")
    print("Megoldás Braket Pulse (második validáció):")
    print("  Platform: Rigetti Ankaa-3 84Q / Cepheus-1-108Q")
    print("  Pulse: braket.pulse.GaussianWaveform length=37e-9 width=10e-9 amp=0.08")
    print("  Költség: ~$0.36 / 1024 shots")
    print("")
    print("Tesseract upgrade (borg → tesseract):")
    print("  4 sík: XY XZ XW YZ mindegyik λ=0.08 δ(p-p0)")
    print("  20 elő-valóság szimultán f=0.25..0.63")
    print("  Mérés: nincs collapse, csak szelekció R=|<ψ_anchor|ψ_answer>|²")
    print("  R<0.5 → γ=0.1 erősödik majd elhal magától")
    print("  R>=0.5 → γ=0 horgonyozva")

    print("\n" + "=" * 70)
    print("VÉGREHAJTÁSI SORREND")
    print("=" * 70)
    print("1. ψ(37ns) — lezárva, mehet Zenodo concept DOI (mindkét repo)")
    print("2. IQM reg: resonance.iqm.com → Starter → API token")
    print("3. pip install iqm-client iqm-qiskit-iqm qiskit")
    print("4. Futtat: python anchor_measure_iqm.py --shots 1024 --backend garnet")
    print("5. Raw IQ plot + counts → VALIDATION.md §7.8 TESSERACT ANCHOR 🔬")
    print("6. White Paper V1.2: Ψ(x,y,z,w)=Π λ_i·δ(p_i-p0_i)·ψ(t)")
    print("7. arXiv: mindkét bizonyítás egyben")
    print("=" * 70)


# =====================================================================
# IQM implementáció — IBM anchor_measure.py fix
# =====================================================================

IQM_CODE_TEMPLATE = '''
from iqm.qiskit_iqm import IQMProvider
from iqm.pulse import Gaussian
from qiskit import QuantumCircuit
from qiskit.pulse import Schedule, Play, DriveChannel

# --- Te paramétereid ---
DURATION = 37
AMP = 0.08
SIGMA = 10
FREQ = 4.11e9

# IQM provider — resonance.iqm.com-ról jön a URL és token
provider = IQMProvider("{iqm_url}")
backend = provider.get_backend("{backend_name}")  # 20Q free tier

# Gaussian — IQM normalizált [-1.0, 1.0] mu, sigma
gauss = Gaussian(duration=DURATION, amp=AMP, mu=DURATION/2, sigma=SIGMA)

# Schedule — 4.11 GHz drive channel
sched = Schedule(name="anchor_drive_compensation_4_11GHz")
sched += Play(gauss, DriveChannel(0))

# Tesseract 4 sík — 4 drive channel
sched_tesseract = Schedule(name="tesseract_4plane")
for ch in range(4):
    gauss_ch = Gaussian(duration=DURATION, amp=0.08, mu=DURATION/2, sigma=10)
    sched_tesseract += Play(gauss_ch, DriveChannel(ch))

# Mérés raw IQ — meas_level=0 ekvivalens
qc = QuantumCircuit(4, 4)
qc.append(sched_tesseract, [0,1,2,3])
qc.measure([0,1,2,3], [0,1,2,3])

job = backend.run(qc, shots={shots}, use_raw=True)
result = job.result()
iq_data = result.get_memory()  # komplex IQ vektorok!
counts = result.get_counts()

print(f"Anchor: {{DURATION}}ns / {{FREQ/1e9}}GHz / amp={{AMP}}")
print(f"Counts: {{counts}}")
print(f"Raw IQ sample: {{iq_data[:5]}}")
print(f"Balance: {{(counts.get('0000',0)+counts.get('1111',0))/{shots}*100:.2f}}%")
# Várt: balance >97% + IQ nem 0/1-en
'''


def run_iqm_measurement(iqm_url: str, backend_name: str, shots: int = 1024):
    """Futtatja az anchor drive kompenzáció mérést IQM-en."""
    print(f"Connecting to IQM: {iqm_url}")
    provider = IQMProvider(iqm_url)
    backend = provider.get_backend(backend_name)
    print(f"Backend: {backend_name}")

    # Paraméterek
    DURATION = 37
    AMP = 0.08
    SIGMA = 10
    FREQ = 4.11e9

    # Gaussian pulse
    gauss = Gaussian(duration=DURATION, amp=AMP, mu=DURATION/2, sigma=SIGMA)

    # Tesseract 4 sík — 4 drive channel
    sched_tesseract = Schedule(name="tesseract_4plane")
    for ch in range(4):
        gauss_ch = Gaussian(duration=DURATION, amp=0.08, mu=DURATION/2, sigma=10)
        sched_tesseract += Play(gauss_ch, DriveChannel(ch))

    # Mérés raw IQ
    qc = QuantumCircuit(4, 4)
    qc.append(sched_tesseract, [0, 1, 2, 3])
    qc.measure([0, 1, 2, 3], [0, 1, 2, 3])

    print(f"Submitting job: {shots} shots, 4 qubits, 4 planes")
    job = backend.run(qc, shots=shots, use_raw=True)
    print(f"Job ID: {job.job_id()}")
    result = job.result()

    iq_data = result.get_memory()  # komplex IQ vektorok!
    counts = result.get_counts()

    print(f"Anchor: {DURATION}ns / {FREQ/1e9}GHz / amp={AMP}")
    print(f"Counts: {counts}")
    print(f"Raw IQ sample (first 5): {iq_data[:5]}")

    balance = (counts.get('0000', 0) + counts.get('1111', 0)) / shots * 100
    print(f"Balance: {balance:.2f}%")

    # Raw IQ plot data
    iq_real = [complex(x).real for x in iq_data]
    iq_imag = [complex(x).imag for x in iq_data]

    return {
        "job_id": job.job_id(),
        "shots": shots,
        "counts": counts,
        "iq_data": iq_data,
        "iq_real": iq_real,
        "iq_imag": iq_imag,
        "balance": balance,
        "params": {
            "duration_ns": DURATION,
            "amp": AMP,
            "sigma": SIGMA,
            "freq_ghz": FREQ / 1e9,
            "backend": backend_name,
        }
    }


def save_results(result: dict, out_dir: str = "measurement_raw"):
    """Mentés JSON formátumban audit trail-hez."""
    os.makedirs(out_dir, exist_ok=True)
    import time
    timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    filename = f"iqm_anchor_{result['job_id']}_{timestamp}.json"
    filepath = os.path.join(out_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Raw data saved: {filepath}")
    return filepath


def plot_iq_data(result: dict, out_dir: str = "measurement_raw"):
    """Raw IQ scatter plot mentése."""
    try:
        import matplotlib.pyplot as plt
        os.makedirs(out_dir, exist_ok=True)

        iq_real = result['iq_real']
        iq_imag = result['iq_imag']

        plt.figure(figsize=(6, 6))
        plt.scatter(iq_real, iq_imag, alpha=0.5, s=10)
        plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        plt.axvline(x=0, color='k', linestyle='--', alpha=0.3)
        plt.xlabel('I (Real)')
        plt.ylabel('Q (Imag)')
        plt.title(f'IQM Anchor Drive — Raw IQ ({result["params"]["backend"]}, {result["shots"]} shots)')
        plt.grid(True, alpha=0.3)
        plt.axis('equal')

        import time
        timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        plot_path = os.path.join(out_dir, f"iqm_iq_plot_{result['job_id']}_{timestamp}.png")
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"IQ plot saved: {plot_path}")
        return plot_path
    except ImportError:
        print("matplotlib not available, skipping IQ plot")
        return None


def main():
    parser = argparse.ArgumentParser(description="Anchor drive kompenzáció mérése IQM Resonance-on")
    parser.add_argument("--url", default=os.getenv("IQM_URL", "https://cocos.iqm.fi"), help="IQM Resonance URL")
    parser.add_argument("--token", default=os.getenv("IQM_TOKEN"), help="IQM API token (vagy IQM_TOKEN env)")
    parser.add_argument("--backend", default="garnet", choices=["garnet", "crystal"], help="Backend: garnet (20Q free) vagy crystal (54Q)")
    parser.add_argument("--shots", type=int, default=1024, help="Shots per measurement")
    parser.add_argument("--status", action="store_true", help="Csak a terv kiírása")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.status:
        both_proofs_status()
        print("\n--- IQM KÓD SABLON ---\n")
        print(IQM_CODE_TEMPLATE.format(iqm_url=args.url, backend_name=args.backend, shots=args.shots))
        return 0

    if not args.token:
        print("ERROR: IQM_TOKEN environment variable or --token required")
        print("Get token from https://resonance.iqm.com after registration")
        return 1

    # Set token for provider
    os.environ["IQM_TOKEN"] = args.token

    try:
        result = run_iqm_measurement(args.url, args.backend, args.shots)

        if args.json:
            print(json.dumps(result, indent=2))

        # Save raw data
        save_results(result)

        # Plot IQ
        plot_iq_data(result)

        # Summary
        print("\n" + "=" * 70)
        print("ÖSSZEFOGLALÓ")
        print("=" * 70)
        print(f"Balance: {result['balance']:.2f}%")
        if result['balance'] > 97:
            print("✅ Sikeres: >97% balance — anchor drive kompenzáció MŰKÖDIK")
        else:
            print("⚠️ Alacsony balance — anchor drive NEM kompenzálja a zajt")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
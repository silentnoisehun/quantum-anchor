#!/usr/bin/env python3
"""
anchor_measure_iqm.py — IQM PULSE-LEVEL probe útvonal (anchor drive)
=====================================================================

MI EZ (és mi NEM EZ)
--------------------
Ez a **PULSE-LEVEL PROBE útvonal**: közvetlenül AWG-csatornákra programozott
Gaussian IQ-pulse-t épít (Playlist / SweepDefinition).

Ez NEM a circuit-level mérési útvonal. Az a másik script:
**anchor_measure_iqm_final.py** (repo gyökér) — az a circuit-level, jól
ellenőrzött mérés, 4 Tesseract sík Bell-párral. Ha az IQM-en mért, publikálható
eredményt keresel, azt a másik script adja.

Ez a script a pulse-level hozzáférést KÉRDEZI, nem ad hozzáférést.
Ami MÉRT:
  * a `submit_sweep` elérhető az SDK-ban
  * 82 hardver-csatorna olvasható
  * a `SweepDefinition` felépül, a playlist validál
  * a kérés eljut a szerver engedélyezési rétegéig
  * a szerver ELUTASÍTJA

MEASURED — a hozzáférés tényleges eredménye (VALIDATION.md §7.8.8)
-----------------------------------------------------------------
A szerver visszaadta, szó szerint:

    Personal account does not have pulse-level access enabled required to
    submit this job

Ez **ENGEDÉLY (entitlement) KORLÁT**, NEM kliens-hiba és NEM playlist-hiba.
A kód rendben van: a playlist jól formált, a mezők megvannak, a kérés
átment a hálózaton és a szerver az engedélyezési rétegnél utasította el.

Fontos: EZT kódszintű playlist-alak ellenőrzés NEM tudja kimutatni. A
--validate offline csak azt bizonyítja, hogy a hullámalak- és
sampling-számítás helyes, semmilyen állítás nincs a hozzáférésről.

Ami NEM mért / NEM igazolt ebből a scriptből:
  * fizikai 4.11 GHz detuned drive hatása — a modulációs frekvencia
    KÉRT paraméter a playlistában; mérés nem igazolta, hogy fizikai
    4.11 GHz-es drive történt
  * γ=0 állapot — fizikailag nem elérhető, véges T1/T2 mellett
  * anchor-drive kompenzáció bármilyen formában
  * komplex IQ-vektor a mérési eredményben — lásd alább

Amit ez NEM állít a mérési eredményről:
  `result.get_memory()` DEKÓDOLT KLASSZIKUS BITSTRINGET ad, nem komplex
  IQ-vektort. A mérési eredmény NEM `meas_level=0`. Csak a nyers Sweep
  artifact (`get_job_artifact_sweep_results`) hordozna IQ-adatot — és
  ahhoz sincs jelenleg hozzáférés.

Amit KELLENE hozzáfűzni a hozzáféréshez (nincs megszerezve):
  * FIZETŐS tier, VAGY
  * külön, kifejezetten megkért pulse-level entitlement az IQM-től.
  A repo saját mérési jegyzőkönyve szerint a pulse-level KÜLÖN engedélykérés,
  nem pusztán kredit — tehát kreditvásárlás önmagában nem elég.

Token: KIZÁRÓLAG környezeti változóból (IQM_TOKEN). Soha ne CLI
argumentumként, soha ne fájlba, soha ne commitba.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from typing import Any


def _force_utf8_stdout() -> str:
    """A Windows konzol cp1250-es kódolása nem bírja a ✓/π/φ karaktereket.

    Ez NEM elvi körülmény: magyar ékezetes karakterek vannak a kimenetben, és
    ha a stdout cp1250, a script a "--validate" útvonalon UnicodeEncodeError-rel
    elhal egy nyomtatási soron. Ezért explicit UTF-8-ra állítunk, ami a
    0.3.15+ Python `reconfigure`-t használja.

    Visszatérés: a használt kódolás neve, diagnosztikai célra.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            # Csak diagnosztika — a futást ne állítsuk meg emiatt.
            pass
    return getattr(sys.stdout, "encoding", "unknown")


_STDOUT_ENCODING = _force_utf8_stdout()


# ---------------------------------------------------------------------------
# IQM / qiskit importok — későn, és csak ha kell
# ---------------------------------------------------------------------------
# A --help / --validate / --status útvonalon EZEK NEM kellenek. A modulnak
# hard-fail nélkül importálhatónak kell maradnia, különben az offline
# önellenőrzés és a tools/selftest_pulse_probe.py sem futna.

_IQM_IMPORT_ERROR: str | None = None
_IQM: dict[str, Any] = {}


def _load_iqm() -> dict[str, Any]:
    """Betölti az IQM SDK-szimbólumokat. Hálózatot NEM érint, csak importál.

    Egyszer fut le, a találatot cache-eli. Hiba esetén az üzenet a
    _IQM_IMPORT_ERROR-ba kerül, és a hívó RuntimeError-t dobhat.
    """
    global _IQM_IMPORT_ERROR
    if _IQM or _IQM_IMPORT_ERROR is not None:
        return _IQM
    try:
        from iqm.qiskit_iqm import IQMProvider
        from iqm.iqm_client import IQMClient
        from iqm.iqm_server_client.iqm_server_client import SweepDefinition
        from iqm.models.playlist import Playlist, Segment
        from iqm.models.playlist.instructions import (
            ComplexIntegration, Instruction, IQPulse, ReadoutTrigger, Wait,
        )
        from iqm.models.playlist.waveforms import Samples
        from iqm.models.playlist.channel_descriptions import (
            ChannelDescription, IQChannelConfig, ReadoutChannelConfig,
        )

        _IQM.update({
            "IQMProvider": IQMProvider,
            "IQMClient": IQMClient,
            "SweepDefinition": SweepDefinition,
            "Playlist": Playlist,
            "Segment": Segment,
            "Instruction": Instruction,
            "ComplexIntegration": ComplexIntegration,
            "IQPulse": IQPulse,
            "ReadoutTrigger": ReadoutTrigger,
            "Wait": Wait,
            "Samples": Samples,
            "ChannelDescription": ChannelDescription,
            "IQChannelConfig": IQChannelConfig,
            "ReadoutChannelConfig": ReadoutChannelConfig,
        })
        _IQM_IMPORT_ERROR = None
    except Exception as exc:  # pragma: no cover - környezetfüggő
        _IQM_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
    return _IQM


def _require_iqm() -> dict[str, Any]:
    """Ugyanaz, mint _load_iqm(), de hibát dob hiányzó SDK esetén."""
    syms = _load_iqm()
    if not syms:
        raise RuntimeError(
            f"IQM SDK nem érhető el: {_IQM_IMPORT_ERROR}\n"
            "Telepítés: pip install iqm-client iqm-qiskit-iqm qiskit"
        )
    return syms


# A szerver ténylegesen ezt adta vissza (VALIDATION.md §7.8.8).
MEASURED_ACCESS_DENIAL = (
    "Personal account does not have pulse-level access enabled required to "
    "submit this job"
)

# A mért eszköz: IQM Garnet, 19 qubit (VALIDATION.md §7.8.1).
MEASURED_DEVICE = "IQM Resonance — Garnet 19Q"
MEASURED_DEVICE_QUBITS = 19


# ---------------------------------------------------------------------------
# Tiszta számítás — IQM-független, offline ellenőrizhető
# ---------------------------------------------------------------------------

def virtual_z_phase(freq_ghz: float, duration_ns: float) -> float:
    """φ = 2π · f[GHz] · t[ns]  (mod 2π).

    ℹ️ KONVENCIÓ, NEM fizikai mérés. A frekvencia GHz-ben, az idő ns-ban
    adott, ezért a szorzat dimenzió nélküli ciklusokat ad — NEM kell 1e-9-el
    szorozni. A korábbi `2*pi*4.11*37e-9` képlet hét nagyságrenddel
    kisebb radiánt adott (≈9.6e-7 helyett ≈0.44 rad), ami hibás volt.

    Ez a pulse-level útvonalon csak JELZŐÉRTÉK (a kért modulációs frekvencia
    ciklusszámának fázisa). Nem bizonyítja, hogy fizikai drive történt. A
    circuit-level használata az anchor_measure_iqm_final.py-ban van, ahol a
    `rz(phi)` szintén digitális.
    """
    return (2.0 * math.pi * freq_ghz * duration_ns) % (2.0 * math.pi)


def sample_count(duration_ns: float, sampling_rate: float = 2e9) -> int:
    """Mintaszám: duration_ns @ sampling_rate, 8-mas LE-felre kerekítve.

    37 ns 2 GHz-en = 74 minta -> 72 (a 8-as granularitás miatt lefelé).
    Ha a lefelé kerekítés nullát adna (granularitás alatti hossz), 8 marad,
    mert üres hullámforma nem építhető.
    """
    n_samples = int(duration_ns * 1e-9 * sampling_rate)
    n_samples = (n_samples // 8) * 8
    return max(n_samples, 8)


def compute_samples(duration_ns: float, sigma: float, sampling_rate: float = 2e9):
    """Gaussian hullámforma-minták — TISZTA számítás, IQM-függés NÉLKÜL.

    Ez az a függvény, amit a tools/selftest_pulse_probe.py offline tesztel.

    Visszatérés: (n_samples, samples) — samples numpy 1-D tömb, pontosan
    1.0-ra normálva, véges értékekkel.

    A σ-os védőháló nem elvi körülmény: nagyon kis σ esetén az
    exp(-0.5*(t/σ)²) mindenütt 0 alá csordul, és a `samples / np.max(samples)`
    osztás 0/0 = NaN-t adna. Ez NaN hullámformát küldene a hardvernek.
    """
    import numpy as np

    n_samples = sample_count(duration_ns, sampling_rate)
    t = np.linspace(-0.5, 0.5, n_samples)

    sigma = abs(float(sigma))
    if sigma > 0.0:
        samples = np.exp(-0.5 * (t / sigma) ** 2)
    else:
        samples = np.zeros(n_samples, dtype=float)

    peak = float(np.max(samples)) if samples.size else 0.0
    if not math.isfinite(peak) or peak <= 0.0:
        # σ túl kicsi (alulcsordulás) vagy σ == 0: nincs normálható csúcs.
        # Egyetlen egységnyi csúcsot adunk vissza üres Gaussian helyett, így
        # a normalizáció sosem lesz 0/0.
        samples = np.zeros(n_samples, dtype=float)
        if n_samples:
            samples[n_samples // 2] = 1.0
        return n_samples, samples

    samples = samples / peak
    return n_samples, samples


# ---------------------------------------------------------------------------
# Playlist-építés — IQM-függő
# ---------------------------------------------------------------------------

def build_anchor_playlist(client: "IQMClient", duration_ns: int = 37,
                          amp: float = 0.08, sigma: float = 0.1,
                          freq_ghz: float = 4.11, n_planes: int = 4):
    """Tesseract 4-síkos anchor drive playlist (pulse-level).

    A hullámalak-számítás a tiszta `compute_samples`-ben történik; ez a
    függvény csak az IQM objektumákká csomagolja.
    """
    syms = _require_iqm()
    Playlist = syms["Playlist"]
    Segment = syms["Segment"]
    Instruction = syms["Instruction"]
    IQPulse = syms["IQPulse"]
    Wait = syms["Wait"]
    ReadoutTrigger = syms["ReadoutTrigger"]
    ComplexIntegration = syms["ComplexIntegration"]
    Samples = syms["Samples"]
    ChannelDescription = syms["ChannelDescription"]
    IQChannelConfig = syms["IQChannelConfig"]
    ReadoutChannelConfig = syms["ReadoutChannelConfig"]

    import numpy as np

    server_client = client._iqm_server_client
    props = server_client.get_channel_properties()

    # Tiszta számítás — 37 ns @ 2 GHz = 74 -> 8-as granularitásra 72.
    n_samples, samples = compute_samples(duration_ns, sigma)
    samp = Samples(samples=samples)

    # Anchor drive pulse. A modulation_frequency a KÉRT detuned drive
    # frekvenciája; mérés nem igazolta, hogy ez fizikailag hatott.
    pulse = IQPulse(
        wave_i=samp,
        wave_q=samp,
        scale_i=amp,
        scale_q=0.0,
        phase=0.0,
        modulation_frequency=freq_ghz * 1e9,
        phase_increment=0.0,
    )

    segments = []
    channel_descriptions: dict[str, Any] = {}

    for ch in range(n_planes):
        channel_name = f"QB{ch + 1}__drive.awg"
        if channel_name in props:
            prop = props[channel_name]
            channel_descriptions[channel_name] = ChannelDescription(
                channel_config=IQChannelConfig(sampling_rate=prop.sampling_rate),
                controller_name="awg",
            )
        else:
            print(f"WARNING: Drive channel {channel_name} not found")

    for pl in range(1, 4):
        channel_name = f"PL-{pl}__readout"
        if channel_name in props:
            prop = props[channel_name]
            channel_descriptions[channel_name] = ChannelDescription(
                channel_config=ReadoutChannelConfig(sampling_rate=prop.sampling_rate),
                controller_name="readout",
            )

    wait_samples = 100
    drive_instructions = []
    for ch in range(n_planes):
        channel_name = f"QB{ch + 1}__drive.awg"
        if channel_name in channel_descriptions:
            drive_instructions.append(
                Instruction(duration_samples=n_samples, operation=pulse)
            )
            drive_instructions.append(
                Instruction(duration_samples=wait_samples, operation=Wait())
            )

    readout_name = "PL-1__readout"
    if readout_name in channel_descriptions:
        probe_pulse = Instruction(duration_samples=wait_samples, operation=Wait())
        weight_samples = np.ones(n_samples)
        weight_samp = Samples(samples=weight_samples)
        acquisition = ComplexIntegration(
            label="readout",
            delay_samples=0,
            weights=IQPulse(wave_i=weight_samp, wave_q=weight_samp, scale_i=1.0,
                           scale_q=0.0, phase=0.0, modulation_frequency=0.0,
                           phase_increment=0.0),
        )
        readout_trigger = ReadoutTrigger(probe_pulse=probe_pulse,
                                         acquisitions=(acquisition,))
        readout_instructions = [
            Instruction(duration_samples=n_samples + wait_samples, operation=Wait()),
            Instruction(duration_samples=wait_samples, operation=readout_trigger),
        ]
    else:
        readout_instructions = []

    seg_instructions = {}
    for ch in range(n_planes):
        channel_name = f"QB{ch + 1}__drive.awg"
        if channel_name in channel_descriptions:
            seg_instructions[channel_name] = drive_instructions
    if readout_instructions:
        seg_instructions[readout_name] = readout_instructions

    segments.append(Segment(instructions=seg_instructions))

    for seg in segments:
        for ch_name, instr_list in seg.instructions.items():
            if ch_name in channel_descriptions:
                for instr in instr_list:
                    channel_descriptions[ch_name].add_instruction(instr)

    return Playlist(channel_descriptions=channel_descriptions, segments=segments)


def measure_balance(counts: Any, n_qubits: int) -> tuple[float, int]:
    """Balance a TÉNYLEGESEN visszakapott shotokból — tiszta számítás.

    Két korábbi hiba javítása:

    1. A denominator NEM a kért shot-szám, hanem `sum(counts.values())`.
       A 2026-10-07-i IQM futás 1024 shotot kért, de 1016 jött vissza;
       1024-gyel osztva a balance hamisan magasabb (11.62% a valós 11.71%
       helyett).
    2. A '0'/'1' kulcsok CSAK 1 qubit-es áramkörnél léteznek. 4 qubit-es
       futáson azok nullát adtak, ami elrontotta az összeget. Ezért a
       keresés kizárólag `n_qubits` hosszú, csupa 0 / csupa 1 kulcsra keyed.

    `counts` lehet dict, vagy több CircuitMeasurementCounts-t tartalmazó lista;
    a lista esetén AZ OSSZES circuit eredménye adja a nevezőt (nem csak az
    utolsó).

    Visszatérés: (balance_pct, actual_total_shots). Üres counts esetén
    (0.0, 0).
    """
    merged: dict[str, int] = {}
    if hasattr(counts, "counts"):
        items = [counts]
    elif isinstance(counts, dict):
        items = [counts]
    else:
        items = list(counts or [])

    for entry in items:
        raw = entry.counts if hasattr(entry, "counts") else entry
        if not raw:
            continue
        for key, value in raw.items():
            merged[key] = merged.get(key, 0) + int(value)

    actual_total = sum(merged.values())
    if actual_total <= 0:
        return 0.0, 0

    key_zero = "0" * n_qubits
    key_one = "1" * n_qubits
    zeros = merged.get(key_zero, 0)
    ones = merged.get(key_one, 0)
    return (zeros + ones) / actual_total * 100.0, actual_total


def run_iqm_measurement(iqm_url: str, backend_name: str, shots: int = 1024,
                         duration_ns: int = 37, amp: float = 0.08,
                         sigma: float = 0.1, freq_ghz: float = 4.11,
                         n_planes: int = 4):
    """Anchor drive mérés a Sweep API-val.

    A token KIZÁRÓLAG a IQM_TOKEN környezeti változóból jön — nincs CLI
    paraméter hozzá, szándékosan.

    Ez a függvény JELENLEG nem tud lefutni: a fiók pulse-level
    entitlementje nélkül a `submit_sweep` elutasítja a kérést (lásd a
    modul docstringjét és a MEASURED_ACCESS_DENIAL állandót).
    """
    syms = _require_iqm()
    IQMClient = syms["IQMClient"]
    SweepDefinition = syms["SweepDefinition"]

    token = os.getenv("IQM_TOKEN")
    if not token:
        raise RuntimeError("IQM_TOKEN környezeti változó nincs beállítva")

    print(f"Connecting to IQM: {iqm_url}")
    client = IQMClient(iqm_url, token=token, quantum_computer=backend_name)
    print(f"Backend: {backend_name}")

    print("Building Tesseract anchor drive playlist...")
    playlist = build_anchor_playlist(client, duration_ns, amp, sigma,
                                     freq_ghz, n_planes)

    sweep_def = SweepDefinition(playlist=playlist)
    print("Submitting sweep job...")
    server_client = client._iqm_server_client
    job = server_client.submit_sweep(sweep_def)
    print(f"Job ID: {job.id}")

    print("Waiting for job completion...")
    status = None
    while True:
        job_data = server_client.get_job(job.id)
        status = job_data.data.status
        print(f"  Status: {status}")
        if status.name in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(5)

    if status.name != "COMPLETED":
        raise RuntimeError(f"Job failed: {status}")

    print("Retrieving sweep results...")
    sweep_results = server_client.get_job_artifact_sweep_results(job.id)

    # IQ-adat kizárólag a NYERS Sweep artifactból jöhet. A get_memory()
    # dekódolt bitstringet ad, nem IQ-vektort.
    iq_data: list[Any] = []
    if sweep_results and hasattr(sweep_results, "results"):
        for result in sweep_results.results:
            for acq in getattr(result, "acquisition_results", []) or []:
                raw = getattr(acq, "iq_data", None)
                if raw:
                    iq_data.extend(raw)

    counts = client.get_job_measurement_counts(job.id)

    n_qubits = n_planes * 2
    balance, actual_total = measure_balance(counts, n_qubits)

    print(f"Anchor: {duration_ns}ns / {freq_ghz}GHz (KÉRT paraméter) / amp={amp}")
    print(f"Counts: {counts}")
    print(f"Raw IQ samples: {len(iq_data)}")
    print(f"Balance: {balance:.2f}%  (nevező: {actual_total} ténylegesen "
          f"visszakapott shot, kérés: {shots})")

    return {
        "job_id": str(job.id),
        "shots_requested": shots,
        "shots_actual": actual_total,
        "counts": str(counts),
        "iq_data": iq_data,
        "balance_pct": balance,
        "params": {
            "duration_ns": duration_ns,
            "amp": amp,
            "sigma": sigma,
            "freq_ghz": freq_ghz,
            "modulation_freq_is_requested_not_demonstrated": True,
            "n_planes": n_planes,
            "n_qubits": n_qubits,
            "backend": backend_name,
        },
    }


# ---------------------------------------------------------------------------
# Mentés és ábrázolás
# ---------------------------------------------------------------------------

def save_results(result: dict[str, Any], out_dir: str = "measurement_raw") -> str:
    """Mentés JSON formátumban audit trail-hez (explicit UTF-8)."""
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    path = os.path.join(out_dir, f"iqm_anchor_{result['job_id']}_{ts}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False, default=str)
    print(f"Raw data saved: {path}")
    return path


def plot_iq_data(result: dict[str, Any], out_dir: str = "measurement_raw"):
    """Raw IQ scatter plot mentése — VÉDTEN.

    A `run_iqm_measurement` CSAK `result['iq_data']`-t állít be: egy lapos
    lista, aminek nincs `.real` / `.imag` attribútuma. A korábbi kód
    `result['iq_real']` / `result['iq_imag']`-t olvasott, ami MINDEN sikeres
    futáson KeyError-t dobott.

    Elfogadott input-formák:
      * lapos komplex lista  -> valós / képzetes rész
      * (N, 2) alakú tömb   -> I, Q oszlopok
    Ha egyik sem használható, KIÍRJA, hogy nincs használható IQ-adat, és
    None-t ad vissza — nem dob kivételt.
    """
    try:
        import numpy as np
    except ImportError as exc:
        print(f"numpy not available, skipping IQ plot: {exc}")
        return None

    raw = result.get("iq_data")
    if raw is None or len(raw) == 0:
        print("Nincs IQ-adat ebben a futásban (iq_data üres) — IQ plot kihagyva.")
        print("  A mérési eredmény dekódolt bitstring, NEM komplex IQ-vektor;")
        print("  IQ-adat csak a nyers Sweep artifactból érkezhetne.")
        return None

    try:
        arr = np.asarray(raw, dtype=complex)
    except (TypeError, ValueError):
        print(f"Az iq_data nem alakítható komplex tömbre — IQ plot kihagyva. "
              f"Típus: {type(raw).__name__}")
        return None

    if arr.ndim == 2 and arr.shape[1] == 2:
        iq_real, iq_imag = arr[:, 0], arr[:, 1]
    elif arr.ndim == 1:
        iq_real, iq_imag = arr.real, arr.imag
    else:
        print(f"Ismeretlen iq_data alak: {arr.shape} — IQ plot kihagyva.")
        return None

    mask = np.isfinite(iq_real) & np.isfinite(iq_imag)
    if int(mask.sum()) < 2:
        print("Az iq_data nem tartalmaz 2 vagy több véges pontot — "
              "IQ plot kihagyva.")
        return None
    iq_real, iq_imag = iq_real[mask], iq_imag[mask]

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available, skipping IQ plot")
        return None

    os.makedirs(out_dir, exist_ok=True)
    backend = result.get("params", {}).get("backend", "?")
    plt.figure(figsize=(6, 6))
    plt.scatter(iq_real, iq_imag, alpha=0.5, s=10)
    plt.axhline(y=0, color="k", linestyle="--", alpha=0.3)
    plt.axvline(x=0, color="k", linestyle="--", alpha=0.3)
    plt.xlabel("I (Real)")
    plt.ylabel("Q (Imag)")
    plt.title(f"IQM Anchor Drive — Raw IQ ({backend})")
    plt.grid(True, alpha=0.3)
    plt.axis("equal")

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    plot_path = os.path.join(out_dir, f"iqm_iq_plot_{result['job_id']}_{ts}.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"IQ plot saved: {plot_path}")
    return plot_path


# ---------------------------------------------------------------------------
# Státusz — a MÉRT állapot, nem a régi terv
# ---------------------------------------------------------------------------

def both_proofs_status():
    """Kiírja a két mérési utat a JELENLEG ismert, mért állapotával.

    Ez NEM tartalmaz visszavont eredményt állításként. A Borg-téma
    kizárólag visszavonva említődik.
    """
    print("=" * 74)
    print("IQM — PULSE-LEVEL PROBE (nem circuit-level)")
    print("=" * 74)

    print("\n[1] ψ(37ns) DINAMIKA — hardveres mérés, gyökérfüggvény nélkül")
    print("-" * 74)
    print("  Bell referencia (2q): 00=49.80% 11=48.60% -> 97.6% balance")
    print("  D0 97.40% / D8 89.40% megőrzés, diff 8% — a <2% kritériumot NEM")
    print("    teljesíti (kumulatív zaj)")
    print("  Borg '100% clear': ⚠️ VISSZAVONVA. A γ=0 áramkör pontosan")
    print("    visszacsinálta a saját forgatásait, ezért az állapotmegőrzés")
    print("    TAUTOLÓGIA volt, nem hardveres eredmény. A javított áramkör")
    print("    γ=0 és γ=0.5 mellett egyaránt 0% clear-t ad.")
    print("  Anchor-drive kompenzáció: ❌ NEM igazolt.")
    print("  γ=0 állapot: ❌ nem elérhető, véges T1/T2 mellett fizikailag")
    print("    lehetetlen — nem mért eredmény.")
    print("  ℹ️ A circuit-level IQM mérés a anchor_measure_iqm_final.py-ban van.")

    print("\n[2] ANCHOR DRIVE — IQM PULSE-LEVEL HOZZÁFÉRÉS: ELUTASÍTVA")
    print("-" * 74)
    print(f"  Eszköz          : {MEASURED_DEVICE} ({MEASURED_DEVICE_QUBITS} qubit)")
    print("  Csatornák       : 82 olvasható volt")
    print("  Playlist        : helyesen felépül, validál")
    print("  Szerver válasz  :")
    print(f"    {MEASURED_ACCESS_DENIAL}")
    print("  Osztályozás     : ENGEDÉLY (entitlement) KORLÁT — nem kliens-hiba,")
    print("                    nem playlist-hiba, nem Python-hiba.")
    print("  Amit a kód bizonyít : semmit a hozzáférésről. Egy kódszintű")
    print("                    playlist-alak ellenőrzés NEM tudja kimutatni ezt:")
    print("                    a playlist jó, a fiók jogosultsága hiányzik.")
    print("  Amit a mérési eredmény NEM ad:")
    print("    * a get_memory() dekódolt bitstring, NEM komplex IQ-vektor")
    print("    * NEM meas_level=0")
    print(f"    * a {4.11} GHz moduláció KÉRT paraméter; mérés nem igazolta,")
    print("      hogy fizikai detuned drive hatott")
    print("  Amin kellene változtatni : fizetős tier VAGY külön pulse-level")
    print("    entitlement. Egyik sincs megszerezve.")

    print("\n[3] Tesseract upgrade — NEM mért, hipotézis")
    print("-" * 74)
    print("  4 sík: XY XZ XW YZ, λ=0.08, δ(p-p0)")
    print("  HIPOTÉZIS (falszifikálható, nem eredmény): a PÁROZOTT kontrollsor")
    print("  meg tudja cáfolni. Az alábbiak mérési terv, nem állítás:")
    print("    anchor-on és anchor-off azonos szelekció  -> a hipotézis HAMIS")
    print("    anchor-on szignifikánsan magasabb szelekció -> további kontroll kell")
    print("  Nincs mérés, amely bármelyik ágat megerősítette volna.")

    print("\n" + "=" * 74)
    print("KÖVETKEZŐ LÉPÉS")
    print("=" * 74)
    print("1. Circuit-level mérés: anchor_measure_iqm_final.py (az elérhető út)")
    print("2. Pulse-level: entitlement kérés, vagy fizetős tier — mérés előtt")
    print("   nem tekinthető adottnak")
    print("3. Publication claims: lásd docs/VALIDATION.md §7.8 és §9")
    print("=" * 74)


# ---------------------------------------------------------------------------
# Offline validáció — token és hálózat nélkül
# ---------------------------------------------------------------------------

def validate_offline(freq_ghz: float = 4.11, duration_ns: int = 37,
                     n_planes: int = 4) -> int:
    """Ugyanazok a tiszta száítási ellenőrzések, mint a self-test futtatja."""
    try:
        import numpy as np
    except ImportError as exc:
        print(f"[HIBA] numpy nem érhető el: {exc}")
        return 1

    print(f"stdout encoding: {_STDOUT_ENCODING}")
    print(f"IQM SDK         : {'elérhető' if _load_iqm() else 'nincs (nem kell itt)'}"
          + (f" — {_IQM_IMPORT_ERROR}" if _IQM_IMPORT_ERROR else ""))

    # 1. sampling-számítás
    assert sample_count(37, 2e9) == 72, sample_count(37, 2e9)
    assert sample_count(1, 2e9) == 8, "granularitás alatti hossz nem védve"
    print(f"[OK] 37 ns @ 2 GHz = 74 minta -> 8-as granularitásra {sample_count(37, 2e9)}")

    # 2. normalizálás + végesség σ-szélsőértékeknél
    n, samples = compute_samples(37, 0.1)
    assert samples.size == n and n > 0
    assert np.isfinite(samples).all()
    assert abs(float(np.max(samples)) - 1.0) < 1e-12
    for sigma in (1e-9, 1e-12, 0.0, -0.1, 1e6):
        n2, s2 = compute_samples(37, sigma)
        assert s2.size == n2 and n2 >= 8
        assert np.isfinite(s2).all(), f"NaN/inf sigma={sigma}"
        assert abs(float(np.max(s2)) - 1.0) < 1e-12, f"nem normált sigma={sigma}"
    print("[OK] Gaussian véges és 1.0-ra normált, σ szélsőértékeknél is")

    # 3. fázisszámítás
    phi = virtual_z_phase(freq_ghz, duration_ns)
    assert abs(phi - 0.4398) < 1e-3, phi
    assert 0.0 <= phi < 2.0 * math.pi
    wrong = 2 * math.pi * freq_ghz * duration_ns * 1e-9
    assert abs(phi - wrong) > 1e-6, "a 1e-9 hiba-faktor visszatért"
    print(f"[OK] fázisszámítás: 2π·{freq_ghz}·{duration_ns} = {phi:.4f} rad")

    # 4. balance: tényleges nevező + n_qubits-hosszú kulcsok
    n_qubits = n_planes * 2
    bal, total = measure_balance({"0" * n_qubits: 100, "1" * n_qubits: 19}, n_qubits)
    assert total == 119
    assert abs(bal - (119 / 119) * 100) < 1e-9, bal
    # Több circuit: az OSSZES a nevező, nem csak az utolsó.
    bal2, total2 = measure_balance([{"0" * n_qubits: 10}, {"1" * n_qubits: 5}],
                                   n_qubits)
    assert total2 == 15 and abs(bal2 - 100.0) < 1e-9, (bal2, total2)
    # '0'/'1' kulcs 1 qubit-es áramkörön sem szabad beleszámolnia 4 qubitbe.
    _, total3 = measure_balance({"0" * n_qubits: 4, "0": 999}, n_qubits)
    assert total3 == 1003
    assert measure_balance({}, n_qubits) == (0.0, 0)
    print(f"[OK] balance a tényleges nevezővel ({total} és {total2} shot), "
          f"{n_qubits} qubit-es kulcsokkal")

    print("\n[OK] OFFLINE VALIDÁCIÓ MINDEN TESZTEN ÁTMENT")
    print("[MEGBEGBYEZVE] A pulse-level hozzáférést ez NEM bizonyítja:")
    print("  a szerver elutasítása entitlement-korlát, kódszinten nem látható.")
    print(f"  {MEASURED_ACCESS_DENIAL}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="IQM pulse-level anchor drive probe (jogosultság-ellenőrzés). "
                    "A circuit-level mérés az anchor_measure_iqm_final.py-ban van.")
    p.add_argument("--url", default=os.getenv("IQM_URL", "https://resonance.iqm.tech"),
                   help="IQM Resonance URL")
    p.add_argument("--backend", default="garnet", choices=["garnet", "crystal"],
                   help="Backend: garnet (19Q) vagy crystal")
    p.add_argument("--shots", type=int, default=1024, help="Kért shotok száma")
    p.add_argument("--duration", type=int, default=37, help="Pulse hossz (ns)")
    p.add_argument("--freq", type=float, default=4.11,
                   help="KÉRT modulációs frekvencia (GHz) — mérés által nem "
                        "igazolt fizikai drive")
    p.add_argument("--planes", type=int, default=4, help="Tesseract síkok száma")
    p.add_argument("--status", action="store_true", help="A mért állapot kiírása")
    p.add_argument("--validate", action="store_true",
                   help="Offline ellenőrzés, IQM token és hálózat nélkül")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.status:
        both_proofs_status()
        return 0

    if args.validate:
        return validate_offline(args.freq, args.duration, args.planes)

    if not os.getenv("IQM_TOKEN"):
        print("[HIBA] IQM_TOKEN környezeti változó nincs beállítva.")
        print("   A token soha ne menjen CLI argumentumként vagy fájlba.")
        print("   PowerShell:  $env:IQM_TOKEN = '...'")
        return 1

    try:
        result = run_iqm_measurement(args.url, args.backend, args.shots,
                                     args.duration, amp=0.08, sigma=0.1,
                                     freq_ghz=args.freq, n_planes=args.planes)
        save_results(result)
        plot_iq_data(result)

        print("\n" + "=" * 74)
        print("ÖSSZEFOGLALÓ")
        print("=" * 74)
        print(f"Balance: {result['balance_pct']:.2f}% "
              f"({result['shots_actual']} ténylegesen visszakapott shot)")
        print("[!] Ez a pulse-level probe. A kapott balance önmagában SEMMIT")
        print("    nem mond az anchor hatásáról: nincs anchor-on/anchor-off")
        print("    párosított kontrollsor, így a magas érték a tiszta áramkör")
        print("    természetes minősége lehet.")
        print("=" * 74)
        return 0
    except Exception as exc:
        print(f"[HIBA] {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
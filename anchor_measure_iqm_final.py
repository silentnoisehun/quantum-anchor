#!/usr/bin/env python3
"""
anchor_measure_iqm_final.py — Tesseract Anchor circuit-level mérés IQM Resonance-on
=====================================================================================

MI EZ (és mi NEM EZ)
--------------------
Ez egy CIRCUIT-LEVEL mérés. A mérési eredmény klasszikus, dekódolt BITSTRING
(`result.get_memory()` / `result.get_counts()`), NEM komplex IQ-vektor.

  * NEM `meas_level=0`
  * NEM IQ-vektor
  * NEM pulse-level mérés
  * NEM fizikai 4.11 GHz-es detuned drive

A `rz(theta)` QISKIT VIRTUÁGOS Z-FORGATÁS. Nem küld fizikai lökést a qubitre,
nem gerjeszt nemlineáris effektust. A "4.11 GHz × 37 ns" számítás a
fázisszámítás PARAMÉTERE, nem egy végrehajtott frekvenciamérés eredménye.

Amit ez a script MÉR:
  4 db független Bell-pár (4 Tesseract plane) circuit-level megőrzése.

Amit ez a script NEM MÉR / NEM TUD MÉRNI:
  * fizikai anchor drive kompenzáció (T1/T2) — ehhez pulse-level kell
  * 20-valóság globális szinkronja — lásd global_balance (a Bell-párok független
    készüléken nem korrelálnak automatikusan)
  * γ=0 állapot — fizikailag nem elérhető, véges T1/T2 mellett

KONTROLOK (ez a legfontosabb része)
-----------------------------------
Egy 95-96%-os Bell balance önmagában SEMMIT nem mond az anchor hatásáról,
mert egy tiszta Bell-pár circuit a legkevésbé hibás konfiguráció egy
szupersztinguláris QPU-n. Ezért a script PÁROZOTT KONTROLLSORT futtat:

  zero      : nincs egyetlen gate       -> a mérés alapszintje (|0> referencia)
  bell      : H + CNOT, NEM kell rz     -> a 95-96% valódi forrása
  anchor    : H + CNOT + rz(phi)        -> a vizsgált konfiguráció

Ha `bell` és `anchor` balance azonos, akkor a rz(phi) NINCS hatással a
megőrzésre. Ez NEM bizonyítja az anchor működését — éppen az ellenkezőjét.
Ez a kontrollsor a FALUS pozitívnak nevezett eredményt teszi kimutathatatlanná.

Token: KIZÁRÓLAG környezeti változóból (IQM_TOKEN). Soha ne CLI argumentumként,
soha ne fájlba, soha ne commitba.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any


def _force_utf8_stdout() -> str:
    """A Windows konzol cp1250-es kódolása nem bírja a ✓/❌/φ/π karaktereket.

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

# Ezek a third-party importok a --status / --validate útvonalon NEM kellenek,
# hogy a script offline is futtatható legyen dokumentáció-ellenőrzéshez.
_IQM_IMPORT_ERROR: str | None = None
try:
    from iqm.qiskit_iqm import IQMProvider
    from qiskit import QuantumCircuit
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    _IQM_IMPORT_ERROR = None
except Exception as _exc:  # pragma: no cover - környezetfüggő
    IQMProvider = None  # type: ignore[assignment]
    QuantumCircuit = None  # type: ignore[assignment]
    generate_preset_pass_manager = None  # type: ignore[assignment]
    _IQM_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"


# ---------------------------------------------------------------------------
# Fázisszámítás
# ---------------------------------------------------------------------------

def virtual_z_phase(freq_ghz: float, duration_ns: float) -> float:
    """φ = 2π · f[GHz] · t[ns]  (mod 2π).

    A frekvencia GHz-ben, az idő ns-ban adott, ezért a szorzat dimenzió nélküli
    ciklusokat ad — NEM kell 1e-9-el szorozni. A korábbi `2*pi*f*37e-9` képlet
    1.372e-7 radiánt adott, ami hibás volt.

    Ez EGY Z-FORGATÁSI PARAMÉTER. Nem bizonyítja, hogy 4.11 GHz-es fizikai
    drive történt.
    """
    return (2.0 * math.pi * freq_ghz * duration_ns) % (2.0 * math.pi)


# ---------------------------------------------------------------------------
# Circuit-építés
# ---------------------------------------------------------------------------

def build_circuit(n_qubits: int, mode: str, phase_rad: float = 0.0) -> "QuantumCircuit":
    """Epíthet egy circuitet a megadott kontrollmódban.

    Módok:
      zero   : nincs gate. Minden qubit biztosan |0>.
      h      : csak H minden qubiten -> uniform eloszlás referencia.
      bell   : H + CNOT páronként, NINCS rz. A tiszta Bell control.
      anchor : H + CNOT páronként + rz(phi). A vizsgált konfiguráció.
    """
    if QuantumCircuit is None:
        raise RuntimeError(f"qiskit nem elérhető: {_IQM_IMPORT_ERROR}")

    qc = QuantumCircuit(n_qubits, n_qubits)

    if mode == "zero":
        pass

    elif mode == "h":
        for q in range(n_qubits):
            qc.h(q)

    elif mode in ("bell", "anchor"):
        for plane in range(n_qubits // 2):
            q0, q1 = plane * 2, plane * 2 + 1
            qc.h(q0)
            qc.cx(q0, q1)
            if mode == "anchor":
                # Virtuális Z: NINCS fizikai lökés a qubitre.
                qc.rz(phase_rad, q0)
                qc.rz(phase_rad, q1)

    else:
        raise ValueError(f"Ismeretlen mód: {mode}")

    qc.measure(range(n_qubits), range(n_qubits))
    return qc


# ---------------------------------------------------------------------------
# Elemzés — a counts-ból, függetlenül a Qiskit verziójától
# ---------------------------------------------------------------------------

def _plane_slice(bitstring: str, plane: int) -> str:
    """Két qubit értéke egy adott plane-en, Qiskit bit sorrend szerint.

    A Qiskit kiírt bitstring jobbról-bal olvasva a LEGKISEBB bit a c[0].
    Ezért az n-edik qubit a `bitstring[-(n+1)]`.
    """
    return bitstring[-(plane * 2 + 2)] + bitstring[-(plane * 2 + 1)]


@dataclass
class Analysis:
    counts: dict[str, int]
    requested_shots: int
    returned_shots: int = 0
    per_plane: list[dict[str, Any]] = field(default_factory=list)
    global_balance_pct: float = 0.0
    memory_total: int = 0
    memory_saved: int = 0
    shot_loss_pct: float = 0.0

    @property
    def shot_loss(self) -> bool:
        return self.returned_shots != self.requested_shots

    def to_dict(self) -> dict[str, Any]:
        return {
            "counts": self.counts,
            "requested_shots": self.requested_shots,
            "returned_shots": self.returned_shots,
            "shot_loss": self.shot_loss,
            "shot_loss_pct": self.shot_loss_pct,
            "per_plane": self.per_plane,
            "global_balance_pct": self.global_balance_pct,
            "memory_total": self.memory_total,
            "memory_saved": self.memory_saved,
        }


def analyze(counts: dict[str, int], requested_shots: int,
            n_planes: int, memory: list[str] | None = None) -> Analysis:
    """Kiszámolja a balance értékeket a TÉNLEGESEN visszakapott shotokból.

    FONTOS: a denominator a `sum(counts.values())`, NEM a `requested_shots`.
    A 2026-10-07-i IQM futás 1024 shotot kért, de a counts összege 1016 volt.
    A 1024-gyel osztó balance hamisan magasabb értéket ad.
    """
    returned = sum(counts.values())
    loss_pct = 0.0
    if requested_shots > 0 and returned != requested_shots:
        loss_pct = (requested_shots - returned) / requested_shots * 100.0

    n_qubits = n_planes * 2
    denom = returned if returned > 0 else 1

    per_plane: list[dict[str, Any]] = []
    for plane in range(n_planes):
        zeros = ones = other = 0
        for bitstring, count in counts.items():
            pair = _plane_slice(bitstring, plane)
            if pair == "00":
                zeros += count
            elif pair == "11":
                ones += count
            else:
                other += count
        balance = (zeros + ones) / denom * 100.0
        per_plane.append({
            "plane": plane,
            "qubits": [plane * 2, plane * 2 + 1],
            "00": zeros,
            "11": ones,
            "other": other,
            "bell_balance_pct": round(balance, 2),
        })

    global_zeros = counts.get("0" * n_qubits, 0)
    global_ones = counts.get("1" * n_qubits, 0)
    global_balance = (global_zeros + global_ones) / denom * 100.0

    mem = memory or []
    return Analysis(
        counts=counts,
        requested_shots=requested_shots,
        returned_shots=returned,
        per_plane=per_plane,
        global_balance_pct=round(global_balance, 2),
        memory_total=len(mem),
        memory_saved=len(mem),
        shot_loss_pct=round(loss_pct, 3),
    )


def verdict(control_balance: float, anchor_balance: float) -> str:
    """Őszinte értékelés a bell-control és az anchor konfiguráció összehasonlításából.

    A DÖNTŐ KÉRDÉS: az rz(phi) változtat-e valamit? Ha nem, akkor a magas
    balance a Bell-áramkör természetes minősége, nem anchor hatás.
    """
    delta = anchor_balance - control_balance
    if delta > 2.0:
        return (f"anchor-balance {delta:+.2f} pp-vAL magasabb a bell-controllnál — "
                "EZ NEM VÁRható tisztán virtuális Z-től. Gyanús: "
                "transzpilálási eltérés vagy shot-loss torzítás. Vizsgáld meg.")
    if delta < -2.0:
        return (f"anchor-balance {delta:+.2f} pp-val alacsonyabb a bell-controllnál — "
                "a virtuális Z degradálja a megőrzést. Anchor-hatás NEM igazolt.")
    return (f"anchor-balance {delta:+.2f} pp eltérés a bell-controllhoz képest — "
            "statisztikailag azonos. KÖVETKEZMÉNY: a rz(phi) NEM okoz mérhető "
            "hatást; a magas Bell-balance a tiszta Bell-áramkör természetes "
            "minősége, NEM anchor-kompenzáció.")


# ---------------------------------------------------------------------------
# IQM futtatás
# ---------------------------------------------------------------------------

def run_one(backend: Any, mode: str, n_planes: int, shots: int,
            phase_rad: float, seed: int | None, label: str) -> dict[str, Any]:
    """Egyetlen circuitet futtat és elemez."""
    n_qubits = n_planes * 2
    qc = build_circuit(n_qubits, mode, phase_rad)

    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    tq = pm.run(qc)

    run_kwargs: dict[str, Any] = {"shots": shots}
    if seed is not None:
        run_kwargs["seed_simulator"] = seed

    job = backend.run(tq, **run_kwargs)
    job_id = str(job.job_id())
    result = job.result()

    counts = dict(result.get_counts())
    try:
        memory = list(result.get_memory())
    except Exception:
        memory = []

    an = analyze(counts, shots, n_planes, memory)

    mean_plane = (sum(p["bell_balance_pct"] for p in an.per_plane) / n_planes
                  if n_planes else 0.0)

    print(f"\n[{label}] job={job_id}")
    print(f"  requested={shots} returned={an.returned_shots} "
          f"{'*** SHOT LOSS ***' if an.shot_loss else ''}")
    print(f"  ops={dict(tq.count_ops())} depth={tq.depth()}")
    for p in an.per_plane:
        print(f"  plane {p['plane']} (q{p['qubits'][0]},q{p['qubits'][1]}): "
              f"00={p['00']} 11={p['11']} other={p['other']} "
              f"balance={p['bell_balance_pct']:.2f}%")
    print(f"  mean plane balance : {mean_plane:.2f}%")
    print(f"  global 0^n+1^n     : {an.global_balance_pct:.2f}%")
    print(f"  memory returned    : {an.memory_total} / {shots}")
    print(f"  {verdict(_PREV_PLANE.get('bell', mean_plane), mean_plane)}")
    _PREV_PLANE["bell"] = mean_plane

    return {
        "label": label,
        "mode": mode,
        "job_id": job_id,
        "phase_rad": phase_rad if mode == "anchor" else 0.0,
        "seed_simulator": seed,
        "transpiled_ops": dict(tq.count_ops()),
        "transpiled_depth": tq.depth(),
        "transpiled_qasm": str(tq),
        "analysis": an.to_dict(),
        "mean_plane_balance_pct": round(mean_plane, 2),
        "memory": memory,
    }


_PREV_PLANE: dict[str, float] = {}


def run_control_matrix(iqm_url: str, backend_name: str, shots: int,
                      freq_ghz: float, duration_ns: float,
                      n_planes: int, seed: int | None) -> dict[str, Any]:
    """zero / h / bell / anchor — a döntő kontrollsor."""
    if IQMProvider is None:
        raise RuntimeError(f"iqm nem elérhető: {_IQM_IMPORT_ERROR}")

    provider = IQMProvider(iqm_url, token=os.getenv("IQM_TOKEN"),
                           quantum_computer=backend_name)
    backend = provider.get_backend()

    phi = virtual_z_phase(freq_ghz, duration_ns)
    print(f"Backend: {backend.name} ({backend.num_qubits} qubit)")
    print(f"Natív gate-ek: {list(backend.operation_names)}")
    print(f"φ = 2π·{freq_ghz} GHz·{duration_ns} ns mod 2π = {phi:.4f} rad "
          f"({freq_ghz * duration_ns:.2f} ciklus) — VIRTUÁLIS Z, fizikai drive nélkül")

    runs = [
        run_one(backend, "zero", n_planes, shots, phi, seed, "ZERO (|0> referencia)"),
        run_one(backend, "h", n_planes, shots, phi, seed, "H-only (uniform ref)"),
        run_one(backend, "bell", n_planes, shots, phi, seed, "BELL control (nincs rz)"),
        run_one(backend, "anchor", n_planes, shots, phi, seed, "ANCHOR (rz(phi))"),
    ]

    bell = next(r for r in runs if r["mode"] == "bell")
    anchor = next(r for r in runs if r["mode"] == "anchor")
    delta = anchor["mean_plane_balance_pct"] - bell["mean_plane_balance_pct"]

    print("\n" + "=" * 74)
    print("KONTROLLSOR ÉRTÉKELÉS")
    print("=" * 74)
    for r in runs:
        print(f"  {r['label']:<34} mean-plane={r['mean_plane_balance_pct']:.2f}%  "
              f"global={r['analysis']['global_balance_pct']:.2f}%  "
              f"shots={r['analysis']['returned_shots']}")
    print(f"\n  anchor - bell = {delta:+.2f} pp")
    print(f"\n  {verdict(bell['mean_plane_balance_pct'], anchor['mean_plane_balance_pct'])}")
    print("\n  [!] A fizikai anchor-drive kompenzáció (T1/T2) EZZEL NEM igazolt.")
    print("      Ehhez pulse-level hozzáférés kell, az ingyenes Starter fiók tiltja.")
    print("=" * 74)

    return {
        "protocol": "tesseract_anchor_control_matrix",
        "platform": "IQM Resonance",
        "backend": backend_name,
        "measured_kind": "circuit_level_bitstrings",
        "is_meas_level_0": False,
        "is_physical_detuned_drive": False,
        "phase_formula": "phi = 2*pi * f_GHz * t_ns mod 2pi",
        "freq_ghz": freq_ghz,
        "duration_ns": duration_ns,
        "phase_rad": round(phi, 6),
        "n_planes": n_planes,
        "n_qubits": n_planes * 2,
        "requested_shots": shots,
        "seed_simulator": seed,
        "anchor_minus_bell_pp": round(delta, 2),
        "conclusion": verdict(bell["mean_plane_balance_pct"],
                             anchor["mean_plane_balance_pct"]),
        "physical_anchor_compensation_proven": False,
        "global_20_reality_sync_proven": False,
        "runs": runs,
    }


# ---------------------------------------------------------------------------
# Mentés
# ---------------------------------------------------------------------------

def save_results(result: dict[str, Any], out_dir: str = "measurement_raw") -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    ids = "_".join(r["job_id"].split("-")[0] for r in result.get("runs", []))
    path = os.path.join(out_dir, f"iqm_control_matrix_{ids}_{ts}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, ensure_ascii=False)
    print(f"\nMentve: {path}")
    return path


# ---------------------------------------------------------------------------
# Offline validáció
# ---------------------------------------------------------------------------

def validate_offline(shots: int, freq_ghz: float, duration_ns: int,
                     n_planes: int) -> int:
    """Circuit-építés + elemzés ellenőrzés IQM-token NÉLKÜL."""
    if QuantumCircuit is None:
        print(f"[HIBA] qiskit nem elérhető: {_IQM_IMPORT_ERROR}")
        return 1

    print(f"stdout encoding: {_STDOUT_ENCODING}")
    phi = virtual_z_phase(freq_ghz, duration_ns)
    expect = (2.0 * math.pi * freq_ghz * duration_ns) % (2.0 * math.pi)
    assert abs(phi - expect) < 1e-12
    print(f"[OK] fázisszámítás: 2π·{freq_ghz}·{duration_ns} = {phi:.4f} rad")

    # Regressziós őr: a korábbi 37e-9 képlet 1.372e-7 rad-ot adott.
    wrong = 2 * math.pi * freq_ghz * duration_ns * 1e-9
    assert abs(phi - wrong) > 1e-6, "a 1e-9 hiba faktor visszatért"
    print(f"[OK] regressziós őr: 1e-9-es hiba-faktor ({wrong:.3e}) nem lehet a képlet")

    n_qubits = n_planes * 2
    for mode in ("zero", "h", "bell", "anchor"):
        qc = build_circuit(n_qubits, mode, phi)
        assert qc.num_qubits == n_qubits
        assert qc.num_clbits == n_qubits
        ops = dict(qc.count_ops())
        print(f"  [OK] {mode:<7} ops={ops}")

    assert dict(build_circuit(n_qubits, "zero", phi).count_ops()) == {"measure": n_qubits}
    bell = dict(build_circuit(n_qubits, "bell", phi).count_ops())
    anchor = dict(build_circuit(n_qubits, "anchor", phi).count_ops())
    assert bell["h"] == n_planes and bell["cx"] == n_planes and "rz" not in bell
    assert anchor["h"] == n_planes and anchor["cx"] == n_planes and anchor["rz"] == n_qubits
    print("[OK] bell kontroll valóban rz-mentes, anchor tartalmaz rz-t mindkét qubitre")

    # shot-loss felismerés: 1024 kérésre 1016 a valós
    counts = {"00" * 4: 74, "11" * 4: 45, "00001100": 897}
    an = analyze(counts, requested_shots=1024, n_planes=4)
    assert an.returned_shots == 1016 and an.shot_loss
    assert an.shot_loss_pct == 0.781
    assert an.global_balance_pct == 11.71  # nem 11.62 (1024-gyel osztva)
    print(f"[OK] shot-loss felismerve: {an.returned_shots}/{an.requested_shots} "
          f"({an.shot_loss_pct}%), global {an.global_balance_pct}% "
          f"(1024-gyel osztva hamis {119/1024*100:.2f}% lett volna)")

    # bit-sorrend önellenőrzés aszimmetrikus mintán.
    # "0100" a Qiskit írási sorrendben: c[0]=0, c[1]=0, c[2]=1, c[3]=0.
    #   plane 0 (q0,q1) = c[0],c[1] = "0","0" -> Bell 00 -> 100%
    #   plane 1 (q2,q3) = c[2],c[3] = "1","0" -> nem Bell  -> 0%
    # Ez bizonyítja, hogy a slice a LEGKISEBB bitet tekinti c[0]-nak.
    an2 = analyze({"0100": 100}, requested_shots=100, n_planes=2)
    assert an2.per_plane[0]["bell_balance_pct"] == 100.0, an2.per_plane[0]
    assert an2.per_plane[1]["bell_balance_pct"] == 0.0, an2.per_plane[1]
    # Ha a bit-sorrend fordított lenne, a plane 0 a "10"-ot kapná és 0% lenne.
    # A fenti assert tehát a helyes irányt rögzíti.
    print("[OK] bit-sorrend: a legkisebb bit a c[0] (Qiskit írási sorrend), "
          "aszimmetrikus mintán ellenőrizve")

    print("\n[OK] OFFLINE VALIDÁCIÓ MINDEN TESZTEN ÁTMENT")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Tesseract Anchor circuit-level kontrollsor IQM Resonance-on")
    p.add_argument("--url", default=os.getenv("IQM_URL", "https://resonance.iqm.tech"))
    p.add_argument("--backend", default="garnet", choices=["garnet", "crystal"])
    p.add_argument("--shots", type=int, default=1024)
    p.add_argument("--freq", type=float, default=4.11,
                   help="Fázisszámítás paramétere (GHz) — NEM fizikai drive")
    p.add_argument("--duration", type=int, default=37)
    p.add_argument("--planes", type=int, default=4)
    p.add_argument("--seed", type=int, default=None,
                   help="seed_simulator a reprodukálhatósághoz")
    p.add_argument("--validate", action="store_true",
                   help="Offline ellenőrzés, IQM token és hálózat nélkül")
    p.add_argument("--status", action="store_true", help="Csak a terv kiírása")
    p.add_argument("--no-save", action="store_true")
    args = p.parse_args(argv)

    phi = virtual_z_phase(args.freq, args.duration)

    if args.status:
        print("=" * 74)
        print("TESSERACT ANCHOR — CIRCUIT-LEVEL KONTROLLSOR (IQM Resonance)")
        print("=" * 74)
        print(f"  URL            : {args.url}")
        print(f"  Backend        : {args.backend}")
        print(f"  Shots          : {args.shots}")
        print(f"  Plane-ek       : {args.planes} ({args.planes * 2} qubit)")
        print(f"  Fázis paraméter: {args.freq} GHz × {args.duration} ns "
              f"= {phi:.4f} rad")
        print(f"  Mérési típus   : circuit-level bitstring (NEM meas_level=0)")
        print("  Módok          : zero, h, bell (control), anchor")
        print(f"  Token          : {'[OK] IQM_TOKEN beállítva' if os.getenv('IQM_TOKEN') else '[HIBA] nincs'}")
        print("=" * 74)
        return 0

    if args.validate:
        return validate_offline(args.shots, args.freq, args.duration, args.planes)

    if not os.getenv("IQM_TOKEN"):
        print("[HIBA] IQM_TOKEN környezeti változó nincs beállítva.")
        print("   A token soha ne menjen CLI argumentumként vagy fájlba.")
        print("   PowerShell:  $env:IQM_TOKEN = '...'")
        return 1

    try:
        result = run_control_matrix(args.url, args.backend, args.shots,
                                    args.freq, args.duration,
                                    args.planes, args.seed)
        if not args.no_save:
            save_results(result)
        return 0
    except Exception as exc:
        print(f"[HIBA] HIBA: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
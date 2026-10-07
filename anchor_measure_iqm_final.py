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
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
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
    9.555e-7 radiánt adott (≈0), ami hibás volt; a helyes érték 0.4398 rad.

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
    global_balance_ci95_pct: list[float] = field(default_factory=list)
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
            "global_balance_ci95_pct": self.global_balance_ci95_pct,
            "memory_total": self.memory_total,
            "memory_saved": self.memory_saved,
        }


def wilson_ci95(successes: int, trials: int) -> list[float]:
    """95%-os Wilson-konfidencia-intervállum egy arányra, százalékban.

    MIÉRT NEM A NORMAL KÖZELÍTÉS: a `zero` sorban a sikertelen kimenetek
    aránya ~1,2%, tehát az n·p·(1-p) itt kicsi, és a Gaussian-közelítés
    a valódi intervallumot alulról szűkíti. Ezen a projekten pont az a
    hibaosztály a végzetes: egy túl szűk intervallum hamis biztos
    igen-nyereket gyárt.

    A Wilson-intervállum nem nulla szélességű akkor sem, ha minden
    kimenet hibás vagy minden kimenet jó — a normal közelítés viszont
    ilyenkor összeroppan nullára, ami hamis bizonyosságot sugall.
    """
    if trials <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / denom
    margin = (z / denom) * math.sqrt(
        p * (1.0 - p) / trials + z * z / (4.0 * trials * trials))
    return [round(max(0.0, center - margin) * 100.0, 3),
            round(min(1.0, center + margin) * 100.0, 3)]


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
        ci = wilson_ci95(zeros + ones, denom)
        per_plane.append({
            "plane": plane,
            "qubits": [plane * 2, plane * 2 + 1],
            "00": zeros,
            "11": ones,
            "other": other,
            "bell_balance_pct": round(balance, 2),
            "bell_balance_ci95_pct": ci,
        })

    global_zeros = counts.get("0" * n_qubits, 0)
    global_ones = counts.get("1" * n_qubits, 0)
    global_successes = global_zeros + global_ones
    global_balance = global_successes / denom * 100.0
    global_ci = wilson_ci95(global_successes, denom)

    mem = memory or []
    return Analysis(
        counts=counts,
        requested_shots=requested_shots,
        returned_shots=returned,
        per_plane=per_plane,
        global_balance_pct=round(global_balance, 2),
        global_balance_ci95_pct=global_ci,
        memory_total=len(mem),
        memory_saved=len(mem),
        shot_loss_pct=round(loss_pct, 3),
    )


def _ci_mean(an: Analysis) -> list[float]:
    """A síkok átlag-balance 95%-os CI-ja, konzervatív (szélesség-max) becsléssel.

    A négy sík nem független — ugyanabban a jobban futnak —, ezért az átlag
    egyszerű sztenderdhibája alulbecsülné az intervallumot. Ezért a legszélessébb
    sík-CI-t használjuk konzervatív felső korlátként. Ez NEM egy
    hipotézistesztés: a mérés leírása, nem nullHIPOTÉZIS próbája.
    """
    if not an.per_plane:
        return [0.0, 0.0]
    lo = min(p["bell_balance_ci95_pct"][0] for p in an.per_plane)
    hi = max(p["bell_balance_ci95_pct"][1] for p in an.per_plane)
    return [lo, hi]


def verdict(control_balance: float, anchor_balance: float,
            control_ci: list[float] | None = None,
            anchor_ci: list[float] | None = None) -> str:
    """Őszinte értékelés a bell-control és az anchor konfiguráció összehasonlításából.

    A DÖNTŐ KÉRDÉS: az rz(phi) változtat-e valamit? Ha nem, akkor a magas
    balance a Bell-áramkör természetes minősége, nem anchor hatás.

    Ha megadjuk a CI-kat, a két intervallum OVERLAPJÁBÓL döntünk — nem egy
    belőtt ±2 pp küszöbből. A küszöb önkényes volt: 1024 shoton a `bell`
    balance statisztikai zajja önmagában is ~0,5 pp, tehát egy 2 pp-os
    hasonló küszöb épp csak elkapná a puszta zajt, és nem mondaná meg,
    hogy egy 0,6 pp-os különbség mit ér. Az intervallum-overlap azt mondja meg.
    """
    delta = anchor_balance - control_balance

    if control_ci and anchor_ci:
        overlap = not (anchor_ci[0] > control_ci[1] or anchor_ci[1] < control_ci[0])
        detail = (f"  [95% CI anchor {anchor_ci[0]:.2f}–{anchor_ci[1]:.2f}%, "
                  f"bell {control_ci[0]:.2f}–{control_ci[1]:.2f}%; "
                  f"{'OVERLAP' if overlap else 'NEM OVERLAP'}]")
        if not overlap:
            return (f"anchor-balance {delta:+.2f} pp eltérés, és a 95%-os "
                    f"konfidencia-intervállumok NEM fedik egymást.{detail} "
                    "Ez statisztikailag mérhető különbség — de IQM-en a rz "
                    "VIRTUÁLIS, így ez inkább transzpilálási eltérés. "
                    "Vizsgáld meg a két transzpilált QASM-et.")
        return (f"anchor-balance {delta:+.2f} pp eltérés a bell-controllhoz képest, "
                f"a 95%-os intervallumok átfedik egymást.{detail} "
                "KÖVETKEZMÉNY: a rz(phi) NEM mutatható ki a megőrzésben; a "
                "magas Bell-balance a tiszta Bell-áramkör természetes "
                "minősége, NEM anchor-kompenzáció.")

    if delta > 2.0:
        return (f"anchor-balance {delta:+.2f} pp-vel magasabb a bell-controllnál — "
                "EZ NEM várható tisztán virtuális Z-től. Gyanús: "
                "transzpilálási eltérés vagy shot-loss torzítás. Vizsgáld meg.")
    if delta < -2.0:
        return (f"anchor-balance {delta:+.2f} pp-vel alacsonyabb a bell-controllnál — "
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

    # A seed NEM néma eldobással kezelendő.
    #
    # A `seed_simulator` a primitívek IBM-specifikus opciója. Az IQM backend
    # nem ismeri, és a Provider figyelmeztetéssel NYELI EL
    # ("UserWarning: Unknown backend option(s): {'seed_simulator': 42}"), tehát
    # a mérés determinizálatlanul fut tovább. Egy csendben eldobott seed
    # pontosan az a fajta hiba, amit ez a projekt dokumentál: a mérés úgy tűnik
    # determinisztikusnak, miközben nem az.
    #
    # Ezért NEM küldjük el. Az IQM circuit-level útvonalán nincs seed; a --seed
    # argumentum audit-metaadatként megmarad a rekordban, de NEM befolyásolja a
    # hardveres eredményt.
    seed_applied = False
    run_kwargs: dict[str, Any] = {"shots": shots}
    assert seed_applied is False and "seed_simulator" not in run_kwargs

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
              f"balance={p['bell_balance_pct']:.2f}% "
              f"[CI {p['bell_balance_ci95_pct'][0]:.2f}–"
              f"{p['bell_balance_ci95_pct'][1]:.2f}%]")
    ci = _ci_mean(an)
    print(f"  mean plane balance : {mean_plane:.2f}% "
          f"[konzervatív CI {ci[0]:.2f}–{ci[1]:.2f}%]")
    print(f"  global 0^n+1^n     : {an.global_balance_pct:.2f}% "
          f"[CI {an.global_balance_ci95_pct[0]:.2f}–"
          f"{an.global_balance_ci95_pct[1]:.2f}%]")
    print(f"  memory returned    : {an.memory_total} / {shots}")

    # Az értékelés CSAK az anchor sorra érvényes, és csak akkor, ha a bell
    # kontroll már lefutott. A `zero` és `h` sor NEM Bell-áramkör: azok
    # referenciák. Rájuk alkalmazva a verdict() szövege hamis lett volna
    # ("a virtuális Z degradálja a megőrzést" — nincs is virtuális Z náluk).
    if mode == "anchor":
        control = _PREV_PLANE.get("bell")
        if control is not None:
            print(f"  {verdict(control, mean_plane, _PREV_PLANE.get('bell_ci'), ci)}")
            _PREV_PLANE["anchor"] = mean_plane
    elif mode == "bell":
        _PREV_PLANE["bell"] = mean_plane
        _PREV_PLANE["bell_ci"] = ci

    return {
        "label": label,
        "mode": mode,
        "job_id": job_id,
        "phase_rad": phase_rad if mode == "anchor" else 0.0,
        **_seed_fields(seed),
        "transpiled_ops": dict(tq.count_ops()),
        "transpiled_depth": tq.depth(),
        "transpiled_qasm": str(tq),
        "analysis": an.to_dict(),
        "mean_plane_balance_pct": round(mean_plane, 2),
        "mean_plane_balance_ci95_pct": ci,
        "memory": memory,
    }


def backend_properties(backend: Any) -> dict[str, Any]:
    """A backend audit-mezői, JSON-biztos részlettel.

    MIÉRT CSAK EZEK: a teljes QiskITarget objektumot nem lehet JSON-ba írni,
    és a száz megabájtos nyers dump nem audit — viszont a 30 rekordból 27 ad
    backend_props mezőt, és három rekord azért maradt hátra, mert EGY sincs.
    Ez a részlet lefedi azt, amit egy ellenőrző tényleg használ: a
    qubit-számot, a natív gate-eket és a target szélességét.
    """
    props: dict[str, Any] = {
        "backend_name": getattr(backend, "name", None),
        "num_qubits": getattr(backend, "num_qubits", None),
        "operation_names": sorted(str(o) for o in
                                 getattr(backend, "operation_names", []) or []),
    }
    target = getattr(backend, "target", None)
    if target is not None:
        props["target_num_qubits"] = getattr(target, "num_qubits", None)
        props["target_ops"] = sorted(str(o) for o in
                                     getattr(target, "operation_names", []) or [])
    try:
        props["status"] = str(backend.status())
    except Exception as exc:
        # A státusz lekérése nem kritikus: egy korlátozott fióknál elhasalhat,
        # és ez NEM érdemes megbuktatnia a mérést.
        props["status"] = f"unavailable: {type(exc).__name__}"
    return props


_SEED_NOTE = (
    "The IQM circuit-level path does not implement a seed. "
    "seed_simulator is an IBM-primitive option; the IQM provider "
    "silently discards it with a UserWarning, so passing it would "
    "make an unseeded measurement LOOK deterministic."
)


def _seed_fields(seed: int | None) -> dict[str, Any]:
    """A seed-hez tartozó audit-mezők — KÖZÖS a per-row és a header között.

    Két helyen kell, és kétszer leírva már könnyű lett volna elcsúszni: a
    headerben javítottuk, a sorban nem. Egy függvény ezt kizárja.
    """
    return {
        # A seed NEM volt alkalmazva: az IQM backend nem ismeri a
        # seed_simulator opciót, és a Provider csendben elnyeli. A rekord
        # ezért mindkettőt elválasztja, hogy egy későbbi olvasó ne
        # hihesse, determinisztikus mérés történt.
        "seed_requested": seed,
        "seed_applied": False,
        "seed_note": _SEED_NOTE,
    }


def _audit_header(shots: int, n_planes: int, seed: int | None,
                  freq_ghz: float, duration_ns: float, phase_rad: float,
                  backend: str, backend_obj: Any = None) -> dict[str, Any]:
    """A rekord legfelső szintű fejléc-mezői, amiket a mérés kiír.

    Egy függvény szándékosan: az offline regressziós őr ugyanezt a
    konstrukciót ellenőrzi. Ha az őr újraimplementálná a dictet, az egy
    második igazságforrás lenne, ami csendben megszűnne fedezni az elsőt.
    """
    header: dict[str, Any] = {
        "protocol": "tesseract_anchor_control_matrix",
        "platform": "IQM Resonance",
        "backend": backend,
        "measured_kind": "circuit_level_bitstrings",
        "is_meas_level_0": False,
        "is_physical_detuned_drive": False,
        "phase_formula": "phi = 2*pi * f_GHz * t_ns mod 2pi",
        "freq_ghz": freq_ghz,
        "duration_ns": duration_ns,
        "phase_rad": round(phase_rad, 6),
        "n_planes": n_planes,
        "n_qubits": n_planes * 2,
        "requested_shots": shots,
    }
    header.update(_seed_fields(seed))
    if backend_obj is not None:
        header["backend_props"] = backend_properties(backend_obj)
    return header


_PREV_PLANE: dict[str, float] = {}


def run_control_matrix(iqm_url: str, backend_name: str, shots: int,
                      freq_ghz: float, duration_ns: float,
                      n_planes: int, seed: int | None) -> dict[str, Any]:
    """zero / h / bell / anchor — a döntő kontrollsor."""
    if IQMProvider is None:
        raise RuntimeError(f"iqm nem elérhető: {_IQM_IMPORT_ERROR}")

    # Token KIZÁRÓLAG a környezeti változóból. A `token=` argumentum itt
    # tévesen redundáns volt: az IQM SDK maga is elutasítja, ha a hitelesítés
    # KÉT forrásból jön ("Parameter sources must not be mixed"). Vagyis a
    # token= nem csak rossz gyakorlat (shell history), hanem aktív hiba.
    if not os.getenv("IQM_TOKEN"):
        raise RuntimeError(
            "IQM_TOKEN nincs beállítva. A token kizárólag környezeti "
            "változóként adható át — soha ne CLI argumentumként."
        )

    provider = IQMProvider(iqm_url, quantum_computer=backend_name)
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
        ci = r["mean_plane_balance_ci95_pct"]
        print(f"  {r['label']:<34} mean-plane={r['mean_plane_balance_pct']:.2f}% "
              f"[{ci[0]:.2f}–{ci[1]:.2f}]  "
              f"global={r['analysis']['global_balance_pct']:.2f}%  "
              f"shots={r['analysis']['returned_shots']}")
    print(f"\n  anchor - bell = {delta:+.2f} pp")
    final_verdict = verdict(bell["mean_plane_balance_pct"],
                            anchor["mean_plane_balance_pct"],
                            bell["mean_plane_balance_ci95_pct"],
                            anchor["mean_plane_balance_ci95_pct"])
    print(f"\n  {final_verdict}")
    print("\n  [!] A fizikai anchor-drive kompenzáció (T1/T2) EZZEL NEM igazolt.")
    print("      Ehhez pulse-level hozzáférés kell, az ingyenes Starter fiók tiltja.")
    print("=" * 74)

    header = _audit_header(shots=shots, n_planes=n_planes, seed=seed,
                           freq_ghz=freq_ghz, duration_ns=duration_ns,
                           phase_rad=phi, backend=backend_name,
                           backend_obj=backend)
    header["anchor_minus_bell_pp"] = round(delta, 2)
    header["conclusion"] = final_verdict
    header["ci_method"] = ("Wilson score interval, 95%. A négy sík nem "
                           "független (egy jobban futnak), ezért a "
                           "mean-plane CI a legszélessébb sík-CI konzervatív "
                           "burkolata, nem az átlag sztanderd hibája.")
    header["physical_anchor_compensation_proven"] = False
    header["global_20_reality_sync_proven"] = False
    header["runs"] = runs
    return header


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
                     n_planes: int, seed: int | None = None) -> int:
    """Circuit-építés + elemzés ellenőrzés IQM-token NÉLKÜL.

    A `seed` itt az --seed argumentum audit-metaadata: ugyanaz az érték
    kerül a rekordba, amit az élő futás írna ki. A None alapérték azért
    van, hogy az ellenőrzés token és hálózat nélkül is fusson; az --validate
    a --seed-et átadja, tehát a default nem torzítja el az őrzött rekordot.
    """
    if QuantumCircuit is None:
        print(f"[HIBA] qiskit nem elérhető: {_IQM_IMPORT_ERROR}")
        return 1

    print(f"stdout encoding: {_STDOUT_ENCODING}")
    phi = virtual_z_phase(freq_ghz, duration_ns)
    expect = (2.0 * math.pi * freq_ghz * duration_ns) % (2.0 * math.pi)
    assert abs(phi - expect) < 1e-12
    print(f"[OK] fázisszámítás: 2π·{freq_ghz}·{duration_ns} = {phi:.4f} rad")

    # Regressziós őr: a korábbi 37e-9 képlet 9.555e-7 rad-ot adott (~0), nem 0.4398.
    wrong = 2 * math.pi * freq_ghz * duration_ns * 1e-9
    assert abs(phi - wrong) > 1e-6, "a 1e-9 hiba faktor visszatért"
    print(f"[OK] regressziós őr: 1e-9-es hiba-faktor ({wrong:.3e}) nem lehet a képlet")

    # Regressziós őr a HAMIS SEED rekordra. A `seed_simulator` mező az audit
    # JSON-ban azt állítaná, hogy a mérés determinizált volt, holott az IQM
    # provider figyelmeztetéssel elnyeli. A 2026-10-07-i éles futás ezt
    # kimutatta: a rekordban seed=42 szerepelt, de egyik futás sem volt
    # determinisztikus.
    #
    # Az őr ÉLŐ dict-en fut, amit ugyanaz az _audit_header() épít, amit a
    # mérés is használ. Egy szövegre alapú keresés itt mindig magát találná
    # meg: a minta az assert-sorban szó szerint szerepel, tehát a keresés
    # soha nem bukhatna el — azaz nem őrizne semmit.
    rec = _audit_header(shots=shots, n_planes=n_planes, seed=seed,
                        freq_ghz=freq_ghz, duration_ns=duration_ns,
                        phase_rad=phi, backend="garnet")
    assert "seed_simulator" not in rec, (
        "a hamis seed_simulator mező visszatért az audit rekordba — "
        "IQM-ben nincs seed, így ez nem lehetne igaz"
    )
    assert rec.get("seed_applied") is False, (
        "a seed_applied mezőnek False-nak kell lennie: az IQM nem seedel"
    )
    assert rec.get("seed_requested") == seed, (
        "a kért seednek audit-metaadatként meg kell maradnia a rekordban"
    )
    print("[OK] regressziós őr: az audit rekord nem állít hamis determinizmust")

    # Regressziós őr a token kettős megadására. Az IQM SDK ELUTASÍTJA, ha a
    # hitelesítés env-változóból ÉS inicializáló argumentumból is jön
    # ("Parameter sources must not be mixed"). Ez 2026-10-07-én élőben
    # kiderült, miután a --token CLI opciót eltávolítottuk, de a token=
    # argumentumot a scriptben hagytuk.
    #
    # Ez az egyetlen őr, ami forrásszöveget néz — és pont azért, mert a
    # `token=` egy KIFEJEZÉS a provider hívásában, amit egy dict-ellenőrzés
    # nem érne el. A keresés ezért NEM a környezeti változó nevét, hanem a
    # KIFEJEZÉST keresi, amit a rossz kód használna: a provider konstrukcióját.
    src = Path(__file__).read_text(encoding="utf-8")
    provider_call = re.search(r"IQMProvider\([^)]*\)", src, re.S)
    assert provider_call is not None, (
        "az IQMProvider hívása eltűnt a scriptből — ezt az őr nem tudja "
        "értékelni, inkább bukjon el, mint hagyjon védelem nélkül"
    )
    call_src = provider_call.group(0)
    assert "token" not in call_src.lower(), (
        f"a providernek NEM szabad tokent átadni: a hitelesítés kizárólag "
        f"az IQM_TOKEN env-változóból jöhet, de a hívás így néz ki: {call_src}"
    )
    print("[OK] regressziós őr: a token kizárólag IQM_TOKEN env-változóból")

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

    # Wilson-CI regressziós őrök. Ezek nem a mérés döntései, hanem a
    # SZÁMSZÁMÍTÁS őrei: a CInak ténylegesen tartalmaznia kell a becslést,
    # és szélső esetben sem roppanhat össze nullára — különben egy 0/1024
    # arányt "biztosnak" jelentene.
    assert wilson_ci95(0, 1024)[1] > 0.0, "a Wilson-felső korlát 0/1024-nél nem lehet 0"
    ci_zero = wilson_ci95(1012, 1024)
    assert ci_zero[0] < 1012 / 1024 * 100.0 < ci_zero[1], ci_zero
    ci_half = wilson_ci95(512, 1024)
    assert abs(ci_half[0] - 46.0) < 1.5 and abs(ci_half[1] - 54.0) < 1.5, ci_half
    ci_all = wilson_ci95(1024, 1024)
    assert ci_all[0] < 100.0 and ci_all[1] == 100.0, ci_all
    print(f"[OK] Wilson CI: 0/1024 -> {wilson_ci95(0, 1024)}, "
          f"512/1024 -> {ci_half}, 1024/1024 -> {ci_all}")

    # A CI-overlap alapú verdict valóban különbözteti meg a két esetet.
    v_same = verdict(97.0, 97.6, [96.4, 97.6], [97.0, 98.2])
    v_diff = verdict(97.0, 99.5, [96.4, 97.6], [99.0, 100.0])
    assert "átfedik egymást" in v_same, v_same
    assert "NEM fedik egymást" in v_diff, v_diff
    print("[OK] verdict: az intervallum-overlap megkülönbözteti a "
          "zajt a mérhető különbségtől")

    print("\n[OK] OFFLINE VALIDÁCIÓ MINDEN TESZTEN ÁTMENT")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Tesseract Anchor circuit-level kontrollsor IQM Resonance-on")
    p.add_argument("--url", default=os.getenv("IQM_URL", "https://resonance.iqm.tech"))
    p.add_argument("--backend", default="garnet",
                   choices=["garnet", "emerald", "sirius"])
    p.add_argument("--shots", type=int, default=1024)
    p.add_argument("--freq", type=float, default=4.11,
                   help="Fázisszámítás paramétere (GHz) — NEM fizikai drive")
    p.add_argument("--duration", type=int, default=37)
    p.add_argument("--planes", type=int, default=4)
    p.add_argument("--seed", type=int, default=None,
                   help="a mérés kért seedje; audit-metaadatként megmarad "
                        "a rekordban, de az IQM NEM alkalmazza (seed_applied=false)")
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
        return validate_offline(args.shots, args.freq, args.duration,
                                args.planes, args.seed)

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

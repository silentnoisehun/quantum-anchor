# Quantum Anchor

**Kozvetlen impulzusszintű kvantumvezérlés az IBM Heron architektúrán — a
koherens állapot-horgonyzás fizikai és informatikai modellje.**

> ## ⚠️ KEZDŐLAP — olvasd el, mielőtt bármit idéznél ebből a projektből
>
> Ez a repository **jelen állapotban nem publikálható**. A modell
> dokumentálva van, és a benne lévő állítások bizonyítéki fokozattal
> rendelkeznek, de a mellékelt white paper (HOPE-WP-2026) **öt
> blokkoló hibát** tartalmaz.
>
> - **A kód nem futtatható.** A `qiskit.pulse` modul megszűnt
>   (Qiskit 2.5.2-ben nincs jelen).
> - **A `meas_level=0` paraméterek nem léteznek** a jelenlegi primitívekben.
> - **Az `amp=0.08` egy 94%-os π-fordulás**, tehát *nem* az a
>   „nem-destruktív perturbáció", amit a paper állít.
> - **A γ=0 nem érhető el hardveren** (véges T1/T2).
> - **A „nem szor" tézis ellentmond a mérési módszernek.**
>
> Minden részlet, bizonyítékkal: **[docs/VALIDATION.md](docs/VALIDATION.md)**
>
> Ez a projekt **nem állít hardveres bizonyítékot**. Semmi itt nem futott
> valódi QPU-n.

---

## Mi ez

A white paper egy hipotézist fogalmaz meg: egy gyenge, nem-destruktív
impulzus „horgonyként" működhet — a rendszer egy módusa túléli az
impulzust, és ez a túlélés jelentőséggel bír.

A projekt **nem** ezt bizonyítja. A projekt dokumentálja, hogy mit mond a
hipotézis, hol ellenőrizetlen, és miért nem publikálható még.

## Tartalom

| Fájl | Mi benne |
|---|---|
| [`docs/VALIDATION.md`](docs/VALIDATION.md) | **A proof ledger.** Minden állítás jelöléssel, az öt blokkoló hibával, és a §7-ben a lefuttatott mérésekkel. |
| `src/anchor_model.py` | A horgonyegyenlet klasszikus kiértékelése. Csak stdlib. |
| `src/anchor_measure.py` | A mérési réteg: amplitúdó-söprés, roundtrip, telítés. Szimuláció. |
| `src/check_no_dependencies.py` | Statikus függőségi audit. |
| `config/.env.template` | A környezeti változók helyőrzői. Csak helyőrző, nem titok. |

## Futtatás

### A mérési réteg

```powershell
python -m src.anchor_measure --shots 4000                      # ideális
python -m src.anchor_measure --backend FakeKyiv --shots 4000  # zajmodell
```

Ez **szimuláció**. Nem használ QPU-t, nem állít hardveres bizonyítékot.
A white paper fizikai állításait teszteli:

| Teszt | Eredmény |
|---|---|
| A4 — a populáció követi a Rabi-képletet | **HOLDS**, max hiba 0,95% |
| A2 — a forgatás visszafordítható | **HOLDS**, maradék 0,00% / 0,22% zaj |
| A3 — telítés a π környezetében | megvan, jól látható |

**Amit ezek NEM bizonyítanak:** mindhárom eredmény magyarázható egy **üres
egyqubites Bloch-forgatással**, amelyben nincs λ, nincs γ, nincs mező.
A mért viselkedés **nem különböztethető meg a triviális Rabi-forgatástól** —
tehát a mérések nem támasztják alá az „horgony" állítást. Részletek:
[docs/VALIDATION.md §7](docs/VALIDATION.md).

### A klasszikus modell

```powershell
python -m src.anchor_model
```

Szintén **klasszikus számítás**. Az `anchor_model.py` a horgonyegyenletet
értékeli ki, és **nulla hardveres állítást** tesz.

### A függőségi audit

```powershell
python -m src.check_no_dependencies
```

Statikusan (AST-alapú) ellenőrzi, hogy a projekt csak standard library-t
importál. Ez teszi ellenőrizhetővé a „nincs harmadik fél függőség"
állítást.

## Követelmények

| Rész | Követelmény |
|---|---|
| `anchor_model.py` | **nincs** — csak a standard library |
| `check_no_dependencies.py` | **nincs** — csak a standard library |
| `anchor_measure.py` | `qiskit`, `qiskit-aer` (szimuláció) |

A `qiskit` a mérési réteghez kell, **nem** a modellhez.

## Bizonyítéki szintek

Ez a repository követi az SCS projekt rendjét:

| Jelölés | Jelentés |
|---|---|
| ✅ | Klasszikus proof — offline számítás igazolja. **Nem** hardveres proof. |
| 🔬 | Hardveres proof — valódi QPU-n mért. Ebben a projektben: **nincs ilyen.** |
| ⚠️ | Ellenőrizetlen vagy mérésfüggő állítás. |
| ℹ️ | Konvenció — a projekt definíciója, nem természeti törvény. |

## Licenc

MIT — lásd [`LICENSE`](LICENSE).

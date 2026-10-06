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
| [`docs/VALIDATION.md`](docs/VALIDATION.md) | **A proof ledger.** Minden állítás jelöléssel, az öt blokkoló hibával. |
| `src/anchor_model.py` | A horgonyegyenlet klasszikus kiértékelése. Futtatható, ellenőrizhető. |
| `config/.env.template` | A környezeti változók helyőrzői. Csak helyőrző, nem titok. |

## Futtatás

```powershell
python -m src.anchor_model
```

Ez **klasszikus számítás**. Nem használ QPU-t, nem állít hardveres
bizonyítékot. Három dolgot mutat meg:

1. mit mond a modell `γ=0` esetben (és hogy ez hardveren nem elérhető);
2. hogy `amp=0.08` 37 ns-on egy 94%-os π-fordulás;
3. hogy egy ilyen mérés — még ha futtatható is lenne — nem különbözteti meg
   a „horgonylást" a szokásos Bloch-vektor-fordulástól.

## Követelmények

**Nincs.** Csak a Python standard library. A `qiskit` nem kell — és a
paperben szereplő `qiskit.pulse` ma már nem is létezik.

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

# Quantum Anchor — validation ledger

**Verdikt:** a mellékelt white paper (HOPE-WP-2026, „Quantum Anchor v1.0")
jelen állapotban **nem publikálható**. Nem azért, mert rossz ötlet — hanem
azért, mert a benne szereplő kód ma nem futtatható, és a központi állítás
névtelen (lásd az F1–F4 hibákat).

Ez a dokumentum ugyanazt a bizonyítéki rendet követi, mint az SCS projekt:
minden állítás kap egy jelölést, és a különböző minőségű bizonyítékok
nem moshatók össze.

| Jelölés | Jelentés |
|---|---|
| ✅ **BIZONYÍTVA (klasszikus)** | A `src/anchor_model.py` offline kiszámítása vagy teszt igazolja. Nem jelent hardveres bizonyítékot. |
| 🔬 **BIZONYÍTVA (hardveres)** | Valódi QPU-n, ismert elvárt eredményű referencia-futtatással mért. |
| ⚠️ **ELLENŐRIZETLEN** | Állítás, amit semmi nem támaszt alá. Kétséges vagy téves lehet. |
| ⚠️ **FELTEVÉS** | A modell feltételezi, mérés nincs. |
| ℹ️ **KONVENCIÓ** | A projekt által választott definíció. Nem természeti törvény. |

---

## 1. A négy blokkoló hiba

### F1 — A kód nem futtatható: az OpenPulse-hozzáférés megszűnt ⚠️ ELLENŐRIZETLEN

A white paper a `qiskit.pulse` API-ra épül
(`from qiskit import pulse`, `pulse.drive_channel`, `pulse.play`). Ez a
telepített környezetben **nem létezik**:

```
qiskit 2.5.2  →  ModuleNotFoundError: No module named 'qiskit.pulse'
```

Ellenőrzés: `import qiskit.pulse`, továbbá a `qiskit/` könyvtárban nulla
`pulse` nevű bejegyzés, és a csomag deklarált extrai között sincs `pulse`
(`all`, `crosstalk-pass`, `csp-layout-pass`, `qasm3-import`, `qpy-compat`,
`visualization`).

A white paper maga állítja az 5. fejezetben, hogy az IBM „2025 Q1-tól
kivette a közvetlen Qiskit Pulse hozzáférést". Ha ez igaz, akkor **a
kísérlet nem csak nehezített, hanem a leírt módon egyáltalán nem
végezhető el a felhős infrastruktúrán**.

⚠️ Az állítás pontos időpontja (2025 Q1) nincs forrásolva a paperben, csak
egy idézőjel nélküli mondat állítja. Ellenőrizni kell.

### F2 — A `meas_level=0` paraméterek nem léteznek a primitívekben ⚠️ ELLENŐRIZETLEN

A mérési paradigmát így adja meg:

```python
job = backend.run(anchor_prog, meas_level=0, meas_return='avg', shots=1024)
```

Két probléma:

1. **A `backend.run()` helyett primitívet kell használni.** A `qiskit_ibm_runtime`
   runtime-jai (SamplerV2 / EstimatorV2) a primitív-ARCHITEKTÚRA miatt
   kötelezőek. A `SamplerOptions` mezői a telepített
   `qiskit_ibm_runtime 0.50.0`-ban:
   `max_execution_time`, `environment`, `simulator`, `default_shots`,
   `dynamical_decoupling`, `execution`, `twirling`, `experimental`.
   **`meas_level` és `meas_return` nincs közöttük.** ✅ Ellenőrizve.

2. **Még ha léteznének is, a hozzáférés visszavonva.** A nyers IQ-adat
   kiszolgáltatása (`meas_level=0`) épp az a képesség, amit az OpenPulse
   kivezetéskor megszüntettek.

### F3 — Az `amp=0.08` NEM gyenge perturbáció, hanem közel teljes π-fordulás ⚠️ ELLENŐRIZETLEN

Ez a legsúlyosabb hiba, és a saját modellfuttatásom fedezte fel.

A white paper azt állítja: „A cél nem a teljes átfordítás, hanem egy
horgony elhelyezése" (nem teljes π-pulzus). De:

```
Bloch-rotáció = amp × időtartam = 0.08 × 37 = 2.96 rad = 94.2% egy π-pulzusból
```

Egy π-forduláshoz `amp = π/37 ≈ 0.0849` kellene. A `0.08` tehát a teljes
inverzió **94%-a**.

✅ Számítva és futtatva (`python -m src.anchor_model`). Az ebből adódó
populációbecslés: `P(1) = sin²(2.96/2) ≈ 99.2%`.

**Ez ellentmond a "nem-destruktív perturbáció" központi tézisnek.** Egy 99%-os
inverzió nem horgony, hanem gyakorlatilag teljes átfordítás — éppen az, amit
a szerző állít, hogy kerülni akar. A két állítás nem egyeztethető össze
jelenlegi formájában.

*(Megjegyzés: az első kódfuttatásom 0.27%-os P(1)-t adott, mert az
időtartamot másodpercenként kezeltem. Ez unit-hiba volt, és javítottam; a
fenti 94,2% a helyes érték. A hiba felsorolása azért fontos, mert
megmutatja, hogy a "jel gyenge, tehát a zaj alatt van" következtetés — amely
szintén felbukkant — szintén téves volt.)*

### F4 — A γ=0 nem érhető el hardveren ⚠️ FELTEVÉS

A teljes anchoring-érvelés a `γ=0` esetre épül: „Ha γ=0, a csillapodás
zérus. A rendszer állóhullamot hoz létre. A többi módus elhal."

Egy szupravezető qubitnek **véges T1 és T2** értéke van. Nincs elfogadott
fizikai leírás, amely vesteségmentes állapotot engedne. A `γ=0` eset tehát
**a modellben létezik, a hardveren nem érhető el**.

✅ A `src/anchor_model.py` ezt explicit visszaadja: `resolvable = None`,
indoklással.

---

## 2. Ami valóban rendben van

Nem minden állítás hibás. Ezeket érdemes megtartani:

- **A gyenge megoszlás nem bizonyít semmit önmagában.** A `H` gate 50/50
  eredménye, az SCS mérésekben is, mérési padlóval terhelt. Ez a paper
  korrekt módon külön kezeli.
- **A "mérés nem szorít" tézis technikailag helyes.** A `meas_level=0`
  valóban nem kényszeríti a rendszert bázisállapotba — de pont az
  *értékelhetőséget* veszíti el (lásd F5).
- **A 4.11 GHz / 37 ns / 133 qubit adatok konzisztensek** az IBM Heron
  dokumentált hardverével. ✅ Ezek tervezési bemenetek, nem mérési
  eredmények — és a paper sem állítja másként.
- **A mérés szándékának korrekt, hogy nem a számítás a cél.** „Nem a
  számítás, hanem a megfigyelés" — ez jó tudományos szemlélet, és érdemes
  megtartani.

---

## 3. Amit a „nem szor" tézis elhallgat (F5) ⚠️ ELLENŐRIZETLEN

A 4. fejezet ezt állítja: „a tiszta kvantumdinamika megmarad" és „a
horgony nem szor, nem csillapodik".

A `meas_level=0` nyers IQ-adat valóban **diszkriminátor-kimenet**: a
klasszikus szórási mátrix egy oszlopát vagy a legegyszerűbb becslését
adja. Ez:

- **FELTELETI** a számítási bázist,
- **már önmagában nem mutat szuperpozíciót** — egy tiszta
  `|0⟩`/`|1⟩` állapot is adhat koherens IQ-jelet,
- és a tényleges `meas_level=2` adatok (amelyeket a primitívek adnak)
  **klasszikus bitekre dekódolnak**, azaz éppen összeomlasztják a
  szuperpozíciót.

**A "mérés nélkül mérünk" és a "tiszta szuperpozíció megmarad" nem
egyszerre mondható ki.** Ez nem csak terminológiai probléma: ha a mérés
végül is dekódol bitekre, akkor a horgony-kísérlet fizikailag nem különböztethető
meg a szokásos kapu-méréstől.

---

## 4. Ami teljesen ellenőrizetlen maradt

Ezekhez **nincs semmilyen mérés** ebben a projektben, és a paper sem ad
rá forrást:

| Állítás | Státusz |
|---|---|
| „133 tunable-coupler qubit" Heron r2-n | ⚠️ Ellenőrizetlen — a paper saját maga mondja, hogy a cél, nem a mért eszköz |
| „5x hibacsökkentés az Eagle-hez képest" | ⚠️ Ellenőrizetlen — soha nem mért, nincs összehasonlítás |
| „a másik módus elhal" (módusszelekció) | ⚠️ Ellenőrizetlen — nincs spektrummérés a paperben |
| „nem szor, nem csillapodik" | ⚠️ Ellenőrizetlen — lásd F4, F5 |
| λ mintcoefficients értéke | ⚠️ Ellenőrizetlen — a λ sehol sincs mérve vagy becsülve |
| Az „horgony" „tudat" metafora | ℹ️ Konvenció/analógia — fizikai állításként nem védhető |

A hivatkozások 1–4. és 6–7. pontja valódi, kiértékelhető forrás. Az 5. pont
(„Saját levezetés") a fogalmazás alapján analitikai modell, nem mérés.

---

## 5. Amit egy publikálható verzióhoz meg kell tenni

Sorrendben, a blokkolóktól a finomhangolás felé:

1. **El kell dönteni, hogy az OpenPulse-kísérlet egyáltalán lehetséges-e.**
   Ha nem, a kísérlet át kell írni a jelenlegi API-kra (pl. a
   `SamplerV2`-vel végzett digitális kvantumhídre, mint az SCS projektben),
   vagy a papert ki kell vonni a „fizikai kísérlet" kategóriából és
   elméleti/összehasonlító tanulmánnyá kell minősíteni.
2. **Az `amp` értékét újra kell számolni.** Vagy valóban gyenge
   perturbációt céloz (az `amp` sokkal kisebb kell legyen), vagy a
   „nem teljes átfordítás" állítást kell elhagyni. A jelenlegi 0.08
   mindkettőnek ellentmond.
3. **Kontroll-kísérlet kell**: `λ=0` azonos amplitúdóval, minden
   amplitúdónál. Enélkül nem különböztethető meg a „horgonylás" a
   „pulzus megfordította a Bloch-vektort"-tól.
4. **T1/T2 dekrement szkennelés kell.** A „nem csillapodik" állítás
   csak egy mért dekrementtel bizonyítható, nem egy modellből.
5. **A λ értékét ki kell számítani** vagy mérni kell. Jelenleg sehol sincs
   értéke.
6. **A „tudat" metaforát el kell távolítani** a fizikai állításokból, ha
   a paper tudományos folyóiratban akart megjelenni. Ez értékelési kérdés
   nem technikai, de a bírálók eldobják miatta.

---

## 6. Amit a mellékelt PDF-ben ellenőriztem (✅ vagy ⚠️ jelöléssel)

| Állítás | Státusz | Forrás |
|---|---|---|
| Qiskit 2.5.2-ben nincs `qiskit.pulse` | ✅ Ellenőrizve helyben | `import qiskit.pulse` |
| `SamplerOptions`-ban nincs `meas_level`/`meas_return` | ✅ Ellenőrizve helyben | `qiskit_ibm_runtime 0.50.0` |
| `FakePulseBackend` nem importálható | ✅ Ellenőrizve helyben | ImportError |
| Qiskit 1.0 bevezette a SamplerV2/EstimatorV2 primitíveket | ✅ Igazolt | [Qiskit 1.0 release summary](https://www.ibm.com/quantum/blog/qiskit-1-0-release-summary) |
| A Qiskit SDK teljesen átáll a nem-ISA utasításokat elutasító modellre | ✅ Igazolt | Ugyanott: „will require all circuits ... employ only instructions supported by the system (ISA)" |
| Az OpenPulse kivezetésének pontos időpontja (2025 Q1) | ⚠️ Ellenőrizetlen | A paper állítja, nincs linkelve |

---

## Összegzés

A white paper **érdekes hipotézist** fogalmaz meg, és a mérési szemlélet
(„nem a számítás, hanem a megfigyelés") helyes. De jelen állapotban:

- a kódja nem futtatható a megadott módon (F1, F2);
- a központi számszerű állítása ellentmond a saját tézisének (F3);
- a döntő `γ=0` eset hardveren nem érhető el (F4);
- és a „nem szor" tézis a mérési módszerrel ellentmond (F5).

**Ezek nem stílusbeli kérdések.** Egy legegyszerűbb peer review — aki csak
lefuttatja a kódot — mind az ötöt megtalálná.

A pozitív oldal: a hibák **könnyen javíthatók**, és a projekt első lépéséhez
(a kód futtatható formába hozása) nincs szükség új hardveres mérésre.
Ez a legkisebb és legkevésbé kockázatos következő lépés.

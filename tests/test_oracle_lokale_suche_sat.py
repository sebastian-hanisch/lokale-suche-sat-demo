"""Orakel-Tests: unabhängige Rechenwege für probSAT und CDCL (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK §5).

* Aufzählung aller 2^n Belegungen (n ≤ 12): Modelle und Erfüllbarkeit; sie prüft die Antworten von CDCL und die Modelle von probSAT.
* CDCL gegen OR-Tools CP-SAT (Erfüllbarkeit, `importorskip`): 30 Zufallsformeln im Repo (im Scratch-Lauf des Baus 200).
* probSAT gegen eine naive Neuberechnung: dieselbe Rechenregel (Ziehungen, Liste der verletzten Klauseln), aber Zähler, Break und Lesezugriffe
  werden in jedem Schritt aus der Belegung neu gezählt statt inkrementell geführt. Gleicher Lauf heißt gleiche Umdrehungen, Lesezugriffe, Modell.
* Gewichte gegen numpy, Auswahlverteilung gegen `numpy.random.default_rng(...).choice` (statistisch, Toleranz 1 %).
"""

import itertools

import numpy as np
import pytest

import lks_algorithm as A
import lks_instanzen as I
import lks_scenario as S
from lks_cdcl import solve
from lks_rng import SplitMix64


def _modelle(n, kl):
    """Aufzählung (eigener Code, nicht `A.alle_modelle`): Menge der Modelle als Tupel."""
    return [b for b in itertools.product((False, True), repeat=n) if all(any(b[abs(l) - 1] == (l > 0) for l in c) for c in kl)]


# --- Aufzählung als Orakel -----------------------------------------------------------------------------------------------------------------

def test_cdcl_antwort_gleicht_der_aufzaehlung_und_modelle_sind_eines_der_aufgezaehlten():
    unerf = erf = 0
    for seed in range(40):
        n = 8 + seed % 5
        inst = I.rand3(n, int(4.3 * n), 100 + seed)
        modelle = _modelle(n, inst.klauseln)
        erg = solve(n, inst.klauseln)
        assert erg.antwort == bool(modelle)
        if erg.antwort:
            erf += 1
            assert tuple(erg.modell[v] for v in range(1, n + 1)) in modelle
        else:
            unerf += 1
    assert erf > 5 and unerf > 5           # beide Fälle kommen vor


def test_probsat_modell_ist_aufgezaehltes_modell_und_unerfuellbares_wird_nie_geloest():
    gel = nicht_gel = unerf_ok = 0
    for seed in range(60):
        n = 8 + seed % 5
        inst = I.rand3(n, int(4.3 * n), 200 + seed)
        modelle = _modelle(n, inst.klauseln)
        lauf = A.probsat_lauf(n, inst.klauseln, 4000, seed)
        if lauf.modell is not None:
            gel += 1
            assert tuple(lauf.modell[v] for v in range(1, n + 1)) in modelle
        else:
            nicht_gel += 1
            unerf_ok += not modelle
    assert gel > 10 and unerf_ok > 5


def test_alle_modelle_der_app_gleichen_der_unabhaengigen_aufzaehlung():
    for kl, n in ((S.HAND_KLAUSELN, 5), (I.rand3(9, 38, 5).klauseln, 9)):
        assert [tuple(c == "1" for c in b) for b in A.alle_modelle(n, kl)] == _modelle(n, kl)


# --- CDCL gegen CP-SAT -------------------------------------------------------------------------------------------------------------------

def test_cdcl_gegen_cpsat_erfuellbarkeit():
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")

    def cpsat(n, kl):
        m = cp_model.CpModel()
        x = [None] + [m.NewBoolVar(f"x{i}") for i in range(1, n + 1)]
        for c in kl:
            m.AddBoolOr([x[l] if l > 0 else x[-l].Not() for l in c])
        s = cp_model.CpSolver()
        s.parameters.num_workers = 1
        s.parameters.max_time_in_seconds = 60
        r = s.Solve(m)
        assert r in (cp_model.OPTIMAL, cp_model.INFEASIBLE)
        return r == cp_model.OPTIMAL

    erf = unerf = 0
    for seed in range(30):
        n = 30 + (seed % 4) * 10
        inst = I.rand3(n, int(4.26 * n), 300 + seed)
        referenz = cpsat(n, inst.klauseln)
        erg = solve(n, inst.klauseln, conflict_budget=100000)
        assert erg.antwort == referenz
        erf += referenz
        unerf += not referenz
        lauf = A.probsat_lauf(n, inst.klauseln, 20000, seed)
        assert referenz or lauf.modell is None          # probSAT findet bei CP-SAT-unerfüllbaren Formeln nie ein Modell
    assert erf >= 5 and unerf >= 5


# --- probSAT gegen naive Neuberechnung -----------------------------------------------------------------------------------------------------

def _naiv(n, kl, max_flips, seed, cb, eps):
    """probSAT mit Neuberechnung in jedem Schritt: Wahrheitswerte, Zähler, Break und Lesezugriffe aus der Belegung, keine inkrementellen Zähler.
    Die Liste der verletzten Klauseln folgt derselben Regel wie die Demo (Anhängen in aufsteigender Klauselnummer, Entfernen durch Austausch mit dem letzten Element)."""
    rng = SplitMix64(seed)
    wert = {v: rng.coin() for v in range(1, n + 1)}

    def wahr(l):
        return wert[l] if l > 0 else not wert[-l]

    def zahl_wahr(c):
        return sum(1 for l in c if wahr(l))

    occ = lambda l: [i for i, c in enumerate(kl) if l in c]          # noqa: E731
    lesen = sum(len(c) for c in kl)
    liste = [i for i, c in enumerate(kl) if zahl_wahr(c) == 0]
    for flips in range(max_flips):
        if not liste:
            return flips, lesen, dict(wert)
        i = liste[rng.below(len(liste))]
        ws = []
        for l in kl[i]:
            v = abs(l)
            tl = v if wert[v] else -v
            lesen += len(occ(tl))
            b = sum(1 for j in occ(tl) if zahl_wahr(kl[j]) == 1)
            ws.append((eps + b) ** (-cb))
        r = rng.random() * sum(ws)
        k, summe = 0, ws[0]
        while r > summe and k < len(ws) - 1:
            k += 1
            summe += ws[k]
        v = abs(kl[i][k])
        tl = v if wert[v] else -v
        lesen += len(occ(tl)) + len(occ(-tl))
        wert[v] = not wert[v]
        for j in occ(tl):
            if zahl_wahr(kl[j]) == 0:
                liste.append(j)
        for j in occ(-tl):
            if j in liste:
                p = liste.index(j)
                letzte = liste.pop()
                if letzte != j:
                    liste[p] = letzte
    return max_flips, lesen, (dict(wert) if not liste else None)


@pytest.mark.parametrize("seed", range(25))
def test_probsat_gleicht_der_naiven_neuberechnung(seed):
    n = 12 + seed % 10
    inst = I.rand3(n, int(4.1 * n), 500 + seed)
    cb, eps = (2.3, 0.9) if seed % 2 else (2.06, 0.5)
    lauf = A.probsat_lauf(n, inst.klauseln, 400, seed, cb=cb, eps=eps)
    flips, lesen, modell = _naiv(n, inst.klauseln, 400, seed, cb, eps)
    assert (lauf.flips, lauf.lesezugriffe) == (flips, lesen)
    assert lauf.modell == modell


# --- Gewichte und Auswahl gegen numpy -----------------------------------------------------------------------------------------------------------

def test_gewichte_gegen_numpy():
    for cb, eps in ((2.3, 0.9), (2.06, 0.9), (3.0, 1.0)):
        b = np.arange(0, 20)
        assert np.allclose([A.gewicht(int(x), cb, eps) for x in b], (eps + b) ** -cb, rtol=1e-12)


def test_auswahlverteilung_gegen_numpy_choice():
    gewichte = [A.gewicht(b, 2.3, 0.9) for b in (0, 1, 2)]
    soll = np.array(gewichte) / sum(gewichte)
    g = SplitMix64(99)
    eigene = np.bincount([A.waehle_index(gewichte, g.random()) for _ in range(100000)], minlength=3) / 100000
    fremd = np.bincount(np.random.default_rng(1).choice(3, size=100000, p=soll), minlength=3) / 100000
    assert np.abs(eigene - fremd).max() < 0.01 and np.abs(eigene - soll).max() < 0.01

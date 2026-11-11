"""Randfälle: leere Formel, Einheitsklausel, Widerspruchspaar, Budget 0, n = 3, Startbelegung, Zähler am Rand."""

import pytest

import lks_algorithm as A
import lks_evaluation as E
import lks_instanzen as I
from lks_probsat import probsat


def test_leere_formel_ist_sofort_erfuellt():
    lauf = A.probsat_lauf(3, [], 10, 1, spur=True)
    assert lauf.modell is not None and lauf.flips == 0 and lauf.lesezugriffe == 0 and lauf.kleinste == 0
    assert lauf.zahlen == [0] and len(lauf.schritte) == 1 and lauf.schritte[0].klausel is None
    assert probsat(3, [], 10, 1).flips == 0


def test_einheitsklausel_wird_gedreht_und_geloest():
    lauf = A.probsat_lauf(3, [(2,)], 50, 4, start={1: False, 2: False, 3: False})
    assert lauf.modell is not None and lauf.modell[2] is True and lauf.flips == 1
    assert lauf.lesezugriffe == 1 + 0 + (0 + 1)           # Zähler füllen: 1; break von x2: Vorkommen von ¬x2 = 0; Umdrehen: Vorkommen von ¬x2 (0) und von x2 (1)
    lauf = A.probsat_lauf(3, [(-2,)], 50, 4, start={1: False, 2: False, 3: False})
    assert lauf.flips == 0 and lauf.modell is not None


def test_widerspruchspaar_wird_nie_geloest_und_kleinste_zahl_ist_eins():
    lauf = A.probsat_lauf(2, [(1,), (-1,)], 500, 3)
    assert lauf.modell is None and lauf.kleinste == 1 and lauf.verletzt_am_ende == 1
    for seed in range(5):
        assert probsat(2, [(1,), (-1,)], 200, seed).modell is None


def test_budget_null_ohne_modell_und_mit_modell():
    inst = I.rand3(10, 60, 3)
    lauf = A.probsat_lauf(inst.n, inst.klauseln, 0, 1, spur=True)
    assert lauf.flips == 0 and len(lauf.schritte) == 1 and lauf.zahlen == [lauf.verletzt_am_ende or 0]
    erfuellt = A.probsat_lauf(3, [(1, 2, 3)], 0, 0, start={1: True, 2: False, 3: False})
    assert erfuellt.modell is not None and erfuellt.flips == 0


def test_drei_variablen_alle_modelle_gefunden_wird_eines():
    kl = [(1, 2, 3), (-1, 2, 3), (1, -2, 3), (1, 2, -3)]           # verboten sind 000, 100, 010, 001; Modelle: 011, 101, 110, 111
    assert len(A.alle_modelle(3, kl)) == 4
    for seed in range(10):
        lauf = A.probsat_lauf(3, kl, 200, seed)
        assert lauf.modell is not None


def test_klauseln_der_erzeuger_haben_nie_zwei_gleiche_variablen():
    for seed in range(60):
        inst = I.rand3(7, 30, seed)
        assert all(len({abs(l) for l in c}) == 3 for c in inst.klauseln)


def test_gewichte_bei_grossem_break_sind_beschraenkt():
    """Break-Werte ab 63 bekommen das Gewicht von 63 (Tabelle der Kern-Kopie); kleine break-Werte haben ihr eigenes Gewicht."""
    assert A.ANZAHL_GEWICHTE == 64
    w = [A.gewicht(b, 2.3, 0.9) for b in (62, 63)]
    assert w[0] > w[1] > 0


def test_formatierungen_am_rand():
    assert E.zahl(0) == "0" and E.zahl(1000) == "1.000" and E.zahl(1234567) == "1.234.567" and E.zahl(2.5) == "2,5"
    assert E.dez(4.26) == "4,26" and E.dez(4.0) == "4,0" and E.dez(0.9) == "0,9"
    assert E.faktor_text(54.4) == "54-mal" and E.faktor_text(3.44) == "3,4-mal"
    assert E.laeufe_text(1) == "1 Lauf" and E.laeufe_text(5) == "5 Läufe" and E.laeufe_text(5, True) == "5 Läufen" and E.laeufe_text(1, True) == "1 Lauf"


def test_kennzahlen_ohne_gelaeste_und_median_basis():
    zeilen = [{"seed": 1, "cdcl": {"antwort": None, "konflikte": 20, "lesezugriffe": 99}, "probsat": [{"seed": 1, "geloest": False, "flips": 5, "lesezugriffe": 50, "verletzt_am_ende": 2}]}]
    z = E.kennzahlen(zeilen)
    assert z.c_unb == 1 and z.p_gel == 0 and z.median_cdcl is None and z.median_probsat is None and z.faktor is None and z.untere_schranke
    assert E.verhaeltnis_text(z) == "–"
    with pytest.raises(KeyError):
        E.kennzahlen(zeilen, "gibt_es_nicht")

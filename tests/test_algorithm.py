"""probSAT mit Spur (`lks_algorithm`): Handbeispiel von Hand durchgerechnet, Eigenschaften je Umdrehung, Gleichlauf mit der Kern-Kopie.

Handrechnung (Formel C1 = (x1 ∨ x2 ∨ x3), C2 = (¬x1 ∨ x2 ∨ ¬x4), C3 = (¬x2 ∨ x3 ∨ x5), C4 = (x1 ∨ ¬x3 ∨ x4), C5 = (¬x1 ∨ ¬x3 ∨ ¬x5),
C6 = (x2 ∨ ¬x4 ∨ x5), C7 = (¬x2 ∨ ¬x4 ∨ ¬x5)), cb = 2,3, ε = 0,9, Zufalls-Seed 20:
  Start: fünf Münzwürfe 0 0 0 0 0, Belegung 00000, nur C1 verletzt. Zähler füllen: 3 · 7 = 21 Lesezugriffe.
  Umdrehung 1: break (x1, x2, x3) = (0, 1, 1): x1 steht mit ¬x1 in C2 (¬x4 wahr) und C5 (drei wahre), x2 mit ¬x2 in C3 (einziges wahres Literal: break) und C7,
    x3 mit ¬x3 in C4 (einziges wahres Literal) und C5. Gewichte 0,9^(−2,3) = 1,2742 und 1,9^(−2,3) = 0,2285 (zweimal), Summe 1,7312. u = 0,8272, u · Summe = 1,4320;
    kumuliert 1,2742 < 1,4320 ≤ 1,5027: das zweite Literal, x2 wird umgedreht. Lesezugriffe: 21 + (2 + 2 + 2) + (|¬x2| = 2 + |x2| = 3) = 32.
  Umdrehung 2: Belegung 01000, nur C3 verletzt, break (¬x2, x3, x5) = (1, 1, 0), Lesezugriffe 12 (3 + 2 + 2, dazu |x2| + |¬x2| = 5), Stand 44; x2 wird zurückgedreht.
  Umdrehung 3: wieder 00000, C1, u · Summe = 0,2148 ≤ 1,2742: erstes Literal, x1 wird umgedreht; Lesezugriffe 6 + (|¬x1| = 2 + |x1| = 2) = 10, Stand 54.
  Belegung 10000 erfüllt alles.
"""

import itertools

import numpy as np
import pytest

import lks_algorithm as A
import lks_instanzen as I
import lks_scenario as S
from lks_probsat import probsat
from lks_rng import SplitMix64

W_NIEDRIG, W_HOCH = 1.2742, 0.2285         # 0,9^(−2,3) und 1,9^(−2,3), auf vier Stellen


# --- Handbeispiel ------------------------------------------------------------------------------------------------------------------------

def test_handbeispiel_neun_modelle_von_32():
    assert A.alle_modelle(5, S.HAND_KLAUSELN) == ["00111", "01001", "01110", "10000", "10001", "10100", "11001", "11100", "11110"]


def test_handbeispiel_zufallsstrom_seed_20():
    g = SplitMix64(S.HAND_SEED)
    assert [g.next() >> 63 for _ in range(5)] == [0, 0, 0, 0, 0]          # fünf Münzwürfe: Belegung 00000
    assert g.next() == 3175587741160004594                                   # Klauselwahl des ersten Schritts (Liste mit einem Element: Platz 0)
    assert round((g.next() >> 11) / 2 ** 53, 6) == 0.827190                   # u des ersten Schritts


def test_handbeispiel_seed_20_schritt_fuer_schritt():
    lauf = A.probsat_lauf(5, S.HAND_KLAUSELN, 50, S.HAND_SEED, spur=True)
    assert lauf.flips == 3 and lauf.lesezugriffe == 54 and lauf.verletzt_am_ende == 0
    assert lauf.modell == {1: True, 2: False, 3: False, 4: False, 5: False}
    assert [s.belegung for s in lauf.schritte] == ["00000", "01000", "00000", "10000"]
    assert [s.verletzt for s in lauf.schritte] == [[1], [3], [1], []]
    assert [s.klausel for s in lauf.schritte] == [1, 3, 1, None]
    assert [s.brk for s in lauf.schritte[:3]] == [[0, 1, 1], [1, 1, 0], [0, 1, 1]]
    assert [s.variable for s in lauf.schritte[:3]] == [2, 2, 1]
    assert [s.gewaehlt for s in lauf.schritte[:3]] == [1, 0, 0]
    assert [s.lesezugriffe for s in lauf.schritte] == [32, 44, 54, 54]
    assert lauf.zahlen == [1, 1, 1, 0]
    s0, s1, s2 = lauf.schritte[:3]
    assert s0.gewichte == pytest.approx([W_NIEDRIG, W_HOCH, W_HOCH], abs=5e-5) and s0.summe == pytest.approx(1.7312, abs=5e-5)
    assert s0.u == pytest.approx(0.827190, abs=5e-7) and s0.u_summe == pytest.approx(1.4320, abs=5e-5)
    assert W_NIEDRIG < s0.u_summe <= W_NIEDRIG + W_HOCH            # das zweite Literal
    assert s1.gewichte == pytest.approx([W_HOCH, W_HOCH, W_NIEDRIG], abs=5e-5) and s1.u_summe == pytest.approx(0.1385, abs=5e-5)
    assert s2.gewichte == pytest.approx([W_NIEDRIG, W_HOCH, W_HOCH], abs=5e-5) and s2.u_summe == pytest.approx(0.2148, abs=5e-5)
    assert lauf.verlauf == [(0, 1), (3, 0)]


def test_handbeispiel_gewichte_von_hand():
    assert A.gewicht(0, 2.3, 0.9) == pytest.approx(0.9 ** -2.3) == pytest.approx(1.27421, abs=5e-6)
    assert A.gewicht(1, 2.3, 0.9) == pytest.approx(1.9 ** -2.3) == pytest.approx(0.22849, abs=5e-6)


def test_handbeispiel_lesezugriffe_von_hand_je_schritt():
    """Zählweise aus den Vorkommen: Start 3·m, je Umdrehung die Vorkommen der wahren Literale der drei Variablen plus beider Literale der gewählten."""
    kl = S.HAND_KLAUSELN
    occ = {l: sum(1 for c in kl if l in c) for v in range(1, 6) for l in (v, -v)}
    assert occ[2] == 3 and occ[-2] == 2 and occ[1] == 2 and occ[-1] == 2
    assert 3 * len(kl) + (occ[-1] + occ[-2] + occ[-3]) + (occ[-2] + occ[2]) == 32
    assert 32 + (occ[2] + occ[-3] + occ[-5]) + (occ[2] + occ[-2]) == 44
    assert 44 + (occ[-1] + occ[-2] + occ[-3]) + (occ[-1] + occ[1]) == 54


# --- Eigenschaften je Umdrehung (unabhängige Neuberechnung) -------------------------------------------------------------------------------

def _wahr(c, b):
    return sum(1 for l in c if (b[abs(l) - 1] == "1") == (l > 0))


def _neu_break(kl, b, v):
    """Break der Variablen v unter der Belegung b: Klauseln, in denen das wahre Literal von v das einzige wahre Literal ist (Neuzählung)."""
    tl = v if b[v - 1] == "1" else -v
    return sum(1 for c in kl if tl in c and _wahr(c, b) == 1)


@pytest.mark.parametrize("seed", range(6))
def test_zaehler_verletzte_und_break_stimmen_nach_jeder_umdrehung_mit_neuberechnung(seed):
    inst = I.rand3(25, 107, 40 + seed)
    lauf = A.probsat_lauf(inst.n, inst.klauseln, 300, seed, spur=True)
    for vorher, nachher in zip(lauf.schritte, lauf.schritte[1:]):
        assert sorted(vorher.verletzt) == [i + 1 for i, c in enumerate(inst.klauseln) if _wahr(c, vorher.belegung) == 0]
        c = inst.klauseln[vorher.klausel - 1]
        assert vorher.klausel in vorher.verletzt and tuple(vorher.literale) == tuple(c)
        assert vorher.brk == [_neu_break(inst.klauseln, vorher.belegung, abs(l)) for l in c]
        assert vorher.gewichte == [(0.9 + b) ** -2.3 for b in vorher.brk]
        diff = [i + 1 for i in range(inst.n) if vorher.belegung[i] != nachher.belegung[i]]
        assert diff == [vorher.variable] and vorher.variable in {abs(l) for l in c}
        assert vorher.u_summe == pytest.approx(vorher.u * sum(vorher.gewichte))
    letzter = lauf.schritte[-1]
    assert sorted(letzter.verletzt) == [i + 1 for i, c in enumerate(inst.klauseln) if _wahr(c, letzter.belegung) == 0]
    assert lauf.zahlen == [len(s.verletzt) for s in lauf.schritte]
    assert lauf.kleinste == min(lauf.zahlen)


def test_lesezugriffe_wachsen_je_umdrehung_um_die_vorkommen():
    inst = I.rand3(20, 85, 3)
    lauf = A.probsat_lauf(inst.n, inst.klauseln, 40, 5, spur=True)
    occ = {l: sum(1 for c in inst.klauseln if l in c) for v in range(1, 21) for l in (v, -v)}
    stand = 3 * len(inst.klauseln)
    for s in lauf.schritte[:-1]:
        def wahr_lit(v):
            return v if s.belegung[v - 1] == "1" else -v
        stand += sum(occ[wahr_lit(abs(l))] for l in s.literale) + occ[wahr_lit(s.variable)] + occ[-wahr_lit(s.variable)]
        assert s.lesezugriffe == stand


def test_gleichlauf_mit_der_kern_kopie():
    for seed in range(40):
        n = 30 + seed % 20
        inst = I.rand3(n, int(4.1 * n), seed)
        cb = 2.3 if seed % 2 else 2.06
        a = A.probsat_lauf(n, inst.klauseln, 2500, seed, cb=cb)
        b = probsat(n, inst.klauseln, 2500, seed, cb=cb)
        assert (a.flips, a.lesezugriffe, a.modell, a.verletzt_am_ende) == (b.flips, b.lesezugriffe, b.modell, b.verletzt_am_ende)


def test_determinismus_und_spur_aendert_nichts():
    inst = I.rand3(40, 170, 9)
    a = A.probsat_lauf(inst.n, inst.klauseln, 4000, 11)
    b = A.probsat_lauf(inst.n, inst.klauseln, 4000, 11, spur=True)
    assert (a.flips, a.lesezugriffe, a.modell, a.kleinste, a.verlauf) == (b.flips, b.lesezugriffe, b.modell, b.kleinste, b.verlauf)
    c = A.probsat_lauf(inst.n, inst.klauseln, 4000, 12)
    assert (a.flips, a.lesezugriffe) != (c.flips, c.lesezugriffe)           # anderer Zufalls-Seed, anderer Lauf


# --- Gewichte und Auswahl -----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("cb,eps", [(2.3, 0.9), (2.06, 0.9), (3.5, 0.5), (1.5, 2.0)])
def test_gewichte_fallen_streng_mit_break_und_gleichen_numpy(cb, eps):
    w = [A.gewicht(b, cb, eps) for b in range(12)]
    assert all(x > y > 0 for x, y in zip(w, w[1:]))
    assert w == pytest.approx(list((eps + np.arange(12)) ** -cb))


@pytest.mark.parametrize("gewichte", [[W_NIEDRIG, W_HOCH, W_HOCH], [W_HOCH, W_HOCH, W_NIEDRIG], [1.0, 1.0, 1.0], [0.0625, 0.5, 4.0]])
def test_auswahlhaeufigkeit_gleicht_der_sollverteilung(gewichte):
    soll = np.array(gewichte) / sum(gewichte)
    g = SplitMix64(1)
    zaehler = [0, 0, 0]
    for _ in range(100000):
        zaehler[A.waehle_index(gewichte, g.random())] += 1
    assert np.abs(np.array(zaehler) / 100000 - soll).max() < 0.01
    numpy_haeufig = np.bincount(np.random.default_rng(7).choice(3, size=100000, p=soll), minlength=3) / 100000        # Gegenprobe mit numpy
    assert np.abs(numpy_haeufig - soll).max() < 0.01


def test_waehle_index_grenzen():
    assert A.waehle_index([1.0, 1.0, 1.0], 0.0) == 0 and A.waehle_index([1.0, 1.0, 1.0], 0.999999) == 2
    assert A.waehle_index([1.0, 1.0, 1.0], 1 / 3) == 0            # kumuliert 1,0 ≥ u · 3 = 1,0: das erste Literal (≥, nicht >)
    assert A.waehle_index([5.0], 0.7) == 0


# --- Modelle, Unerfüllbares, Umnummerieren -------------------------------------------------------------------------------------------------

def test_gemeldete_modelle_erfuellen_alle_klauseln_und_unerfuellbares_wird_nie_geloest():
    gel = 0
    for seed in range(40):
        inst = I.rand3(12, 51, seed)                                          # m/n = 4,25, n klein: gemischt erfüllbar und unerfüllbar
        modelle = A.alle_modelle(inst.n, inst.klauseln)
        lauf = A.probsat_lauf(inst.n, inst.klauseln, 3000, seed)
        if lauf.modell is not None:
            gel += 1
            assert all(any(lauf.modell[abs(l)] == (l > 0) for l in c) for c in inst.klauseln)
            assert "".join("1" if lauf.modell[v] else "0" for v in range(1, 13)) in modelle
        if not modelle:
            assert lauf.modell is None and lauf.kleinste >= 1
    assert gel > 0


def test_umnummerieren_aendert_die_aussage_nicht():
    inst = I.rand3(14, 56, 6)
    perm = list(range(1, 15))
    SplitMix64(4).shuffle(perm)
    neu = [tuple((perm[abs(l) - 1]) * (1 if l > 0 else -1) for l in c) for c in inst.klauseln]
    for seed in range(5):
        lauf = A.probsat_lauf(14, neu, 5000, seed)
        if lauf.modell is not None:
            rueck = {v: lauf.modell[perm[v - 1]] for v in range(1, 15)}
            assert all(any(rueck[abs(l)] == (l > 0) for l in c) for c in inst.klauseln)


def test_alle_acht_klauseln_jede_belegung_verletzt_genau_eine():
    u = S.alle_klauseln(3)
    assert len(u.klauseln) == 8 and A.verletzte_je_belegung(3, u.klauseln) == [1] * 8
    lauf = A.probsat_lauf(3, u.klauseln, 1000, 7)
    assert lauf.modell is None and lauf.kleinste == 1 and lauf.verletzt_am_ende == 1 and lauf.flips == 1000
    assert all(m == 1 for _, m in lauf.verlauf)


def test_schubfach_wird_nie_geloest_kleinste_zahl_mindestens_eins():
    inst = S.schubfach(4)
    lauf = A.probsat_lauf(inst.n, inst.klauseln, 5000, 3)
    assert lauf.modell is None and lauf.kleinste >= 1


def test_klausel_und_literal_text_und_zaehlung():
    assert A.klausel_text((1, -2, 3)) == "(x1 ∨ ¬x2 ∨ x3)" and A.literal_text(-4) == "¬x4"
    assert A.zahl_text(1.27418) == "1,2742"
    assert [A.wahre_literale(c, "00000") for c in S.HAND_KLAUSELN] == [0, 2, 1, 1, 3, 1, 3]       # Handrechnung, Belegung 00000


def test_enumeration_gegen_itertools_unabhaengig():
    kl = [(1, 2), (-1, 2), (1, -2)]
    modelle = [b for b in itertools.product((0, 1), repeat=2) if all(any((b[abs(l) - 1] == 1) == (l > 0) for l in c) for c in kl)]
    assert modelle == [(1, 1)] and A.alle_modelle(2, kl) == ["11"]

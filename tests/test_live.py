"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige (lks_live.py). Der Zwischenspeicher ändert keine Zahl: die aus Einheiten zusammengesetzte Messreihe ist
bitgleich zu `messe_zufall_live` und `messe_struktur_live`, ein anderer Parameter kommt nie aus dem Speicher, ein zweiter Aufruf rechnet nicht noch einmal."""

import lks_constants as C
import lks_evaluation as E
import lks_live as L
from streamlit.testing.v1 import AppTest

K, F, CB, EPS, SEED = 300, 1500, C.DEFAULT_CB, C.DEFAULT_EPS, 3


def _loeschen():
    for f in (L.zufall_einheit, L.rampen_einheit, L.schur_cdcl_einheit, L.schur_probsat_einheit):
        f.clear()


def _zaehler(monkeypatch):
    aufrufe = []
    echt = E.probsat_zeilen

    def zaehlend(inst, seeds, *args, **kwargs):
        aufrufe.append(tuple(seeds))
        return echt(inst, seeds, *args, **kwargs)

    monkeypatch.setattr(E, "probsat_zeilen", zaehlend)
    return aufrufe


def test_zufall_aus_einheiten_bitgleich_zu_messe_zufall_live():
    _loeschen()
    ref = E.messe_zufall_live(50, 4.26, 3, K, F, CB, EPS, SEED)
    assert L.zufall_aus_speicher(50, 4.26, 3, K, F, CB, EPS, SEED) == ref
    assert L.zufall_aus_speicher(50, 4.26, 3, K, F, CB, EPS, SEED) == ref        # zweiter Durchlauf aus dem Speicher
    assert L.zufall_aus_speicher(50, 4.26, 2, K, F, CB, EPS, SEED) == E.messe_zufall_live(50, 4.26, 2, K, F, CB, EPS, SEED)     # kürzere Reihe teilt Einheiten


def test_rampen_aus_einheiten_bitgleich_zu_messe_struktur_live():
    _loeschen()
    ref = E.messe_struktur_live("rampen160", 60, 2, K, F, CB, EPS, SEED)
    assert L.struktur_aus_speicher("rampen160", 60, 2, K, F, CB, EPS, SEED) == ref
    assert L.struktur_aus_speicher("rampen160", 60, 2, K, F, CB, EPS, SEED) == ref


def test_schur_aus_einheiten_bitgleich_zu_messe_struktur_live():
    _loeschen()
    ref = E.messe_struktur_live("schur13_3", 0, 4, K, F, CB, EPS, SEED)
    assert L.struktur_aus_speicher("schur13_3", 0, 4, K, F, CB, EPS, SEED) == ref
    assert L.struktur_aus_speicher("schur13_3", 0, 4, K, F, CB, EPS, SEED) == ref


def test_zweiter_aufruf_rechnet_nicht_anderer_parameter_schon(monkeypatch):
    _loeschen()
    aufrufe = _zaehler(monkeypatch)
    a = L.zufall_einheit(50, 4.26, 0, K, F, CB, EPS, SEED)
    L.zufall_einheit(50, 4.26, 0, K, F, CB, EPS, SEED)
    assert len(aufrufe) == 1
    b = L.zufall_einheit(50, 4.26, 0, K, F, CB, EPS, SEED + 1)        # anderer Zufalls-Seed von probSAT
    c = L.zufall_einheit(50, 4.26, 1, K, F, CB, EPS, SEED)            # andere Formel
    d = L.zufall_einheit(50, 4.26, 0, K, F, CB, EPS + 0.1, SEED)      # anderes ε
    e = L.zufall_einheit(50, 4.26, 0, K, F + 500, CB, EPS, SEED)      # anderes Umdrehungsbudget
    assert len(aufrufe) == 5
    assert a == E.zufall_einheit(50, 4.26, 0, K, F, CB, EPS, SEED) and b == E.zufall_einheit(50, 4.26, 0, K, F, CB, EPS, SEED + 1)
    assert c == E.zufall_einheit(50, 4.26, 1, K, F, CB, EPS, SEED) and d == E.zufall_einheit(50, 4.26, 0, K, F, CB, EPS + 0.1, SEED)
    assert e == E.zufall_einheit(50, 4.26, 0, K, F + 500, CB, EPS, SEED)


def test_fortschrittsanzeige_liefert_ergebnisse_in_reihenfolge_und_ohne_fehler():
    def skript():
        import streamlit as st
        import lks_live as L

        erg = L.mit_fortschritt("Probe", [("eins", lambda: 10), ("zwei", lambda: 20), ("drei", lambda: 30)])
        st.write(f"ergebnis {erg}")

    at = AppTest.from_function(skript)
    at.run(timeout=60)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("ergebnis [10, 20, 30]" in m.value for m in at.markdown)

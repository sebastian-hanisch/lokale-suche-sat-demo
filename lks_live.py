"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige.

Jede Live-Messreihe besteht aus Einheiten (eine Formel, ein Konfliktgraph, ein probSAT-Lauf auf der Schur-Instanz). Jede Einheit ist eine reine Funktion ihrer Parameter (die
Formeln sind deterministisch, SplitMix64; der Zufalls-Seed von probSAT steckt im Schlüssel) und liegt einzeln im Zwischenspeicher (`st.cache_data`, kleine `max_entries`); die
Anzeige zählt die fertigen Einheiten (`mit_fortschritt`). Ein zweiter Klick mit denselben Einstellungen antwortet aus dem Speicher; eine Reihe mit weniger Formeln teilt ihre
Einheiten mit einer längeren. Die Ergebnisse sind bitgleich zu `messe_zufall_live` und `messe_struktur_live` (`tests/test_live.py`). Rechnung, Zahlen und Aussagen ändern
sich nicht."""

import streamlit as st

import lks_constants as C
import lks_evaluation as E


@st.cache_data(show_spinner=False, max_entries=48)
def zufall_einheit(n, verhaeltnis, index, konflikte, flips, cb, eps, seed):
    return E.zufall_einheit(n, verhaeltnis, index, konflikte, flips, cb, eps, seed)


@st.cache_data(show_spinner=False, max_entries=48)
def rampen_einheit(groesse, gs, konflikte, flips, cb, eps, seed):
    return E.rampen_einheit(groesse, gs, konflikte, flips, cb, eps, seed)


@st.cache_data(show_spinner=False, max_entries=8)
def schur_cdcl_einheit(familie, konflikte):
    return E.schur_cdcl_einheit(familie, konflikte)


@st.cache_data(show_spinner=False, max_entries=48)
def schur_probsat_einheit(familie, cdcl_antwort, seed, flips, cb, eps):
    return E.schur_probsat_einheit(familie, cdcl_antwort, seed, flips, cb, eps)


def mit_fortschritt(titel: str, schritte: list) -> list:
    """Führt die Schritte nacheinander aus und zeigt, wie viele fertig sind. `schritte`: Liste aus (Beschriftung, Funktion ohne Argumente); die Funktion liefert das Ergebnis
    (aus dem Zwischenspeicher oder frisch gerechnet). Rückgabe: die Ergebnisse in der Reihenfolge der Schritte."""
    n = len(schritte)
    ergebnisse = []
    with st.status(titel, expanded=True) as status:
        balken = st.progress(0.0, text=f"0 von {n} fertig")
        for i, (beschriftung, rechne) in enumerate(schritte):
            balken.progress(i / n, text=f"{beschriftung} (Schritt {i + 1} von {n})")
            ergebnisse.append(rechne())
        balken.progress(1.0, text=f"{n} von {n} fertig")
        status.update(label=f"{titel}: fertig", state="complete", expanded=False)
    return ergebnisse


def _ohne_anzeige(schritte: list) -> list:
    return [rechne() for _, rechne in schritte]


def zufall_schritte(n, verhaeltnis, anzahl, konflikte, flips, cb, eps, seed) -> list:
    return [(f"Formel {i + 1} von {anzahl}: CDCL und ein probSAT-Lauf", lambda i=i: zufall_einheit(n, verhaeltnis, i, konflikte, flips, cb, eps, seed)) for i in range(anzahl)]


def struktur_schritte(familie, groesse, anzahl, konflikte, flips, cb, eps, seed) -> list:
    if familie.startswith("rampen"):
        return [(f"Graph {i + 1} von {anzahl}: CDCL und drei probSAT-Läufe", lambda gs=gs: rampen_einheit(groesse, gs, konflikte, flips, cb, eps, seed))
                for i, gs in enumerate(range(C.RAMPEN_SEED_START, C.RAMPEN_SEED_START + anzahl))]
    gemerkt = {}

    def cdcl():
        gemerkt["antwort"] = (c := schur_cdcl_einheit(familie, konflikte))["antwort"]
        return c

    return [("CDCL auf der Schur-Instanz", cdcl)] + [
        (f"probSAT-Lauf {i + 1} von {anzahl}", lambda s=s: schur_probsat_einheit(familie, gemerkt["antwort"], s, flips, cb, eps)) for i, s in enumerate(range(seed, seed + anzahl))]


def zufall(n, verhaeltnis, anzahl, konflikte, flips, cb, eps, seed) -> dict:
    """Die Live-Messreihe auf Zufallsformeln mit Fortschrittsanzeige (je Formel ein Schritt). Wie `E.messe_zufall_live`, mit Zwischenspeicher."""
    formeln = mit_fortschritt("Die Messreihe läuft", zufall_schritte(n, verhaeltnis, anzahl, konflikte, flips, cb, eps, seed))
    return E.zufall_aufbauen(n, verhaeltnis, formeln)


def zufall_aus_speicher(n, verhaeltnis, anzahl, konflikte, flips, cb, eps, seed) -> dict:
    """Wie `zufall`, ohne Anzeige."""
    return E.zufall_aufbauen(n, verhaeltnis, _ohne_anzeige(zufall_schritte(n, verhaeltnis, anzahl, konflikte, flips, cb, eps, seed)))


def struktur(familie, groesse, anzahl, konflikte, flips, cb, eps, seed) -> dict:
    """Die Live-Messreihe einer Strukturaufgabe mit Fortschrittsanzeige (je Graph bzw. je probSAT-Lauf ein Schritt). Wie `E.messe_struktur_live`, mit Zwischenspeicher."""
    einheiten = mit_fortschritt("Die Messreihe läuft", struktur_schritte(familie, groesse, anzahl, konflikte, flips, cb, eps, seed))
    return E.struktur_aufbauen(familie, groesse, einheiten)


def struktur_aus_speicher(familie, groesse, anzahl, konflikte, flips, cb, eps, seed) -> dict:
    """Wie `struktur`, ohne Anzeige."""
    return E.struktur_aufbauen(familie, groesse, _ohne_anzeige(struktur_schritte(familie, groesse, anzahl, konflikte, flips, cb, eps, seed)))

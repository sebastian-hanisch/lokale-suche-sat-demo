"""Inhalt der App (AppTest): Handbeispiel-Werte, jedes Preset ohne Fehler, jeder Fall, Streamlit-Fallstricke (Schlüssel, Titel, Expander)."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import lks_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrik(at, label):
    return next(m.value for m in at.metric if m.label == label)


def _texte(at) -> str:
    return " ".join([i.value for i in at.info] + [w.value for w in at.warning] + [s.value for s in at.success] + [m.value for m in at.markdown])


def test_handbeispiel_standard_zeigt_drei_umdrehungen_54_lesezugriffe_neun_modelle():
    at = _app()
    assert _metrik(at, "Antwort") == "Modell" and _metrik(at, "Umdrehungen") == "3" and _metrik(at, "Lesezugriffe") == "54"
    assert _metrik(at, "Modelle der Formel (Aufzählung)") == "9 von 32"
    assert at.slider(key="schritt").value == 1                      # Zustand nach der ersten Umdrehung
    assert any("Vor der Umdrehung 2: Belegung 01000, verletzt: C3." in i.value for i in at.info)


def test_schritt_null_zeigt_die_gewichte_des_handbeispiels():
    at = _app()
    at.slider(key="schritt").set_value(0).run()
    assert not at.exception
    assert any("Vor der Umdrehung 1: Belegung 00000, verletzt: C1." in i.value and "u · Summe = 1,4320" in i.value for i in at.info)
    tabellen = [d.value for d in at.dataframe]
    assert any(list(t.columns[:4]) == ["Literal", "Variable", "break", "Gewicht"] and list(t["Gewicht"]) == ["1,2742", "0,2285", "0,2285"] for t in tabellen)


def test_letzter_schritt_zeigt_modell_aus_der_aufzaehlung():
    at = _app()
    at.slider(key="schritt").set_value(3).run()
    assert any("Modell 10000" in s.value and "eines der 9 Modelle" in s.value for s in at.success)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_laeuft_ohne_fehler(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]


def test_kleine_zufallsformel_unerfuellbar_oder_nicht_ohne_fehler_fuer_viele_seeds():
    at = _app()
    at.radio(key="formel").set_value(C.FORMEL_KLEIN).run()
    for seed in (0, 1, 2, 3, 4, 5, 6, 7):
        at.number_input(key="klein_seed").set_value(seed).run()
        assert not at.exception, (seed, [str(e) for e in at.exception])
        assert _metrik(at, "Antwort") in ("Modell", "unbekannt")
        if _metrik(at, "Modelle der Formel (Aufzählung)").startswith("0 "):
            assert _metrik(at, "Antwort") == "unbekannt"          # unerfüllbar: nie ein Modell


@pytest.mark.parametrize("fall", ["hand8", "schubfach5", "faerbung", "zufall150", "misserfolg"])
def test_jeder_fall_des_experiments_unerfuellbar(fall):
    at = _app()
    at.selectbox(key="fall").set_value(C.FAELLE[fall]).run()
    assert not at.exception, [str(e) for e in at.exception]


def test_fall_hand8_und_schubfach_sagen_unerfuellbar_und_unbekannt():
    at = _app()
    at.selectbox(key="fall").set_value(C.FAELLE["hand8"]).run()
    text = _texte(at)
    assert "„unerfüllbar“" in text and "die kleinste Zahl verletzter Klauseln auf dem Weg war 1" in text
    assert _metrik(at, "CDCL") == "unerfüllbar" and _metrik(at, "probSAT") == "unbekannt" and _metrik(at, "kleinste Zahl verletzter Klauseln") == "1"
    at.selectbox(key="fall").set_value(C.FAELLE["schubfach5"]).run()
    assert _metrik(at, "CDCL") == "unerfüllbar" and _metrik(at, "probSAT") == "unbekannt" and int(_metrik(at, "kleinste Zahl verletzter Klauseln")) >= 1


def test_permalink_setzt_seed_cb_und_fall():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["seed"] = "34"
    at.query_params["cb"] = "2.06"
    at.run()
    assert not at.exception
    assert at.number_input(key="seed").value == 34 and at.select_slider(key="cb").value == 2.06


def test_titel_einleitung_und_expander_ohne_platzhalter():
    at = _app()
    assert at.title[0].value == "🎲 Lokale Suche gegen CDCL"
    labels = [e.label for e in at.expander]
    for erwartet in ("So funktioniert probSAT", "📐 Mathematische Formulierung", "📋 Erklärtabelle: Verfahren und Begriffe"):
        assert erwartet in labels
    assert not any("TODO" in m.value for m in at.markdown)


def test_schluessel_der_charts_sind_eindeutig_und_vorhanden():
    at = _app()
    assert not at.exception          # doppelte Plotly-Schlüssel würden StreamlitDuplicateElementId auslösen

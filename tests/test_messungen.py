"""Die vorgerechneten Messreihen (`lks_messungen.json`): Aufbau, innere Widerspruchsfreiheit, Neumessung billiger Zellen gegen die Datei, Live-Funktionen."""

import json

import pytest

import lks_constants as C
import lks_evaluation as E
import lks_instanzen as I
import lks_scenario as S
from lks_probsat import probsat


@pytest.fixture(scope="module")
def daten():
    d = E.lade_messungen()
    assert d, "lks_messungen.json fehlt oder ist leer"
    return d


def test_meta_und_kern_versionen(daten):
    m = daten["meta"]
    assert m["cdcl_budget"] == C.BUDGET_REFERENZ_KONFLIKTE == 20000 and m["flip_budget"] == C.BUDGET_REFERENZ_FLIPS == 300000
    assert (m["cb"], m["eps"], m["cb_alt"]) == (2.3, 0.9, 2.06) and m["probsat_seeds"] == [1, 2, 3]
    assert m["formel_seeds"] == list(range(8000, 8012)) and m["rampen_seeds"] == list(range(500, 510))
    assert m["kern"] == {"cdcl": "832b2c10dfdea62d", "probsat": "8caf126238c62c92", "rng": "5d5d8f45d0e1eddf", "instanzen": "6795de796b66fff8"}
    assert m["skript"] == "tools/messungen.py"


def test_zellen_vollstaendig_und_aufbau(daten):
    assert set(daten["zufall"]) == {f"n{n}_v{v}" for n in C.ZUFALL_N for v in C.VERHAELTNISSE}
    for schluessel, z in daten["zufall"].items():
        assert z["m"] == S.klauselzahl(z["n"], z["verhaeltnis"]) and len(z["formeln"]) == C.ANZAHL_FORMELN
        assert [f["seed"] for f in z["formeln"]] == list(range(8000, 8012))
        for f in z["formeln"]:
            assert f["cdcl"]["antwort"] in (True, False, None) and f["cdcl"]["konflikte"] >= 0 and f["cdcl"]["konflikte"] <= 20000 + 1
            assert [r["seed"] for r in f["probsat"]] == [1, 2, 3]
            assert ("probsat_cb_alt" in f) == (z["n"] >= 300)
    assert set(daten["struktur"]) == set(C.STRUKTUREN)
    assert len(daten["struktur"]["rampen160"]["instanzen"]) == 10
    assert all(len(i["probsat"]) == 5 for i in daten["struktur"]["rampen160"]["instanzen"])
    assert all(len(daten["struktur"][k]["instanzen"][0]["probsat"]) == 20 for k in ("schur43_4", "schur13_3"))


def test_probsat_loest_nie_eine_von_cdcl_bewiesen_unerfuellbare_formel(daten):
    zeilen = [f for z in daten["zufall"].values() for f in z["formeln"]] + [i for s in daten["struktur"].values() for i in s["instanzen"]]
    unerf = [f for f in zeilen if f["cdcl"]["antwort"] is False]
    assert unerf, "keine unerfüllbare Formel in den Messreihen"
    for f in unerf:
        assert not any(r["geloest"] for r in f["probsat"])
        assert all(r["verletzt_am_ende"] >= 1 and r["flips"] == 300000 for r in f["probsat"])


def test_gleiche_formel_gleiche_antwort_in_beiden_gewichtungen_nur_zaehler_unterscheiden_sich(daten):
    """Die Zeile cb = 2,06 nutzt dieselben Formeln und Zufalls-Seeds wie cb = 2,3: bei bewiesen unerfüllbaren Formeln löst keine Zeile etwas."""
    for z in daten["zufall"].values():
        for f in z["formeln"]:
            if "probsat_cb_alt" in f and f["cdcl"]["antwort"] is False:
                assert not any(r["geloest"] for r in f["probsat_cb_alt"])


def test_flips_und_lesezugriffe_sind_stimmig(daten):
    for z in daten["zufall"].values():
        for f in z["formeln"]:
            for r in f["probsat"]:
                assert 0 <= r["flips"] <= 300000 and r["lesezugriffe"] >= 3 * z["m"]      # Start: 3 · m Lesezugriffe
                assert (r["verletzt_am_ende"] == 0) == r["geloest"]
                if not r["geloest"]:
                    assert r["flips"] == 300000                                           # ohne Lösung wird das Budget ausgeschöpft


def test_neumessung_einer_billigen_zelle_gleicht_der_datei(daten):
    """n = 100, m/n = 4,0 (billig): die erste Formel mit CDCL und den drei probSAT-Läufen noch einmal gerechnet; muss die Datei bis aufs Zählen treffen."""
    z = daten["zufall"]["n100_v4.0"]["formeln"][0]
    inst = S.zufall_formel(100, 4.0, 0)
    assert inst.klauseln == I.rand3(100, 400, 8000).klauseln
    c = E.cdcl_zeile(inst, 20000)
    assert c == z["cdcl"]
    zeilen = E.probsat_zeilen(inst, (1, 2, 3), 300000, 2.3, 0.9, c["antwort"])
    assert zeilen == z["probsat"]


def test_live_funktionen_gleichen_der_datei_in_einer_kleinen_zelle(daten):
    live = E.messe_zufall_live(100, 4.0, 2, 20000, 300000, 2.3, 0.9, 1)
    ref = daten["zufall"]["n100_v4.0"]["formeln"]
    assert [f["cdcl"] for f in live["formeln"]] == [f["cdcl"] for f in ref[:2]]
    assert [f["probsat"][0] for f in live["formeln"]] == [f["probsat"][0] for f in ref[:2]]       # Zufalls-Seed 1 = erster Lauf der Referenz
    assert live["m"] == 400 and live["n"] == 100


def test_live_struktur_schur13_gleicht_der_datei(daten):
    live = E.messe_struktur_live("schur13_3", 0, 3, 20000, 300000, 2.3, 0.9, 1)
    ref = daten["struktur"]["schur13_3"]["instanzen"][0]
    assert live["instanzen"][0]["cdcl"] == ref["cdcl"] and live["instanzen"][0]["probsat"] == ref["probsat"][:3]
    assert live["label"] == "Schur k = 3, n = 13"


def test_die_datei_ist_gueltiges_json_mit_unix_zeilenenden():
    roh = E.MESSDATEI.read_bytes()
    assert b"\r\n" not in roh and json.loads(roh.decode("utf-8"))


def test_probsat_kopie_und_messung_gleichen_sich_fuer_einen_zufalls_seed(daten):
    z = daten["zufall"]["n100_v4.0"]["formeln"][3]
    inst = S.zufall_formel(100, 4.0, 3)
    p = probsat(inst.n, inst.klauseln, 300000, 2)
    r = z["probsat"][1]
    assert (p.modell is not None, p.flips, p.lesezugriffe, p.verletzt_am_ende) == (r["geloest"], r["flips"], r["lesezugriffe"], r["verletzt_am_ende"])


def test_live_struktur_rampen_kleine_graphen_und_schlechte_familie():
    live = E.messe_struktur_live("rampen160", 60, 2, 5000, 20000, 2.3, 0.9, 1)
    assert len(live["instanzen"]) == 2 and [i["seed"] for i in live["instanzen"]] == [500, 501]
    assert all(len(i["probsat"]) == 3 and [r["seed"] for r in i["probsat"]] == [1, 2, 3] for i in live["instanzen"])
    assert live["label"] == "Aufträge auf Rampen (3-Färbung, n = 60 Aufträge, Grad 4,5)"
    for i in live["instanzen"]:
        if i["cdcl"]["antwort"] is False:
            assert not any(r["geloest"] for r in i["probsat"])
    with pytest.raises(KeyError):
        E.messe_struktur_live("gibt_es_nicht", 0, 1, 100, 100, 2.3, 0.9, 1)

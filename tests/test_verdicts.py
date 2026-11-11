"""Verdikte und Kennzahlen als reine Funktionen: Schwellen und jede Zahl im Text an handgesetzten Zeilen (DEMO-PLAYBOOK §12)."""

import lks_algorithm as A
import lks_evaluation as E


def zelle(**kw) -> E.Zelle:
    basis = dict(n_formeln=12, c_erf=4, c_unerf=3, c_unb=5, p_laeufe=36, p_gel=20, p_formeln=8, p_gemischt=0, p_laeufe_erf=36, p_gel_erf=20,
                 p_laeufe_unerf=0, p_gel_unerf=0, median_cdcl=1000.0, median_probsat=100.0)
    basis.update(kw)
    return E.Zelle(**basis)


def lauf(antwort, konflikte, lesen, *probsat):
    return {"seed": 1, "cdcl": {"antwort": antwort, "konflikte": konflikte, "lesezugriffe": lesen},
            "probsat": [{"seed": i, "geloest": g, "flips": f, "lesezugriffe": r, "verletzt_am_ende": v} for i, (g, f, r, v) in enumerate(probsat, 1)]}


# --- Kennzahlen --------------------------------------------------------------------------------------------------------------------------

def test_kennzahlen_von_hand():
    zeilen = [lauf(True, 10, 100, (True, 5, 40, 0), (True, 6, 60, 0), (False, 99, 500, 2)),
              lauf(True, 20, 300, (True, 7, 80, 0), (False, 99, 500, 1), (False, 99, 500, 1)),
              lauf(False, 30, 900, (False, 99, 500, 1), (False, 99, 500, 3), (False, 99, 500, 1)),
              lauf(None, 20000, 9999, (True, 8, 20, 0), (True, 9, 100, 0), (True, 3, 30, 0))]
    z = E.kennzahlen(zeilen)
    assert (z.n_formeln, z.c_erf, z.c_unerf, z.c_unb) == (4, 2, 1, 1)
    assert (z.p_laeufe, z.p_gel, z.p_formeln, z.p_gemischt) == (12, 6, 3, 2)
    assert (z.p_laeufe_erf, z.p_gel_erf, z.p_laeufe_unerf, z.p_gel_unerf) == (6, 3, 3, 0)
    assert z.median_cdcl == 200.0                       # Median von 100 und 300
    assert z.median_probsat == 50.0                     # gelöste: 40, 60, 80, 20, 100, 30 → sortiert 20, 30, 40, 60, 80, 100: (40 + 60) / 2
    assert z.faktor == 4.0 and z.untere_schranke          # c_erf = 2 < 3


def test_faktor_und_untere_schranke():
    assert zelle().faktor == 10.0 and not zelle().untere_schranke
    assert zelle(c_erf=2).untere_schranke and zelle(p_gel=2).untere_schranke and not zelle(c_erf=3, p_gel=3).untere_schranke
    assert zelle(median_cdcl=None).faktor is None and zelle(median_probsat=None).faktor is None


def test_verhaeltnis_text():
    assert E.verhaeltnis_text(zelle(c_erf=5)) == "CDCL 10-mal mehr"
    assert E.verhaeltnis_text(zelle(median_cdcl=100.0, median_probsat=5000.0)) == "probSAT 50-mal mehr"
    assert E.verhaeltnis_text(zelle(median_cdcl=300.0, median_probsat=100.0)) == "CDCL 3,0-mal mehr"
    assert E.verhaeltnis_text(zelle(c_erf=2)) == "CDCL 10-mal mehr (Richtwert)"
    assert E.verhaeltnis_text(zelle(median_cdcl=None)) == "–"


# --- Zufallszelle -----------------------------------------------------------------------------------------------------------------------

def test_verdict_zufall_text_von_hand_und_ampel_gruen():
    z = zelle(c_erf=6, c_unerf=2, c_unb=4, p_laeufe=36, p_gel=30, p_formeln=10, median_cdcl=50000.0, median_probsat=5000.0)
    kind, text = E.verdict_zufall("Zufalls-3-SAT n = 150, m/n = 4,2", z, 20000, 300000)
    assert kind == "success"
    assert text == ("Zufalls-3-SAT n = 150, m/n = 4,2: probSAT löst 30 von 36 Läufen (10 von 12 Formeln in mindestens einem Lauf, Budget 300.000 Umdrehungen). "
                    "CDCL entscheidet 8 von 12 Formeln (6 erfüllbar, 2 unerfüllbar), 4 bleiben am Budget von 20.000 Konflikten offen. "
                    "Lesezugriffe im Median der Gelösten: CDCL 50.000 (aus 6 Formeln), probSAT 5.000 (aus 30 Läufen); CDCL braucht im Median 10-mal so viele Lesezugriffe wie probSAT. "
                    "2 Formeln beweist nur CDCL als unerfüllbar; probSAT findet dort kein Modell und kann es nicht beweisen.")


def test_verdict_zufall_gelb_bei_weniger_als_drei_werten_mit_untere_schranke():
    kind, text = E.verdict_zufall("X", zelle(c_erf=2, c_unerf=0, c_unb=10, median_cdcl=6000000.0, median_probsat=110000.0, p_gemischt=3), 20000, 300000)
    assert kind == "warning"
    assert "CDCL braucht im Median 55-mal so viele" in text and "Der Median von CDCL (2 Werte) stammt aus weniger als 3 gelösten Fällen" in text
    assert "untere Schranke" in text and "Bei 3 Formeln gelang nur ein Teil der probSAT-Läufe" in text
    kind2, text2 = E.verdict_zufall("X", zelle(p_gel=1, c_erf=5), 20000, 300000)
    assert kind2 == "warning" and "probSAT (1 Wert)" in text2


def test_verdict_zufall_probsat_braucht_mehr_und_fehlende_mediane():
    kind, text = E.verdict_zufall("X", zelle(median_cdcl=100.0, median_probsat=3000.0, c_erf=4), 20000, 300000)
    assert kind == "success" and "probSAT braucht im Median 30-mal so viele Lesezugriffe wie CDCL" in text
    _, t = E.verdict_zufall("X", zelle(c_erf=0, median_cdcl=None), 20000, 300000)
    assert "CDCL löst keine erfüllbare Formel, es gibt keinen CDCL-Median und kein Verhältnis." in t
    _, t = E.verdict_zufall("X", zelle(p_gel=0, median_probsat=None), 20000, 300000)
    assert "probSAT löst keinen Lauf, es gibt keinen probSAT-Median und kein Verhältnis." in t
    kind, t = E.verdict_zufall("X", zelle(c_erf=0, p_gel=0, median_cdcl=None, median_probsat=None), 20000, 300000)
    assert kind == "warning" and "Keines der Verfahren löst einen Fall" in t


def test_verdict_zufall_wachstum_nennt_jede_zelle():
    kind, text = E.verdict_zufall_wachstum({300: (zelle(c_erf=2, c_unerf=0, p_gel=33), None), 150: (zelle(c_erf=7, c_unerf=0, p_gel=36), None)})
    assert kind == "info"
    assert text == "n = 150: probSAT 36 von 36 Läufen, CDCL 7 von 12 Formeln entschieden; n = 300: probSAT 33 von 36 Läufen, CDCL 2 von 12 Formeln entschieden."


# --- Struktur -----------------------------------------------------------------------------------------------------------------------------

def test_verdict_struktur_von_hand():
    z = zelle(n_formeln=10, c_erf=8, c_unerf=2, c_unb=0, p_laeufe=50, p_gel=34, p_laeufe_erf=40, p_gel_erf=34, median_cdcl=21054.0, median_probsat=1080892.0)
    kind, text = E.verdict_struktur("Rampen", z, 20000, 300000)
    assert kind == "success"
    assert text == ("Rampen: CDCL löst 8 von 10 Instanzen (2 unerfüllbar, 0 am Budget von 20.000 Konflikten offen). "
                    "probSAT löst auf den 8 erfüllbaren Instanzen 34 von 40 Läufen (Budget 300.000 Umdrehungen). "
                    "Lesezugriffe im Median der Gelösten: CDCL 21.054 (aus 8 Instanzen), probSAT 1.080.892 (aus 34 Läufen); probSAT braucht im Median 51-mal so viele Lesezugriffe wie CDCL. "
                    "probSAT-Läufe ohne Lösung fehlen im Median; das Verhältnis ist deshalb eine untere Schranke des Vorsprungs von CDCL.")


def test_verdict_struktur_ohne_probsat_loesung_und_ein_lauf():
    z = zelle(n_formeln=4, c_erf=4, c_unerf=0, c_unb=0, p_laeufe=20, p_gel=0, p_laeufe_erf=20, p_gel_erf=0, median_probsat=None)
    kind, text = E.verdict_struktur("Latin", z, 20000, 300000)
    assert kind == "warning" and "probSAT löst auf den 4 erfüllbaren Instanzen 0 von 20 Läufen" in text and "probSAT löst keinen Lauf" in text
    z1 = zelle(c_erf=1, p_laeufe_erf=1, p_gel_erf=1, p_gel=1)
    assert "1 von 1 Lauf (Budget" in E.verdict_struktur("S", z1, 20000, 300000)[1]
    assert "CDCL 1.000 (aus 1 Instanz), probSAT" in E.verdict_struktur("S", z1, 20000, 300000)[1]


# --- Unerfüllbar und Aufgeben ----------------------------------------------------------------------------------------------------------

def test_verdict_unerfuellbar_alle_zweige():
    kind, text = E.verdict_unerfuellbar("Schubfach", False, 159, 300000, 1, False)
    assert kind == "warning"
    assert text == ("Schubfach: CDCL antwortet nach 159 Konflikten „unerfüllbar“. "
                    "probSAT hat nach 300.000 Umdrehungen kein Modell; die kleinste Zahl verletzter Klauseln auf dem Weg war 1. Die Antwort ist „unbekannt“, nicht „unerfüllbar“.")
    kind, text = E.verdict_unerfuellbar("Z", True, 80, 300000, 2, False)
    assert kind == "info" and "CDCL findet nach 80 Konflikten ein Modell" in text and "die kleinste Zahl verletzter Klauseln auf dem Weg war 2" in text
    kind, text = E.verdict_unerfuellbar("Z", None, 20000, 1000, 3, False)
    assert kind == "warning" and "CDCL bleibt nach 20.000 Konflikten am Budget: „unbekannt“" in text
    kind, text = E.verdict_unerfuellbar("Z", True, 5, 12, 0, True, True)
    assert kind == "info" and "probSAT findet nach 12 Umdrehungen ein Modell (gegen die Klauseln geprüft)" in text


def test_verdict_misserfolg_drei_zweige():
    kind, text = E.verdict_misserfolg([(1, True, 8949, 0), (2, False, 300000, 4)])
    assert kind == "warning"
    assert text == ("Dieselbe Formel ist erfüllbar (Zufalls-Seed 1: Modell nach 8.949 Umdrehungen, gegen die Klauseln geprüft), und doch endet der Lauf mit "
                    "Zufalls-Seed 2 nach 300.000 Umdrehungen ohne Modell (kleinste Zahl verletzter Klauseln 4). Ein Lauf ohne Lösung beweist nicht, dass es keine gibt.")
    kind, text = E.verdict_misserfolg([(1, True, 10, 0), (2, True, 20, 0)])
    assert kind == "info" and "Alle 2 Läufe finden ein Modell" in text
    kind, text = E.verdict_misserfolg([(1, False, 10, 3), (2, False, 20, 2)])
    assert kind == "warning" and "kleinste Zahl verletzter Klauseln: 2" in text


def test_verdict_anteil_unerfuellbar_von_hand():
    z = zelle(c_erf=4, c_unerf=8, c_unb=0, p_laeufe_unerf=24, p_gel_unerf=0, p_laeufe_erf=12, p_gel_erf=12)
    kind, text = E.verdict_anteil_unerfuellbar("n = 150", z, 300000)
    assert kind == "warning"
    assert text == ("n = 150: CDCL beweist 8 von 12 Formeln als unerfüllbar und findet bei 4 ein Modell (0 offen). "
                    "probSAT findet bei den unerfüllbaren Formeln in 0 von 24 Läufen ein Modell (es gibt keins) und beweist nichts; nach 300.000 Umdrehungen lautet seine Antwort dort „unbekannt“. "
                    "Bei den 4 erfüllbaren Formeln löst es 12 von 12 Läufen.")
    assert E.verdict_anteil_unerfuellbar("x", zelle(c_unerf=0), 1000)[0] == "info"


# --- Schrittbeschreibung ---------------------------------------------------------------------------------------------------------------

def test_schritt_text_handbeispiel_schritt_null_und_ende():
    s = A.Schritt(0, "00000", [1], 1, (1, 2, 3), [0, 1, 1], [1.2742, 0.2285, 0.2285], 1.7312, 0.827190, 1.4320, 1, 2, 32)
    t = E.schritt_text(s, 5, True)
    assert t == ("Vor der Umdrehung 1: Belegung 00000, verletzt: C1. Gewählt wird die Klausel C1 (x1 ∨ x2 ∨ x3) (Platz 1 von 1 in der Liste der verletzten Klauseln). "
                 "Mit u = 0,8272 ergibt sich u · Summe = 1,4320 bei der Gesamtsumme 1,7312; das 2. Literal (x2) überschreitet diese Marke zuerst. x2 wird umgedreht.")
    assert E.schritt_text(A.Schritt(3, "10000", []), 5, True) == "Nach 3 Umdrehungen: Belegung 10000, keine Klausel verletzt. Das ist ein Modell."
    assert "Ohne Modell lautet die Antwort „unbekannt“" in E.schritt_text(A.Schritt(9, "10001", [2, 5]), 5, False)
    assert "verletzt: C2, C5" in E.schritt_text(A.Schritt(9, "10001", [2, 5]), 5, False)


def test_kurve_punkte_von_hand():
    gel = A.Lauf({1: True}, 40, 0, 0, 0, [(0, 5), (7, 2), (40, 0)])
    assert E.kurve_punkte(gel, 300000) == ([0, 7, 40, 40], [5, 2, 0, 0])
    nicht = A.Lauf(None, 1000, 0, 3, 2, [(0, 5), (9, 2)])
    assert E.kurve_punkte(nicht, 1000) == ([0, 9, 1000], [5, 2, 2])

"""Jede Zahl der README (Abschnitt „Befunde“) wird hier nachgerechnet (DEMO-PLAYBOOK §4, §11a).

Die großen Messreihen stehen vorgerechnet in `lks_messungen.json` (Messskript `tools/messungen.py`); dieser Test liest sie mit denselben
Auswertungsfunktionen wie die App und rechnet einen Teil neu (Fälle des Experiments „Unerfüllbar“, eine Formel mit n = 300).
Zufallsformeln: 12 feste Formeln je Zelle (Zufalls-Seeds 8000 bis 8011), drei probSAT-Läufe je Formel (Zufalls-Seeds 1 bis 3),
Budgets 300.000 Umdrehungen und 20.000 Konflikte. Medianangaben stehen nur über gelöste Fälle; die Zahl der Werte steht daneben.
Die Gegenprobe mit anderen Formelmengen (`tools/gegenprobe_ausgabe.txt`) steht nicht in den Tests; die Zeile zu lateinischen Quadraten ist eine
Konstante der Vormessung (Quelle `out_v16_struktur.txt` im Planungsordner).
"""

import pytest

import lks_algorithm as A
import lks_constants as C
import lks_evaluation as E
import lks_scenario as S
from lks_instanzen import pruefe_modell


@pytest.fixture(scope="module")
def daten():
    d = E.lade_messungen()
    assert d
    return d


# (n, m/n): (CDCL erfüllbar, unerfüllbar, offen, probSAT gelöste Läufe von 36, Formeln mit Lösung, Formeln mit gemischtem Ausgang, Median CDCL, Median probSAT)
ZUFALL = {
    (100, 4.0): (12, 0, 0, 36, 12, 0, 44006.0, 30042.0),
    (100, 4.2): (6, 6, 0, 18, 6, 0, 29657.0, 78800.5),
    (100, 4.26): (6, 6, 0, 18, 6, 0, 25361.5, 55873.0),
    (150, 4.0): (12, 0, 0, 36, 12, 0, 142275.5, 54431.5),
    (150, 4.2): (6, 6, 0, 18, 6, 0, 379385.0, 69551.5),
    (150, 4.26): (4, 8, 0, 12, 4, 0, 230848.5, 130447.5),
    (300, 4.0): (7, 0, 5, 35, 12, 1, 4509853.0, 136210.0),
    (300, 4.2): (1, 0, 11, 25, 9, 1, 29671871.0, 427550.0),
    (300, 4.26): (1, 0, 11, 18, 6, 0, 44661694.0, 728636.0),
    (600, 4.0): (0, 0, 12, 35, 12, 1, None, 424326.0),
    (600, 4.2): (0, 0, 12, 21, 9, 4, None, 1763568.0),
    (600, 4.26): (0, 0, 12, 12, 6, 4, None, 3667614.0),
}


def zk(n, v, schluessel="probsat"):
    return E.kennzahlen(E.zeilen_von(E.zelle_zufall(n, v)), schluessel)


def test_aufbau_der_zellen_und_budgets(daten):
    assert daten["meta"]["cdcl_budget"] == 20000 and daten["meta"]["flip_budget"] == 300000
    assert set(daten["zufall"]) == {f"n{n}_v{v}" for n, v in ZUFALL}
    assert all(len(z["formeln"]) == 12 and all(len(f["probsat"]) == 3 for f in z["formeln"]) for z in daten["zufall"].values())


@pytest.mark.parametrize("zelle", list(ZUFALL))
def test_claim_zufallszelle(zelle):
    k = zk(*zelle)
    c_erf, c_unerf, c_unb, p_gel, p_formeln, p_gemischt, m_cdcl, m_probsat = ZUFALL[zelle]
    assert (k.c_erf, k.c_unerf, k.c_unb) == (c_erf, c_unerf, c_unb)
    assert (k.p_gel, k.p_laeufe, k.p_formeln, k.p_gemischt) == (p_gel, 36, p_formeln, p_gemischt)
    assert k.median_cdcl == m_cdcl and k.median_probsat == m_probsat


def test_claim_wachstum_cdcl_entscheidet_weniger_probsat_loest_bis_n_600():
    """Bei m/n = 4,0: CDCL löst 12, 12, 7, 0 von 12 Formeln (n = 100, 150, 300, 600), probSAT in mindestens einem Lauf 12, 12, 12, 12; Läufe 36, 36, 35, 35 von 36."""
    assert [zk(n, 4.0).c_erf for n in C.ZUFALL_N] == [12, 12, 7, 0]
    assert [zk(n, 4.0).p_formeln for n in C.ZUFALL_N] == [12, 12, 12, 12]
    assert [zk(n, 4.0).p_gel for n in C.ZUFALL_N] == [36, 36, 35, 35]
    # bei n = 300 und 600 entscheidet CDCL in keiner Zelle mit m/n ≥ 4,2 mehr als eine Formel
    assert [zk(n, v).c_erf + zk(n, v).c_unerf for n in (300, 600) for v in (4.2, 4.26)] == [1, 1, 0, 0]


def test_claim_bis_n_150_loest_probsat_genau_die_von_cdcl_gefundenen_formeln_und_nie_eine_unerfuellbare():
    for n in (100, 150):
        for v in C.VERHAELTNISSE:
            k = zk(n, v)
            assert k.p_formeln == k.c_erf and k.p_gel == 3 * k.c_erf and k.p_gel_unerf == 0 and k.p_gemischt == 0
    unerf = sum(zk(n, v).c_unerf for n in C.ZUFALL_N for v in C.VERHAELTNISSE)
    assert unerf == 26 and sum(zk(n, v).p_gel_unerf for n in C.ZUFALL_N for v in C.VERHAELTNISSE) == 0


def test_claim_lesezugriffe_verhaeltnis_je_zelle():
    """Median CDCL durch Median probSAT (nur Gelöste): kleiner als 1 bei n = 100 (4,2 und 4,26), sonst größer; bei n = 300 33-, 69- und 61-fach (letzte zwei untere Schranke)."""
    f = {z: round(zk(*z).faktor, 1) for z in ZUFALL if ZUFALL[z][6] is not None}
    assert f == {(100, 4.0): 1.5, (100, 4.2): 0.4, (100, 4.26): 0.5, (150, 4.0): 2.6, (150, 4.2): 5.5, (150, 4.26): 1.8,
                 (300, 4.0): 33.1, (300, 4.2): 69.4, (300, 4.26): 61.3}
    assert [zk(100, v).faktor < 1 for v in C.VERHAELTNISSE] == [False, True, True] and all(zk(150, v).faktor > 1 for v in C.VERHAELTNISSE)
    assert [zk(300, v).untere_schranke for v in C.VERHAELTNISSE] == [False, True, True]       # c_erf = 7 gegen 1 und 1
    assert all(zk(600, v).faktor is None for v in C.VERHAELTNISSE)                            # CDCL löst keine Formel: kein Median
    assert [round(1 / zk(100, v).faktor, 1) for v in (4.2, 4.26)] == [2.7, 2.2]               # probSAT braucht dort 2,7- bzw. 2,2-mal so viele


def test_claim_gemischte_formeln_gleiche_formel_anderer_seed(daten):
    gemischt = {z: zk(*z).p_gemischt for z in ZUFALL}
    assert sum(gemischt.values()) == 11 and [gemischt[(600, v)] for v in C.VERHAELTNISSE] == [1, 4, 4]
    gem = E.ersten_gemischten([E.zelle_zufall(n, v) for n in (300, 600) for v in (4.26, 4.2, 4.0)])
    assert gem == {"n": 300, "verhaeltnis": 4.2, "formel_seed": 8008, "geloest": [3], "nicht": [1, 2]}


def test_claim_robustheit_cb_2_06_gegen_2_3():
    """Gleiche Formeln und Zufalls-Seeds: gelöste Läufe mit cb = 2,06 weichen bei n = 300 und 600 um höchstens einen Lauf von denen mit cb = 2,3 ab; Mediane der probSAT-Läufe unterscheiden sich."""
    alt = {(n, v): zk(n, v, "probsat_cb_alt") for n in (300, 600) for v in C.VERHAELTNISSE}
    assert {z: (k.p_gel, k.p_formeln, k.median_probsat) for z, k in alt.items()} == {
        (300, 4.0): (36, 12, 199236.5), (300, 4.2): (25, 9, 422692.0), (300, 4.26): (18, 6, 991560.0),
        (600, 4.0): (34, 12, 524536.5), (600, 4.2): (20, 8, 2505882.5), (600, 4.26): (11, 5, 1993812.0)}
    assert [abs(alt[z].p_gel - zk(*z).p_gel) for z in alt] == [1, 0, 0, 1, 1, 1]


# --- Struktur --------------------------------------------------------------------------------------------------------------------------------

def sk(schluessel, daten):
    return E.kennzahlen(E.zeilen_von(daten["struktur"][schluessel]))


def test_claim_struktur(daten):
    r, s4, s3 = sk("rampen160", daten), sk("schur43_4", daten), sk("schur13_3", daten)
    assert (r.n_formeln, r.c_erf, r.c_unerf, r.c_unb) == (10, 6, 4, 0)
    assert (r.p_laeufe, r.p_gel, r.p_laeufe_erf, r.p_gel_erf, r.p_gel_unerf) == (50, 23, 30, 23, 0)
    assert (r.median_cdcl, r.median_probsat) == (27570.5, 929074.0) and round(1 / r.faktor, 1) == 33.7
    assert (s4.c_erf, s4.p_laeufe, s4.p_gel, s4.median_cdcl, s4.median_probsat) == (1, 20, 3, 2835.0, 12842630.0) and round(1 / s4.faktor) == 4530
    assert (s3.c_erf, s3.p_laeufe, s3.p_gel, s3.median_cdcl, s3.median_probsat) == (1, 20, 20, 1276.0, 22297.0) and round(1 / s3.faktor, 1) == 17.5
    assert s4.untere_schranke and s3.untere_schranke and not r.untere_schranke              # Schur: nur ein CDCL-Wert (eine Instanz)
    assert [i["seed"] for i in daten["struktur"]["rampen160"]["instanzen"] if i["cdcl"]["antwort"] is False] == [501, 504, 505, 509]
    assert C.RAMPEN_UNSAT_SEED == 501


def test_claim_latin12_zeile_ist_konstante_der_vormessung():
    assert "0 von 20" in C.LATIN12["probsat"] and "10.438" in C.LATIN12["cdcl"] and "Ordnung 12" in C.LATIN12["label"]
    assert "nicht in dieser Demo nachgerechnet" in C.LATIN12["quelle"]


# --- Unerfüllbar und Aufgeben ----------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,inst,flips,n,m,konflikte", [
    ("hand8", S.alle_klauseln(3), 1000, 3, 8, 4),
    ("schubfach5", S.schubfach(5), 300000, 30, 81, 159),
    ("faerbung", S.rampen(160, C.RAMPEN_UNSAT_SEED), 300000, 480, 1240, 151),
])
def test_claim_unerfuellbare_faelle(name, inst, flips, n, m, konflikte):
    d = E.messe_fall(inst, 20000, flips, 2.3, 0.9, 20)
    assert (d["n"], d["m"]) == (n, m) and d["cdcl_antwort"] is False and d["cdcl_konflikte"] == konflikte
    l = d["lauf"]
    assert l.modell is None and l.flips == flips and l.kleinste == 1       # die kleinste Zahl verletzter Klauseln erreicht 1 und nie 0
    kind, text = E.verdict_unerfuellbar(name, d["cdcl_antwort"], d["cdcl_konflikte"], l.flips, l.kleinste, False)
    assert f"nach {E.zahl(konflikte)} Konflikten „unerfüllbar“" in text and "kleinste Zahl verletzter Klauseln auf dem Weg war 1" in text


def test_claim_zufall_150_426_anteil_unerfuellbar():
    k = zk(150, 4.26)
    assert (k.c_unerf, k.c_erf, k.p_laeufe_unerf, k.p_gel_unerf, k.p_laeufe_erf, k.p_gel_erf) == (8, 4, 24, 0, 12, 12)


def test_claim_misserfolg_erfuellbare_formel_ein_lauf_scheitert():
    """n = 300, m/n = 4,2, Formel-Seed 8008: Zufalls-Seed 3 findet nach 27.426 Umdrehungen ein Modell, die Zufalls-Seeds 1 und 2 nicht in 300.000."""
    inst = S.zufall_formel(300, 4.2, 8)
    laeufe = {sd: A.probsat_lauf(inst.n, inst.klauseln, 300000, sd) for sd in (1, 2, 3)}
    assert laeufe[3].modell is not None and laeufe[3].flips == 27426 and pruefe_modell(inst.klauseln, laeufe[3].modell)
    assert laeufe[1].modell is None and laeufe[2].modell is None and laeufe[1].kleinste >= 1 and laeufe[2].kleinste >= 1
    kind, text = E.verdict_misserfolg([(sd, l.modell is not None, l.flips, l.kleinste) for sd, l in laeufe.items() if sd in (3, 1)])
    assert kind == "warning" and "Zufalls-Seed 3: Modell nach 27.426 Umdrehungen" in text


# --- Verdikte der Presets ------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_durchlaeuft_jedes_verdikt_mit_zahlen_der_zelle(name, daten):
    p = C.PRESETS[name]
    z = E.kennzahlen(E.zeilen_von(E.zelle_zufall(p["zufall_n"], p["zufall_v"])))
    kind, text = E.verdict_zufall("X", z, 20000, 300000)
    assert kind in ("success", "warning") and f"probSAT löst {z.p_gel} von 36 Läufen" in text and f"({z.c_erf} erfüllbar, {z.c_unerf} unerfüllbar)" in text
    assert (kind == "warning") == z.untere_schranke
    key = C.STRUKTUR_VON_LABEL[p["struktur"]]
    kind, text = E.verdict_struktur("S", sk(key, daten), 20000, 300000)
    assert kind in ("success", "warning") and f"CDCL löst {sk(key, daten).c_erf} von" in text


def test_ampel_gelb_genau_bei_untere_schranke_in_den_zufallszellen():
    gelb = [z for z in ZUFALL if zk(*z).untere_schranke]
    assert gelb == [(300, 4.2), (300, 4.26), (600, 4.0), (600, 4.2), (600, 4.26)]


# --- Neumessung (langsamster Test) ----------------------------------------------------------------------------------------------------------

def test_neumessung_n_300_erste_formel_gleicht_der_datei(daten):
    """n = 300, m/n = 4,0, Formel-Seed 8000: CDCL mit 20.000 Konflikten und drei probSAT-Läufe noch einmal gerechnet."""
    z = daten["zufall"]["n300_v4.0"]["formeln"][0]
    inst = S.zufall_formel(300, 4.0, 0)
    c = E.cdcl_zeile(inst, 20000)
    assert c == z["cdcl"]
    assert E.probsat_zeilen(inst, (1, 2, 3), 300000, 2.3, 0.9, c["antwort"]) == z["probsat"]

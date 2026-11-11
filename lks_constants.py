"""Konstanten: Regler-Grenzen, feste Annahmen, Instanzen der Messreihen, Farben und Presets."""

# --- probSAT und CDCL -----------------------------------------------------------------------------------------------------------------------
CB_OPTIONEN = (1.5, 2.0, 2.06, 2.3, 2.5, 3.0, 3.5)       # Exponent der Break-Gewichtung; 2,3 nach Balint/Schöning 2012 (3-SAT ohne Make-Anteil)
DEFAULT_CB = 2.3
EPS_OPTIONEN = (0.5, 0.9, 1.0, 2.0)                      # ε im Gewicht (ε + break)^(−cb)
DEFAULT_EPS = 0.9
FLIP_OPTIONEN = (1000, 10000, 100000, 300000)            # Obergrenze der Umdrehungen je probSAT-Lauf (300.000 wie in den vorgerechneten Messreihen)
DEFAULT_FLIPS = 300000
KONFLIKT_OPTIONEN = (1000, 5000, 20000)                  # Konfliktbudget von CDCL (20.000 wie in den vorgerechneten Messreihen)
DEFAULT_KONFLIKTE = 20000
SEED_MAX = 999999
HAND_SEED = 20                                           # Zufalls-Seed des Handbeispiels: drei Umdrehungen
BUDGET_REFERENZ_FLIPS = 300000                           # Budgets der vorgerechneten Messreihen (tools/messungen.py)
BUDGET_REFERENZ_KONFLIKTE = 20000
PROBSAT_SEEDS_REFERENZ = (1, 2, 3)                       # Zufalls-Seeds der probSAT-Läufe je Formel in den Zufallsreihen
CB_ALT = 2.06                                            # Vergleichswert der Robustheitszeile (aus dem Gedächtnis gewählt, nicht aus dem Papier)

# --- Schritt für Schritt -------------------------------------------------------------------------------------------------------------------
FORMEL_HAND = "Handbeispiel (n = 5, 7 Klauseln)"
FORMEL_KLEIN = "Kleine Zufallsformel"
FORMELN = (FORMEL_HAND, FORMEL_KLEIN)
KLEIN_N = (8, 12)                                        # Variablen der kleinen Zufallsformel (Aufzählung aller 2^n Belegungen bleibt klein)
DEFAULT_KLEIN_N, DEFAULT_KLEIN_SEED = 10, 0
MAX_SCHRITT_FLIPS = 2000                                 # so viele Umdrehungen zeigt die Schritt-für-Schritt-Ansicht höchstens

# --- Messreihen: Zufalls-3-SAT --------------------------------------------------------------------------------------------------------------
ZUFALL_N = (100, 150, 300, 600)                          # vorgerechnete Größen
VERHAELTNISSE = (4.0, 4.2, 4.26)                         # Klauseln je Variable
ANZAHL_FORMELN = 12                                      # feste Formeln je Zelle (Seeds 8000 bis 8011)
LIVE_N = (50, 150, 50)                                   # Live-Messreihe: Variablen (min, max, Schritt), nie über 150
DEFAULT_LIVE_N = 100
LIVE_ANZAHL = (2, 8, 4)                                  # Live-Messreihe: Zahl der festen Formeln bzw. Graphen (min, max, Voreinstellung)

# --- Messreihen: Struktur --------------------------------------------------------------------------------------------------------------------
RAMPEN_SEED_START = 500                                  # die zehn festen Konfliktgraphen haben die Seeds 500 bis 509
LIVE_RAMPEN_N = (60, 160, 20)                            # Aufträge je Graph in der Live-Messreihe (min, max, Schritt)
DEFAULT_LIVE_RAMPEN_N = 100
LIVE_SCHUR_LAEUFE = (3, 20, 10)                          # Schur: Zahl der probSAT-Läufe der Live-Messreihe (min, max, Voreinstellung)
STRUKTUREN = {
    "rampen160": "Aufträge auf Rampen (3-Färbung, n = 160)",
    "schur43_4": "Schur k = 4, n = 43",
    "schur13_3": "Schur k = 3, n = 13",
}
STRUKTUR_LABELS = tuple(STRUKTUREN.values())
STRUKTUR_VON_LABEL = {v: k for k, v in STRUKTUREN.items()}
SCHUR_INSTANZEN = {"schur43_4": (43, 4), "schur13_3": (13, 3)}
LATIN12 = {   # Zeile der Vormessung, kein Teil der Demo (der Erzeuger liegt nicht in der Demo): Quelle sat-cp-planung/vormessung/out_v16_struktur.txt
    "label": "Lateinisches Quadrat, Ordnung 12, Lücken 0,58 (4 Instanzen, je 5 Läufe)",
    "cdcl": "4 von 4 Instanzen erfüllbar (Median 10.438 Lesezugriffe)",
    "probsat": "0 von 20 Läufen gelöst",
    "quelle": "Vormessung mit anderer Instanzfamilie (Zufallsgenerator Python-random statt SplitMix64), probSAT mit cb = 2,06; nicht in dieser Demo nachgerechnet",
}

# --- Experiment 4 ----------------------------------------------------------------------------------------------------------------------------
FAELLE = {
    "hand8": "Handbeispiel: alle 8 Klauseln über 3 Variablen",
    "zufall150": "Zufallsformeln n = 150, m/n = 4,26",
    "schubfach5": "Schubfach h = 5 (6 Tauben, 5 Löcher)",
    "faerbung": "Unerfüllbare Färbung (Aufträge auf Rampen, n = 160)",
    "misserfolg": "Erfüllbar, aber nicht gefunden (n = 300, m/n = 4,26)",
}
FALL_LABELS = tuple(FAELLE.values())
FALL_VON_LABEL = {v: k for k, v in FAELLE.items()}
RAMPEN_UNSAT_SEED = 501                                  # erster der zehn festen Konfliktgraphen (n = 160), den CDCL als unerfüllbar beweist (tests/test_claims.py)
HAND8_FLIPS = 1000                                       # Umdrehungen im Handbeispiel „alle 8 Klauseln“

# --- Darstellung ----------------------------------------------------------------------------------------------------------------------------
COLOR_CDCL = "#2F6B65"
COLOR_PROBSAT = "#B5651D"
COLOR_GRAU = "rgba(150,150,150,0.55)"
COLOR_WAHL = "#C0392B"
COLOR_LINIE = "#4c78a8"

# --- Presets ---------------------------------------------------------------------------------------------------------------------------------
_BASIS = {"seed": 1, "flips": DEFAULT_FLIPS, "konflikte": DEFAULT_KONFLIKTE, "cb": DEFAULT_CB, "eps": DEFAULT_EPS}
PRESETS = {
    "Handbeispiel": {**_BASIS, "seed": HAND_SEED, "formel": FORMEL_HAND, "zufall_n": 300, "zufall_v": 4.0,
                     "struktur": STRUKTUREN["rampen160"], "fall": FAELLE["hand8"]},
    "Zufall wächst": {**_BASIS, "formel": FORMEL_KLEIN, "zufall_n": 600, "zufall_v": 4.0,
                      "struktur": STRUKTUREN["rampen160"], "fall": FAELLE["zufall150"]},
    "Struktur": {**_BASIS, "formel": FORMEL_HAND, "zufall_n": 150, "zufall_v": 4.26,
                 "struktur": STRUKTUREN["schur43_4"], "fall": FAELLE["zufall150"]},
    "Unerfüllbar": {**_BASIS, "formel": FORMEL_HAND, "zufall_n": 150, "zufall_v": 4.26,
                    "struktur": STRUKTUREN["rampen160"], "fall": FAELLE["schubfach5"]},
}
PRESET_HELP = {
    "Handbeispiel": "Fünf Variablen, sieben Klauseln, Zufalls-Seed 20: drei Umdrehungen bis zur Lösung, von Hand nachrechenbar. Darunter die Messreihe n = 300, m/n = 4,0.",
    "Zufall wächst": "Kleine Zufallsformel zum Durchklicken; die Messreihe springt auf n = 600, m/n = 4,0, wo die Messung CDCL im Budget nichts mehr löst.",
    "Struktur": "Schur-Partition k = 4, n = 43: dort braucht probSAT viel mehr Lesezugriffe als CDCL und löst nicht jeden Lauf.",
    "Unerfüllbar": "Schubfach h = 5: CDCL beweist die Unerfüllbarkeit, probSAT bleibt nach dem Budget bei „unbekannt“.",
}

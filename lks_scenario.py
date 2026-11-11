"""Szenario: das Handbeispiel und die Formelfamilien der Demo (Zufalls-3-SAT, Aufträge auf Rampen, Schur, Schubfach).

Alle Zufallsinstanzen laufen über den ganzzahligen SplitMix64 (`lks_rng.py`) und sind aus (Größe, Seed) bestimmt.
"""

import itertools

import lks_instanzen as I
from lks_instanzen import Instanz

# Handbeispiel: fünf Variablen, sieben Klauseln (3-KNF), von Hand nachrechenbar; neun der 32 Belegungen sind Modelle.
HAND_N = 5
HAND_KLAUSELN = [(1, 2, 3), (-1, 2, -4), (-2, 3, 5), (1, -3, 4), (-1, -3, -5), (2, -4, 5), (-2, -4, -5)]
HAND_SEED = 20          # Zufalls-Seed des Handbeispiels: drei Umdrehungen bis zur Lösung

KLEIN_VERHAELTNIS = 4.26          # Klauseln je Variable der kleinen Zufallsformeln in der Schritt-für-Schritt-Ansicht
FORMEL_SEED_START = 8000          # die festen Zufallsformeln der Messreihen haben die Seeds 8000, 8001, ...


def hand_formel() -> Instanz:
    return Instanz(HAND_N, list(HAND_KLAUSELN), {"art": "hand"})


def klauselzahl(n: int, verhaeltnis: float = KLEIN_VERHAELTNIS) -> int:
    return int(round(verhaeltnis * n))


def kleine_formel(n: int, seed: int) -> Instanz:
    """Zufalls-3-SAT mit n Variablen und gerundet 4,26·n Klauseln (Schritt für Schritt)."""
    return I.rand3(n, klauselzahl(n), seed)


def zufall_formel(n: int, verhaeltnis: float, index: int) -> Instanz:
    """Die `index`-te feste Zufallsformel der Messreihen (Seed 8000 + index)."""
    return I.rand3(n, klauselzahl(n, verhaeltnis), FORMEL_SEED_START + index)


def alle_klauseln(k: int = 3) -> Instanz:
    """Alle 2^k Klauseln über k Variablen: unerfüllbar, und jede Belegung verletzt genau eine Klausel."""
    klauseln = [tuple(s * v for s, v in zip(vz, range(1, k + 1))) for vz in itertools.product((1, -1), repeat=k)]
    return Instanz(k, klauseln, {"art": "alle_klauseln", "k": k, "erfuellbar": False})


def rampen(n: int, seed: int) -> Instanz:
    """Aufträge auf drei Rampen, Konfliktgraph mit mittlerem Grad 4,5 (3-Färbung)."""
    return I.rampen_instanz(n, 4.5, seed, 3)


def schubfach(h: int) -> Instanz:
    return I.pigeonhole(h)


def schur(n: int, k: int) -> Instanz:
    return I.schur(n, k)

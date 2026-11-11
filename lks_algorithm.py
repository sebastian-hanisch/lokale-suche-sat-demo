"""probSAT mit Spur: dieselbe Rechnung wie die Kern-Kopie `lks_probsat.py`, dazu Schritt-für-Schritt-Protokoll und Verlauf.

Eine Belegung wird zufällig gewürfelt; solange eine Klausel verletzt ist, wird eine verletzte Klausel gewählt und aus ihr
eine Variable mit Wahrscheinlichkeit proportional zu (ε + break)^(−cb) umgedreht. `break` einer Variablen ist die Zahl der Klauseln,
die nur durch das aktuell wahre Literal dieser Variablen erfüllt sind (sie würden beim Umdrehen verletzt). Es gibt kein Gedächtnis, keinen
Beweis und keine Antwort „unerfüllbar“: ohne Lösung im Flip-Budget heißt die Antwort „unbekannt“.

Zufall nur über SplitMix64 (`lks_rng.py`), nie Python-`random`. Reihenfolge der Ziehungen je Umdrehung: erst die Wahl der Klausel
(`next() % Länge der Liste der verletzten Klauseln`), dann `u = (next() >> 11) / 2^53` für die Wahl der Variablen; beim Start je
Variable ein Münzwurf `next() >> 63`.

Die Liste der verletzten Klauseln ist die Liste der Kern-Kopie (Reihenfolge der Aufnahme, beim Entfernen rückt das letzte Element
auf den frei werdenden Platz). Der Gleichlauf mit `lks_probsat.probsat` (Flips, Lesezugriffe, Modell) ist getestet.

Aufwand: Flips und Literal-Lesezugriffe (Start 3·m für das Füllen der Zähler; je Umdrehung für jedes Literal der Klausel die Vorkommen des
aktuell wahren Literals der Variablen, dazu beim Umdrehen die Vorkommen beider Literale der gewählten Variablen).
"""

import itertools
from dataclasses import dataclass, field

from lks_rng import SplitMix64

ANZAHL_GEWICHTE = 64      # break-Werte ab 63 bekommen das Gewicht von 63 (wie in der Kern-Kopie)


@dataclass
class Schritt:
    """Ein Zustand der Suche und (außer im letzten Eintrag) die darauf folgende Umdrehung."""
    schritt: int                       # Zahl der bisherigen Umdrehungen (Zustand vor der Umdrehung)
    belegung: str                      # "00101": Wert von x1 bis xn
    verletzt: list                     # Nummern (ab 1) der verletzten Klauseln, in der Reihenfolge der Liste
    klausel: int | None = None         # gewählte verletzte Klausel (Nummer ab 1)
    literale: tuple = ()
    brk: list = field(default_factory=list)        # break je Literal der Klausel
    gewichte: list = field(default_factory=list)   # (ε + break)^(−cb)
    summe: float = 0.0
    u: float = 0.0                     # gewürfelte Zahl in [0, 1)
    u_summe: float = 0.0               # u · Summe
    gewaehlt: int | None = None        # Index des gewählten Literals in der Klausel
    variable: int | None = None        # umgedrehte Variable
    lesezugriffe: int = 0              # Zählerstand nach der Umdrehung (beim letzten Eintrag: Endstand)


@dataclass
class Lauf:
    modell: dict | None
    flips: int
    lesezugriffe: int
    verletzt_am_ende: int
    kleinste: int                      # kleinste Zahl verletzter Klauseln, die auf dem Weg vorkam (Start eingeschlossen)
    verlauf: list                      # [(Umdrehung, neues Minimum)] bei jedem neuen Minimum
    schritte: list | None = None       # nur mit spur=True
    zahlen: list | None = None         # nur mit spur=True: Zahl verletzter Klauseln vor jeder Umdrehung und am Ende


def gewicht(b: int, cb: float, eps: float) -> float:
    return (eps + b) ** (-cb)


def waehle_index(gewichte: list, u: float) -> int:
    """Erstes Literal, dessen kumulierte Gewichtssumme ≥ u · Gesamtsumme ist (letztes Literal als Rückfall)."""
    r = u * sum(gewichte)
    k, summe = 0, gewichte[0]
    while r > summe and k < len(gewichte) - 1:
        k += 1
        summe += gewichte[k]
    return k


def probsat_lauf(n, klauseln, max_flips, seed, cb=2.3, eps=0.9, start=None, spur=False) -> Lauf:
    rng = SplitMix64(seed)
    klauseln = [tuple(c) for c in klauseln]
    vorkommen = {l: [] for v in range(1, n + 1) for l in (v, -v)}
    for i, c in enumerate(klauseln):
        for l in c:
            vorkommen[l].append(i)
    wert = [False] + ([rng.coin() for _ in range(n)] if start is None else [bool(start[v]) for v in range(1, n + 1)])
    wahr = [0] * len(klauseln)
    lesen = 0
    for i, c in enumerate(klauseln):
        wahr[i] = sum(1 for l in c if (wert[l] if l > 0 else not wert[-l]))
        lesen += len(c)
    verletzt = [i for i, w in enumerate(wahr) if w == 0]
    pos = {c: j for j, c in enumerate(verletzt)}
    tabelle = [gewicht(b, cb, eps) for b in range(ANZAHL_GEWICHTE)]
    kleinste, verlauf = len(klauseln) + 1, []
    schritte, zahlen = ([], []) if spur else (None, None)

    def entferne(i):
        j = pos.pop(i)
        letzte = verletzt.pop()
        if letzte != i:
            verletzt[j] = letzte
            pos[letzte] = j

    def zustand(flips):
        nonlocal kleinste
        if len(verletzt) < kleinste:
            kleinste = len(verletzt)
            verlauf.append((flips, kleinste))
        if spur:
            zahlen.append(len(verletzt))

    def momentaufnahme(flips) -> Schritt:
        return Schritt(flips, "".join("1" if wert[v] else "0" for v in range(1, n + 1)), [i + 1 for i in verletzt])

    flips = 0
    for flips in range(max_flips):
        zustand(flips)
        if not verletzt:
            if spur:
                s = momentaufnahme(flips)
                s.lesezugriffe = lesen
                schritte.append(s)
            return Lauf({v: wert[v] for v in range(1, n + 1)}, flips, lesen, 0, 0, verlauf, schritte, zahlen)
        s = momentaufnahme(flips) if spur else None
        i = verletzt[rng.below(len(verletzt))]
        c = klauseln[i]
        gewichte, brks = [], []
        for l in c:
            v = abs(l)
            wahres = v if wert[v] else -v               # das Literal der Variablen, das jetzt wahr ist
            b = 0
            for j in vorkommen[wahres]:
                lesen += 1
                if wahr[j] == 1:
                    b += 1
            brks.append(b)
            gewichte.append(tabelle[min(b, ANZAHL_GEWICHTE - 1)])
        u = rng.random()
        k = waehle_index(gewichte, u)
        v = abs(c[k])
        wahres = v if wert[v] else -v
        for j in vorkommen[wahres]:
            lesen += 1
            wahr[j] -= 1
            if wahr[j] == 0:
                pos[j] = len(verletzt)
                verletzt.append(j)
        wert[v] = not wert[v]
        for j in vorkommen[-wahres]:
            lesen += 1
            if wahr[j] == 0:
                entferne(j)
            wahr[j] += 1
        if spur:
            s.klausel, s.literale, s.brk, s.gewichte = i + 1, c, brks, gewichte
            s.summe, s.u, s.u_summe, s.gewaehlt, s.variable, s.lesezugriffe = sum(gewichte), u, u * sum(gewichte), k, v, lesen
            schritte.append(s)
    else:
        flips = max_flips
    zustand(max_flips)
    if spur:
        s = momentaufnahme(max_flips)
        s.lesezugriffe = lesen
        schritte.append(s)
    if not verletzt:
        return Lauf({v: wert[v] for v in range(1, n + 1)}, max_flips, lesen, 0, 0, verlauf, schritte, zahlen)
    return Lauf(None, max_flips, lesen, len(verletzt), kleinste, verlauf, schritte, zahlen)


def alle_modelle(n, klauseln) -> list:
    """Alle Modelle durch Aufzählung der 2^n Belegungen (nur für kleine n), als Bit-Strings „x1 … xn“."""
    modelle = []
    for bits in itertools.product((False, True), repeat=n):
        if all(any(bits[abs(l) - 1] == (l > 0) for l in c) for c in klauseln):
            modelle.append("".join("1" if b else "0" for b in bits))
    return modelle


def wahre_literale(klausel, belegung: str) -> int:
    """Zahl der wahren Literale einer Klausel unter einer Belegung „x1 … xn“ als Bit-String (Neuzählung, unabhängig vom Zähler des Laufs)."""
    return sum(1 for l in klausel if (belegung[abs(l) - 1] == "1") == (l > 0))


def verletzte_je_belegung(n, klauseln) -> list:
    """Zahl verletzter Klauseln je Belegung (alle 2^n, in der Reihenfolge der Aufzählung 00…0 bis 11…1)."""
    out = []
    for bits in itertools.product("01", repeat=n):
        b = "".join(bits)
        out.append(sum(1 for c in klauseln if wahre_literale(c, b) == 0))
    return out


def klausel_text(c) -> str:
    return "(" + " ∨ ".join(("" if l > 0 else "¬") + f"x{abs(l)}" for l in c) + ")"


def literal_text(l) -> str:
    return ("" if l > 0 else "¬") + f"x{abs(l)}"


def zahl_text(x: float, stellen: int = 4) -> str:
    return f"{x:.{stellen}f}".replace(".", ",")

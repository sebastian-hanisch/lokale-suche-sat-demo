# Kopie des Kern-Moduls probsat.py der Linie "SAT und Constraint Programming" (sat-cp-planung/kern/probsat.py, Kern-Version 8caf126238c62c92).
# Nur die Importe der Geschwistermodule sind auf das Präfix lks_ umgestellt; sonst wörtlich (tests/test_kern_kopien.py prüft das).
"""probSAT des Kern-Pakets: stochastische lokale Suche (Balint/Schöning 2012), nur für Erfüllbarkeit.

In jedem Schritt wird eine verletzte Klausel gewählt und aus ihr eine Variable mit Wahrscheinlichkeit proportional zu
(ε + break)^(−cb), wobei break die Zahl der Klauseln ist, die durch das Umdrehen falsch würden (polynomielle Gewichtung für 3-SAT,
cb = 2,3 und ε = 0,9 nach dem Papier). Zufall nur über SplitMix64. Ohne Lösung im Flip-Budget heißt „unbekannt“, nie „unerfüllbar“.
Aufwand: Flips und Literal-Lesezugriffe (Zählung der Klauseln beim Break-Bestimmen und beim Umdrehen).
"""
from dataclasses import dataclass

from lks_rng import SplitMix64


@dataclass
class ProbSatErgebnis:
    modell: dict | None      # erfüllende Belegung oder None
    flips: int
    lesezugriffe: int
    verletzt_am_ende: int    # Zahl verletzter Klauseln bei Abbruch (0 bei Erfolg)


def probsat(n, klauseln, max_flips, seed, cb=2.3, eps=0.9, start=None) -> ProbSatErgebnis:
    rng = SplitMix64(seed)
    klauseln = [tuple(c) for c in klauseln]
    vorkommen = {l: [] for v in range(1, n + 1) for l in (v, -v)}
    for i, c in enumerate(klauseln):
        for l in c:
            vorkommen[l].append(i)
    wert = [False] + ([rng.coin() for _ in range(n)] if start is None else [bool(start[v]) for v in range(1, n + 1)])
    wahr = [0] * len(klauseln)                         # Zahl wahrer Literale je Klausel
    lesen = 0
    for i, c in enumerate(klauseln):
        wahr[i] = sum(1 for l in c if (wert[l] if l > 0 else not wert[-l]))
        lesen += len(c)
    verletzt = [i for i, w in enumerate(wahr) if w == 0]
    pos = {c: j for j, c in enumerate(verletzt)}
    tabelle = [(eps + b) ** (-cb) for b in range(64)]

    def entferne(i):
        j = pos.pop(i)
        letzte = verletzt.pop()
        if letzte != i:
            verletzt[j] = letzte
            pos[letzte] = j

    for flips in range(max_flips):
        if not verletzt:
            return ProbSatErgebnis({v: wert[v] for v in range(1, n + 1)}, flips, lesen, 0)
        i = verletzt[rng.below(len(verletzt))]
        c = klauseln[i]
        gewichte = []
        for l in c:
            v = abs(l)
            wahres = v if wert[v] else -v               # das Literal der Variablen, das jetzt wahr ist
            b = 0
            for j in vorkommen[wahres]:
                lesen += 1
                if wahr[j] == 1:
                    b += 1
            gewichte.append(tabelle[min(b, 63)])
        r = rng.random() * sum(gewichte)
        k, summe = 0, gewichte[0]
        while r > summe and k < len(c) - 1:
            k += 1
            summe += gewichte[k]
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
    if not verletzt:
        return ProbSatErgebnis({v: wert[v] for v in range(1, n + 1)}, max_flips, lesen, 0)
    return ProbSatErgebnis(None, max_flips, lesen, len(verletzt))

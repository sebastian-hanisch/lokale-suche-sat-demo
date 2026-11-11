"""Gegenprobe der Zufallsreihe mit anderen festen Formelmengen (nicht Teil der Tests, Ausgabe in `tools/gegenprobe_ausgabe.txt`).

Aufruf:  python tools/gegenprobe.py

Wie `tools/messungen.py`, nur mit den Formel-Seeds 9000 bis 9011 statt 8000 bis 8011, für n = 150 und n = 300 (m/n = 4,0 / 4,2 / 4,26), drei probSAT-Läufe
je Formel (Zufalls-Seeds 1 bis 3), cb = 2,3, ε = 0,9, 300.000 Umdrehungen, 20.000 Konflikte. Sie zeigt, wie sehr die Zahlen der README (gelöste Läufe und
Formeln, Median der Lesezugriffe) von der Wahl der zwölf Formeln abhängen.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lks_evaluation as E  # noqa: E402
import lks_instanzen as I  # noqa: E402

FORMEL_SEEDS = tuple(range(9000, 9012))


def main():
    zeilen = ["Gegenprobe: Formel-Seeds 9000 bis 9011, 3 probSAT-Läufe je Formel (Zufalls-Seeds 1 bis 3), cb = 2,3, ε = 0,9, 300.000 Umdrehungen, 20.000 Konflikte"]
    for n in (150, 300):
        for verh in (4.0, 4.2, 4.26):
            m = int(round(verh * n))
            formeln = []
            for fs in FORMEL_SEEDS:
                inst = I.rand3(n, m, fs)
                c = E.cdcl_zeile(inst, 20000)
                formeln.append({"seed": fs, "cdcl": c, "probsat": E.probsat_zeilen(inst, (1, 2, 3), 300000, 2.3, 0.9, c["antwort"])})
            k = E.kennzahlen(formeln)
            zeile = (f"n = {n}, m/n = {E.dez(verh)}: CDCL erfüllbar / unerfüllbar / offen {k.c_erf} / {k.c_unerf} / {k.c_unb}; probSAT gelöste Läufe {k.p_gel} von {k.p_laeufe} "
                     f"({k.p_formeln} von {k.n_formeln} Formeln); Median Lesezugriffe CDCL {k.median_cdcl} (aus {k.c_erf}), probSAT {k.median_probsat} (aus {k.p_gel})")
            print(zeile, flush=True)
            zeilen.append(zeile)
    (Path(__file__).with_name("gegenprobe_ausgabe.txt")).write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

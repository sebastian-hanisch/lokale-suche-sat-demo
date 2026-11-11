"""Messskript der vorgerechneten Messreihen: schreibt `lks_messungen.json` im Repo-Wurzelordner.

Aufruf (Test-venv oder Laufzeit-venv, nur numpy-freie Standardbibliothek):  python tools/messungen.py [--schnell]

Gemessen wird in Zählgrößen (Konflikte, Flips, Literal-Lesezugriffe), nie in Sekunden:
  * Zufalls-3-SAT: n = 100, 150, 300, 600, m/n = 4,0 / 4,2 / 4,26, je 12 feste Formeln (SplitMix64-Seeds 8000 bis 8011);
    CDCL (Kern-Kopie) mit 20 000 Konflikten, probSAT (Kern-Kopie) mit 300 000 Flips, drei Läufe je Formel (Zufalls-Seeds 1, 2, 3),
    cb = 2,3, ε = 0,9. Dazu die Robustheitszeile cb = 2,06 (nur n = 300 und 600, dieselben Läufe).
  * Aufträge auf Rampen (3-Färbung, Grad 4,5, n = 160 Aufträge, zehn feste Graphen mit den Seeds 500 bis 509): CDCL einmal, probSAT 5 Läufe je Graph.
  * Schur k = 4, n = 43 und Schur k = 3, n = 13: CDCL einmal, probSAT 20 Läufe (Zufalls-Seeds 1 bis 20).
Jedes von einem Verfahren gemeldete Modell wird gegen die Klauseln geprüft; ein probSAT-Modell bei einer von CDCL als unerfüllbar
bewiesenen Formel wäre ein Fehler und bricht den Lauf ab.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lks_instanzen as I  # noqa: E402
from lks_cdcl import solve  # noqa: E402
from lks_probsat import probsat  # noqa: E402

ZUFALL_N = (100, 150, 300, 600)
VERHAELTNISSE = (4.0, 4.2, 4.26)
FORMEL_SEEDS = tuple(range(8000, 8012))
PROBSAT_SEEDS = (1, 2, 3)
CDCL_BUDGET = 20000
FLIP_BUDGET = 300000
CB, EPS, CB_ALT = 2.3, 0.9, 2.06
RAMPEN_SEEDS = tuple(range(500, 510))
RAMPEN_SEEDS_PROBSAT = (1, 2, 3, 4, 5)
SCHUR_SEEDS = tuple(range(1, 21))


def cdcl_zeile(inst) -> dict:
    erg = solve(inst.n, inst.klauseln, conflict_budget=CDCL_BUDGET)
    if erg.antwort is True:
        assert I.pruefe_modell(inst.klauseln, erg.modell), "CDCL-Modell verletzt eine Klausel"
    return {"antwort": erg.antwort, "konflikte": erg.stat["konflikte"], "lesezugriffe": erg.stat["lesezugriffe"]}


def probsat_zeilen(inst, seeds, cb, eps, cdcl_antwort) -> list:
    zeilen = []
    for seed in seeds:
        p = probsat(inst.n, inst.klauseln, FLIP_BUDGET, seed, cb=cb, eps=eps)
        if p.modell is not None:
            assert I.pruefe_modell(inst.klauseln, p.modell), "probSAT-Modell verletzt eine Klausel"
            assert cdcl_antwort is not False, "probSAT-Modell bei bewiesen unerfüllbarer Formel"
        zeilen.append({"seed": seed, "geloest": p.modell is not None, "flips": p.flips, "lesezugriffe": p.lesezugriffe,
                       "verletzt_am_ende": p.verletzt_am_ende})
    return zeilen


def messe_zufall(schnell: bool) -> dict:
    out = {}
    for n in ZUFALL_N:
        for verh in VERHAELTNISSE:
            m = int(round(verh * n))
            t0 = time.time()
            formeln = []
            seeds = FORMEL_SEEDS[:3] if schnell else FORMEL_SEEDS
            for fs in seeds:
                inst = I.rand3(n, m, fs)
                c = cdcl_zeile(inst)
                p = probsat_zeilen(inst, PROBSAT_SEEDS, CB, EPS, c["antwort"])
                z = {"seed": fs, "cdcl": c, "probsat": p}
                if n >= 300:
                    z["probsat_cb_alt"] = probsat_zeilen(inst, PROBSAT_SEEDS, CB_ALT, EPS, c["antwort"])
                formeln.append(z)
            out[f"n{n}_v{verh}"] = {"n": n, "verhaeltnis": verh, "m": m, "formeln": formeln}
            print(f"zufall n={n} m/n={verh}: {sum(f['cdcl']['antwort'] is True for f in formeln)} erfüllbar, "
                  f"{sum(f['cdcl']['antwort'] is False for f in formeln)} unerfüllbar, {sum(f['cdcl']['antwort'] is None for f in formeln)} Budget | "
                  f"probSAT {sum(r['geloest'] for f in formeln for r in f['probsat'])}/{len(formeln) * len(PROBSAT_SEEDS)} Läufe "
                  f"({round(time.time() - t0)} s)", flush=True)
    return out


def messe_struktur(schnell: bool) -> dict:
    out = {}
    rampen = []
    for gs in (RAMPEN_SEEDS[:2] if schnell else RAMPEN_SEEDS):
        inst = I.rampen_instanz(160, 4.5, gs, 3)
        c = cdcl_zeile(inst)
        rampen.append({"seed": gs, "cdcl": c, "probsat": probsat_zeilen(inst, RAMPEN_SEEDS_PROBSAT, CB, EPS, c["antwort"])})
    out["rampen160"] = {"label": "Aufträge auf Rampen (3-Färbung, n = 160 Aufträge, Grad 4,5)", "instanzen": rampen}
    print("rampen160:", [(r["cdcl"]["antwort"], sum(x["geloest"] for x in r["probsat"])) for r in rampen], flush=True)
    for schluessel, (n, k, label) in {"schur43_4": (43, 4, "Schur k = 4, n = 43"), "schur13_3": (13, 3, "Schur k = 3, n = 13")}.items():
        inst = I.schur(n, k)
        c = cdcl_zeile(inst)
        out[schluessel] = {"label": label, "instanzen": [{"seed": 0, "cdcl": c, "probsat": probsat_zeilen(inst, SCHUR_SEEDS, CB, EPS, c["antwort"])}]}
        print(schluessel, c["antwort"], sum(x["geloest"] for x in out[schluessel]["instanzen"][0]["probsat"]), "von", len(SCHUR_SEEDS), flush=True)
    out["rampen160"]["label"] = "Aufträge auf Rampen (3-Färbung, n = 160 Aufträge, Grad 4,5)"
    return out


def main():
    schnell = "--schnell" in sys.argv
    t0 = time.time()
    daten = {
        "meta": {"skript": "tools/messungen.py", "cdcl_budget": CDCL_BUDGET, "flip_budget": FLIP_BUDGET, "cb": CB, "eps": EPS, "cb_alt": CB_ALT,
                 "probsat_seeds": list(PROBSAT_SEEDS), "formel_seeds": list(FORMEL_SEEDS), "rampen_seeds": list(RAMPEN_SEEDS),
                 "kern": {"cdcl": "832b2c10dfdea62d", "probsat": "8caf126238c62c92", "rng": "5d5d8f45d0e1eddf", "instanzen": "6795de796b66fff8"},
                 "einheit": "Literal-Lesezugriffe (CDCL: gelesene Literale der Propagation; probSAT: Break-Zählung und Umdrehen), nie Sekunden"},
        "struktur": messe_struktur(schnell),
        "zufall": messe_zufall(schnell),
    }
    ziel = ROOT / ("lks_messungen_schnell.json" if schnell else "lks_messungen.json")
    ziel.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("geschrieben:", ziel.name, f"({round(time.time() - t0)} s Rechenzeit, nur Protokoll, kein Befund)")


if __name__ == "__main__":
    main()

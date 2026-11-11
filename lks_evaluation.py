"""Messreihen, Kennzahlen und Verdikte.

Gemessen werden Konflikte, Umdrehungen (Flips) und Literal-Lesezugriffe, nie Sekunden. Die vorgerechneten Messreihen stehen in
`lks_messungen.json` (Messskript `tools/messungen.py`); die Live-Messreihen der App rechnen mit denselben Kern-Kopien
(`lks_cdcl.solve`, `lks_probsat.probsat`). Alle Verdikte sind reine Funktionen `verdict_*(...) -> (Art, Text)`: jede Zahl im Text stammt
aus den übergebenen Kennzahlen.

Vergleichseinheit sind Literal-Lesezugriffe. Sie zählen verschiedene Operationen (CDCL: gelesene Literale der Propagation und der
Konfliktanalyse; probSAT: Break-Zählung und Umdrehen) und sind nur der Größenordnung nach vergleichbar. Ein Median der Lesezugriffe steht
nur über die **gelösten** Läufe eines Verfahrens; löst ein Verfahren wenig, stammt sein Median aus den leichtesten Fällen und ist eine
untere Schranke seiner Kosten.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import median

import lks_algorithm as A
import lks_constants as C
import lks_scenario as S
from lks_cdcl import solve
from lks_instanzen import pruefe_modell
from lks_probsat import probsat

MESSDATEI = Path(__file__).with_name("lks_messungen.json")
MIN_WERTE = 3        # unter so vielen gelösten Fällen ist ein Median nur eine untere Schranke (Ampel gelb)


# --------------------------------------------------------------------------------------------------------------------------------- Zahlen
def zahl(x: float) -> str:
    """Deutsche Schreibweise: Tausenderpunkt; ganze Werte ohne, sonst mit einer Nachkommastelle und Dezimalkomma."""
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}".replace(",", ".")
    return f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def dez(x: float) -> str:
    """Parameter mit Dezimalkomma ohne überflüssige Nullen (2,3; 0,9; 4,26; 4,0)."""
    s = f"{x:g}".replace(".", ",")
    return s if "," in s else s + ",0"


def faktor_text(f: float) -> str:
    """Verhältnis ≥ 1 als „54-mal“ (ab 10 ganzzahlig) oder „3,4-mal“."""
    return f"{int(round(f))}-mal" if f >= 10 else f"{f:.1f}".replace(".", ",") + "-mal"


def laeufe_text(k: int, dativ: bool = False) -> str:
    """„1 Lauf“, „5 Läufe“; mit `dativ` „5 Läufen“ (nach „von“, „in“)."""
    return f"{k} Lauf" if k == 1 else f"{k} Läufen" if dativ else f"{k} Läufe"


# --------------------------------------------------------------------------------------------------------------------------------- Messdaten
@lru_cache(maxsize=1)
def lade_messungen() -> dict:
    """Die vorgerechneten Messreihen (leer, wenn die Datei fehlt)."""
    if not MESSDATEI.exists():
        return {}
    return json.loads(MESSDATEI.read_text(encoding="utf-8"))


def zellen_zufall() -> dict:
    return lade_messungen().get("zufall", {})


def zelle_zufall(n: int, verhaeltnis: float) -> dict | None:
    return zellen_zufall().get(f"n{n}_v{verhaeltnis}")


def zelle_struktur(schluessel: str) -> dict | None:
    return lade_messungen().get("struktur", {}).get(schluessel)


def cdcl_zeile(inst, budget: int) -> dict:
    erg = solve(inst.n, inst.klauseln, conflict_budget=budget)
    if erg.antwort is True:
        assert pruefe_modell(inst.klauseln, erg.modell), "CDCL-Modell verletzt eine Klausel"
    return {"antwort": erg.antwort, "konflikte": erg.stat["konflikte"], "lesezugriffe": erg.stat["lesezugriffe"]}


def probsat_zeilen(inst, seeds, flips: int, cb: float, eps: float, cdcl_antwort=None) -> list:
    zeilen = []
    for seed in seeds:
        p = probsat(inst.n, inst.klauseln, flips, seed, cb=cb, eps=eps)
        if p.modell is not None:
            assert pruefe_modell(inst.klauseln, p.modell), "probSAT-Modell verletzt eine Klausel"
            assert cdcl_antwort is not False, "probSAT-Modell bei bewiesen unerfüllbarer Formel"
        zeilen.append({"seed": seed, "geloest": p.modell is not None, "flips": p.flips, "lesezugriffe": p.lesezugriffe,
                       "verletzt_am_ende": p.verletzt_am_ende})
    return zeilen


def messe_zufall_live(n: int, verhaeltnis: float, anzahl: int, cdcl_budget: int, flips: int, cb: float, eps: float, seed: int) -> dict:
    """Live-Messreihe auf den ersten `anzahl` festen Formeln der Familie; ein probSAT-Lauf je Formel mit dem Zufalls-Seed der Seitenleiste."""
    formeln = []
    for index in range(anzahl):
        inst = S.zufall_formel(n, verhaeltnis, index)
        c = cdcl_zeile(inst, cdcl_budget)
        formeln.append({"seed": S.FORMEL_SEED_START + index, "cdcl": c, "probsat": probsat_zeilen(inst, (seed,), flips, cb, eps, c["antwort"])})
    return {"n": n, "verhaeltnis": verhaeltnis, "m": S.klauselzahl(n, verhaeltnis), "formeln": formeln}


def messe_struktur_live(familie: str, groesse: int, anzahl: int, cdcl_budget: int, flips: int, cb: float, eps: float, seed: int) -> dict:
    """Live-Messreihe einer Strukturaufgabe. Rampen: die ersten `anzahl` festen Graphen mit je drei probSAT-Läufen (Zufalls-Seeds seed bis seed + 2);
    Schur: eine Instanz, `anzahl` probSAT-Läufe (Zufalls-Seeds seed, seed + 1, …)."""
    if familie.startswith("rampen"):
        instanzen = []
        for gs in range(C.RAMPEN_SEED_START, C.RAMPEN_SEED_START + anzahl):
            inst = S.rampen(groesse, gs)
            c = cdcl_zeile(inst, cdcl_budget)
            instanzen.append({"seed": gs, "cdcl": c, "probsat": probsat_zeilen(inst, range(seed, seed + 3), flips, cb, eps, c["antwort"])})
        return {"label": f"Aufträge auf Rampen (3-Färbung, n = {groesse} Aufträge, Grad 4,5)", "instanzen": instanzen}
    n, k = C.SCHUR_INSTANZEN[familie]
    inst = S.schur(n, k)
    c = cdcl_zeile(inst, cdcl_budget)
    return {"label": f"Schur k = {k}, n = {n}",
            "instanzen": [{"seed": 0, "cdcl": c, "probsat": probsat_zeilen(inst, range(seed, seed + anzahl), flips, cb, eps, c["antwort"])}]}


# ------------------------------------------------------------------------------------------------------------------------------ Einheiten der Live-Messreihen
# Jede Einheit ist ein Stück der Messreihe oben, einzeln rechenbar (Zwischenspeicher und Fortschrittsanzeige der App, lks_live.py). `messe_zufall_live` und `messe_struktur_live`
# bleiben unverändert; die Tests prüfen, dass die aus Einheiten zusammengesetzte Reihe bitgleich dasselbe liefert.

def zufall_einheit(n: int, verhaeltnis: float, index: int, cdcl_budget: int, flips: int, cb: float, eps: float, seed: int) -> dict:
    """Eine feste Formel der Live-Messreihe auf Zufallsformeln: CDCL und ein probSAT-Lauf (ein Element von `messe_zufall_live(...)["formeln"]`)."""
    inst = S.zufall_formel(n, verhaeltnis, index)
    c = cdcl_zeile(inst, cdcl_budget)
    return {"seed": S.FORMEL_SEED_START + index, "cdcl": c, "probsat": probsat_zeilen(inst, (seed,), flips, cb, eps, c["antwort"])}


def zufall_aufbauen(n: int, verhaeltnis: float, formeln: list) -> dict:
    """Setzt die Live-Messreihe aus den Einheiten zusammen (wie `messe_zufall_live`)."""
    return {"n": n, "verhaeltnis": verhaeltnis, "m": S.klauselzahl(n, verhaeltnis), "formeln": list(formeln)}


def rampen_einheit(groesse: int, gs: int, cdcl_budget: int, flips: int, cb: float, eps: float, seed: int) -> dict:
    """Ein fester Konfliktgraph (Zufalls-Seed `gs`) der Live-Messreihe auf Rampen: CDCL und drei probSAT-Läufe."""
    inst = S.rampen(groesse, gs)
    c = cdcl_zeile(inst, cdcl_budget)
    return {"seed": gs, "cdcl": c, "probsat": probsat_zeilen(inst, range(seed, seed + 3), flips, cb, eps, c["antwort"])}


def schur_cdcl_einheit(familie: str, cdcl_budget: int) -> dict:
    """Der CDCL-Lauf der Schur-Instanz einer Live-Messreihe."""
    n, k = C.SCHUR_INSTANZEN[familie]
    return cdcl_zeile(S.schur(n, k), cdcl_budget)


def schur_probsat_einheit(familie: str, cdcl_antwort, seed: int, flips: int, cb: float, eps: float) -> dict:
    """Ein probSAT-Lauf auf der Schur-Instanz (eine Zeile von `probsat_zeilen`); `cdcl_antwort` dient nur der Gegenprobe."""
    n, k = C.SCHUR_INSTANZEN[familie]
    return probsat_zeilen(S.schur(n, k), (seed,), flips, cb, eps, cdcl_antwort)[0]


def struktur_aufbauen(familie: str, groesse: int, einheiten: list) -> dict:
    """Setzt die Live-Messreihe einer Strukturaufgabe aus den Einheiten zusammen (wie `messe_struktur_live`). Rampen: `einheiten` = Elemente aus `rampen_einheit`;
    Schur: `einheiten` = [CDCL-Zeile, probSAT-Zeile, probSAT-Zeile, …]."""
    if familie.startswith("rampen"):
        return {"label": f"Aufträge auf Rampen (3-Färbung, n = {groesse} Aufträge, Grad 4,5)", "instanzen": list(einheiten)}
    n, k = C.SCHUR_INSTANZEN[familie]
    return {"label": f"Schur k = {k}, n = {n}", "instanzen": [{"seed": 0, "cdcl": einheiten[0], "probsat": list(einheiten[1:])}]}


# --------------------------------------------------------------------------------------------------------------------------------- Kennzahlen
@dataclass(frozen=True)
class Zelle:
    """Kennzahlen einer Messzelle (eine Zeile der Tabelle): Formeln bzw. Instanzen mit je einem CDCL-Lauf und mehreren probSAT-Läufen."""
    n_formeln: int
    c_erf: int
    c_unerf: int
    c_unb: int
    p_laeufe: int
    p_gel: int                    # gelöste probSAT-Läufe
    p_formeln: int                # Formeln, die probSAT in mindestens einem Lauf löst
    p_gemischt: int               # Formeln, bei denen nur ein Teil der Läufe gelang (gleiche Formel, anderer Zufalls-Seed)
    p_laeufe_erf: int             # Läufe auf Formeln, die CDCL als erfüllbar fand
    p_gel_erf: int                # davon gelöst
    p_laeufe_unerf: int           # Läufe auf Formeln, die CDCL als unerfüllbar bewiesen hat
    p_gel_unerf: int              # probSAT-Modelle bei von CDCL bewiesen unerfüllbaren Formeln (muss 0 sein)
    median_cdcl: float | None     # Median der Lesezugriffe über die von CDCL gefundenen erfüllbaren Formeln
    median_probsat: float | None  # Median der Lesezugriffe über die gelösten probSAT-Läufe

    @property
    def faktor(self) -> float | None:
        """Median CDCL / Median probSAT (nur wenn beide vorhanden)."""
        if self.median_cdcl is None or self.median_probsat is None or self.median_probsat == 0:
            return None
        return self.median_cdcl / self.median_probsat

    @property
    def untere_schranke(self) -> bool:
        """Mindestens ein Median stammt aus weniger als MIN_WERTE gelösten Fällen (oder fehlt)."""
        return self.c_erf < MIN_WERTE or self.p_gel < MIN_WERTE


def kennzahlen(zeilen: list, probsat_schluessel: str = "probsat") -> Zelle:
    """Aus den Zeilen einer Zelle (Formeln bzw. Instanzen, jede mit `cdcl` und einer Liste von probSAT-Läufen) die Kennzahlen."""
    c = [z["cdcl"]["antwort"] for z in zeilen]
    laeufe = [(z["cdcl"]["antwort"], r) for z in zeilen for r in z[probsat_schluessel]]
    cw = [z["cdcl"]["lesezugriffe"] for z in zeilen if z["cdcl"]["antwort"] is True]
    pw = [r["lesezugriffe"] for _, r in laeufe if r["geloest"]]
    teil = [sum(r["geloest"] for r in z[probsat_schluessel]) for z in zeilen]
    return Zelle(
        n_formeln=len(zeilen), c_erf=sum(a is True for a in c), c_unerf=sum(a is False for a in c), c_unb=sum(a is None for a in c),
        p_laeufe=len(laeufe), p_gel=len(pw), p_formeln=sum(t > 0 for t in teil),
        p_gemischt=sum(0 < t < len(z[probsat_schluessel]) for t, z in zip(teil, zeilen)),
        p_laeufe_erf=sum(a is True for a, _ in laeufe), p_gel_erf=sum(a is True and r["geloest"] for a, r in laeufe),
        p_laeufe_unerf=sum(a is False for a, _ in laeufe), p_gel_unerf=sum(a is False and r["geloest"] for a, r in laeufe),
        median_cdcl=float(median(cw)) if cw else None, median_probsat=float(median(pw)) if pw else None)


def verhaeltnis_text(z: Zelle) -> str:
    """Wer im Median der Gelösten mehr Lesezugriffe braucht (Spalte der Tabellen); ein Median aus weniger als drei Werten macht das Verhältnis zum Richtwert."""
    f = z.faktor
    if f is None:
        return "–"
    t = f"CDCL {faktor_text(f)} mehr" if f >= 1 else f"probSAT {faktor_text(1 / f)} mehr"
    return t + (" (Richtwert)" if z.untere_schranke else "")


def zeilen_von(zelle: dict) -> list:
    return zelle["formeln"] if "formeln" in zelle else zelle["instanzen"]


# --------------------------------------------------------------------------------------------------------------------------------- Verdikte
def _median_satz(z: Zelle, einheit: tuple = ("Formel", "Formeln")) -> str:
    """Satz über die Mediane der Lesezugriffe mit Basis und Hinweis auf die untere Schranke."""
    if z.median_cdcl is None and z.median_probsat is None:
        return "Keines der Verfahren löst einen Fall; es gibt keinen Median der Lesezugriffe."
    if z.median_cdcl is None:
        return (f"Lesezugriffe im Median der gelösten Läufe: probSAT {zahl(z.median_probsat)} (aus {laeufe_text(z.p_gel, True)}); CDCL löst keine erfüllbare {einheit[0]}, "
                f"es gibt keinen CDCL-Median und kein Verhältnis.")
    if z.median_probsat is None:
        return (f"Lesezugriffe im Median der gelösten Fälle: CDCL {zahl(z.median_cdcl)} (aus {z.c_erf} {einheit[0] if z.c_erf == 1 else einheit[1]}); probSAT löst keinen Lauf, "
                f"es gibt keinen probSAT-Median und kein Verhältnis.")
    f = z.faktor
    if f >= 1:
        wer = f"CDCL braucht im Median {faktor_text(f)} so viele Lesezugriffe wie probSAT"
    else:
        wer = f"probSAT braucht im Median {faktor_text(1 / f)} so viele Lesezugriffe wie CDCL"
    satz = (f"Lesezugriffe im Median der Gelösten: CDCL {zahl(z.median_cdcl)} (aus {z.c_erf} {einheit[0] if z.c_erf == 1 else einheit[1]}), probSAT {zahl(z.median_probsat)} "
            f"(aus {laeufe_text(z.p_gel, True)}); {wer}.")
    if z.untere_schranke:
        wenig = []
        if z.c_erf < MIN_WERTE:
            wenig.append(f"CDCL ({z.c_erf} {'Wert' if z.c_erf == 1 else 'Werte'})")
        if z.p_gel < MIN_WERTE:
            wenig.append(f"probSAT ({z.p_gel} {'Wert' if z.p_gel == 1 else 'Werte'})")
        satz += (f" Der Median von {' und '.join(wenig)} stammt aus weniger als {MIN_WERTE} gelösten Fällen, den leichtesten des Verfahrens; "
                 f"seine wahren Kosten sind mindestens so hoch (untere Schranke).")
    return satz


def verdict_zufall(label: str, z: Zelle, cdcl_budget: int, flip_budget: int) -> tuple:
    """Zufalls-3-SAT-Zelle: wer löst wie viel, mit welchen Lesezugriffen (Ampel gelb bei weniger als 3 Werten eines Medians)."""
    satz = (f"{label}: probSAT löst {z.p_gel} von {laeufe_text(z.p_laeufe, True)} ({z.p_formeln} von {z.n_formeln} Formeln in mindestens einem Lauf, "
            f"Budget {zahl(flip_budget)} Umdrehungen). CDCL entscheidet {z.c_erf + z.c_unerf} von {z.n_formeln} Formeln "
            f"({z.c_erf} erfüllbar, {z.c_unerf} unerfüllbar), {z.c_unb} bleiben am Budget von {zahl(cdcl_budget)} Konflikten offen. ")
    satz += _median_satz(z)
    if z.p_gemischt:
        satz += f" Bei {z.p_gemischt} Formeln gelang nur ein Teil der probSAT-Läufe: dieselbe Formel, anderer Zufalls-Seed."
    if z.c_unerf:
        satz += f" {z.c_unerf} Formeln beweist nur CDCL als unerfüllbar; probSAT findet dort kein Modell und kann es nicht beweisen."
    return ("warning" if z.untere_schranke else "success"), satz


def verdict_struktur(label: str, z: Zelle, cdcl_budget: int, flip_budget: int) -> tuple:
    """Strukturaufgabe: CDCL gegen probSAT; probSAT-Läufe nur auf den von CDCL als erfüllbar gefundenen Instanzen gezählt."""
    satz = (f"{label}: CDCL löst {z.c_erf} von {z.n_formeln} Instanzen ({z.c_unerf} unerfüllbar, {z.c_unb} am Budget von {zahl(cdcl_budget)} Konflikten offen). "
            f"probSAT löst auf den {z.c_erf} erfüllbaren Instanzen {z.p_gel_erf} von {laeufe_text(z.p_laeufe_erf, True)} (Budget {zahl(flip_budget)} Umdrehungen). ")
    satz += _median_satz(z, ("Instanz", "Instanzen"))
    if z.faktor is not None and z.faktor < 1 and z.p_gel < z.p_laeufe_erf:
        satz += " probSAT-Läufe ohne Lösung fehlen im Median; das Verhältnis ist deshalb eine untere Schranke des Vorsprungs von CDCL."
    return ("warning" if z.untere_schranke else "success"), satz


def verdict_zufall_wachstum(zellen: dict) -> tuple:
    """Über die Messzellen einer Verhältnis-Spalte (n → Zelle): wie sich gelöste Läufe beider Verfahren mit n ändern."""
    teile = []
    for n, (z, _) in sorted(zellen.items()):
        teile.append(f"n = {n}: probSAT {z.p_gel} von {z.p_laeufe} Läufen, CDCL {z.c_erf + z.c_unerf} von {z.n_formeln} Formeln entschieden")
    return "info", "; ".join(teile) + "."


def verdict_unerfuellbar(fall: str, antwort_cdcl, konflikte_cdcl: int, flips: int, kleinste: int, geloest: bool, modell_ok: bool | None = None) -> tuple:
    """Ein Fall des Experiments „Unerfüllbar und Aufgeben“: was CDCL sagt, was probSAT nach dem Budget sagt."""
    if antwort_cdcl is False:
        c = f"CDCL antwortet nach {zahl(konflikte_cdcl)} Konflikten „unerfüllbar“"
    elif antwort_cdcl is True:
        c = f"CDCL findet nach {zahl(konflikte_cdcl)} Konflikten ein Modell"
    else:
        c = f"CDCL bleibt nach {zahl(konflikte_cdcl)} Konflikten am Budget: „unbekannt“"
    if geloest:
        p = f"probSAT findet nach {zahl(flips)} Umdrehungen ein Modell" + (" (gegen die Klauseln geprüft)" if modell_ok else "")
        return "info", f"{fall}: {c}. {p}."
    p = (f"probSAT hat nach {zahl(flips)} Umdrehungen kein Modell; die kleinste Zahl verletzter Klauseln auf dem Weg war {kleinste}. Die Antwort ist „unbekannt“, "
         f"nicht „unerfüllbar“")
    kind = "warning" if antwort_cdcl is not True else "info"
    return kind, f"{fall}: {c}. {p}."


def verdict_anteil_unerfuellbar(label: str, z: Zelle, flip_budget: int) -> tuple:
    """Zufallsformeln im Übergangsbereich: wie viele Formeln nur CDCL als unerfüllbar erkennt und was probSAT dort und bei den erfüllbaren leistet."""
    satz = (f"{label}: CDCL beweist {z.c_unerf} von {z.n_formeln} Formeln als unerfüllbar und findet bei {z.c_erf} ein Modell ({z.c_unb} offen). "
            f"probSAT findet bei den unerfüllbaren Formeln in {z.p_gel_unerf} von {laeufe_text(z.p_laeufe_unerf, True)} ein Modell (es gibt keins) und beweist nichts; "
            f"nach {zahl(flip_budget)} Umdrehungen lautet seine Antwort dort „unbekannt“. Bei den {z.c_erf} erfüllbaren Formeln löst es {z.p_gel_erf} von {laeufe_text(z.p_laeufe_erf, True)}.")
    return ("warning" if z.c_unerf else "info"), satz


def schritt_text(s: A.Schritt, n: int, loesung: bool) -> str:
    """Beschreibung eines Zustands der Schritt-für-Schritt-Ansicht (reine Funktion von Schritt und Ausgang)."""
    verletzt = ", ".join(f"C{i}" for i in s.verletzt) if s.verletzt else "keine"
    if s.klausel is None:
        if not s.verletzt:
            return f"Nach {s.schritt} Umdrehungen: Belegung {s.belegung}, keine Klausel verletzt. Das ist ein Modell."
        return f"Nach {s.schritt} Umdrehungen (Budget erreicht): Belegung {s.belegung}, verletzt: {verletzt}. Ohne Modell lautet die Antwort „unbekannt“."
    teile = [f"Vor der Umdrehung {s.schritt + 1}: Belegung {s.belegung}, verletzt: {verletzt}.",
             f"Gewählt wird die Klausel C{s.klausel} {A.klausel_text(s.literale)} (Platz {s.verletzt.index(s.klausel) + 1} von {len(s.verletzt)} in der Liste der verletzten Klauseln).",
             f"Mit u = {A.zahl_text(s.u, 4)} ergibt sich u · Summe = {A.zahl_text(s.u_summe, 4)} bei der Gesamtsumme {A.zahl_text(s.summe, 4)}; "
             f"das {s.gewaehlt + 1}. Literal ({A.literal_text(s.literale[s.gewaehlt])}) überschreitet diese Marke zuerst. x{s.variable} wird umgedreht."]
    return " ".join(teile)


def verdict_misserfolg(laeufe: list) -> tuple:
    """Eine erfüllbare Formel mit mehreren probSAT-Läufen: `laeufe` = [(Zufalls-Seed, gelöst, Umdrehungen, kleinste verletzte Zahl)]."""
    gel = [x for x in laeufe if x[1]]
    fehl = [x for x in laeufe if not x[1]]
    if gel and fehl:
        g, f = gel[0], fehl[0]
        return "warning", (f"Dieselbe Formel ist erfüllbar (Zufalls-Seed {g[0]}: Modell nach {zahl(g[2])} Umdrehungen, gegen die Klauseln geprüft), und doch endet der Lauf mit "
                           f"Zufalls-Seed {f[0]} nach {zahl(f[2])} Umdrehungen ohne Modell (kleinste Zahl verletzter Klauseln {f[3]}). "
                           f"Ein Lauf ohne Lösung beweist nicht, dass es keine gibt.")
    if gel:
        return "info", f"Alle {len(gel)} Läufe finden ein Modell; mit diesen Einstellungen zeigt die Formel keinen Misserfolg."
    return "warning", (f"Kein Lauf findet ein Modell (kleinste Zahl verletzter Klauseln: {min(x[3] for x in laeufe)}). Ob die Formel erfüllbar ist, "
                       f"sagt dieses Ergebnis nicht.")


def ersten_gemischten(zellenfolge) -> dict | None:
    """Erste Formel aus den Messzellen (Zellen mit n ≥ 300 zuerst), bei der nur ein Teil der probSAT-Läufe gelang: {n, verhaeltnis, seed, geloest, nicht}."""
    for z in zellenfolge:
        for f in z["formeln"]:
            gel = [r["seed"] for r in f["probsat"] if r["geloest"]]
            nicht = [r["seed"] for r in f["probsat"] if not r["geloest"]]
            if gel and nicht:
                return {"n": z["n"], "verhaeltnis": z["verhaeltnis"], "formel_seed": f["seed"], "geloest": gel, "nicht": nicht}
    return None


def kurve_punkte(lauf: A.Lauf, budget: int) -> tuple:
    """Verlauf als Treppenkurve: x = Umdrehungen, y = kleinste Zahl verletzter Klauseln; letzter Punkt am Ende bzw. am Budget."""
    xs = [f for f, _ in lauf.verlauf]
    ys = [m for _, m in lauf.verlauf]
    xs.append(lauf.flips if lauf.modell is not None else budget)
    ys.append(ys[-1] if ys else lauf.kleinste)
    return xs, ys


def messe_fall(inst, cdcl_budget: int, flips: int, cb: float, eps: float, seed: int) -> dict:
    """Ein Fall des Experiments 4: CDCL und ein probSAT-Lauf mit Verlauf."""
    erg = solve(inst.n, inst.klauseln, conflict_budget=cdcl_budget)
    lauf = A.probsat_lauf(inst.n, inst.klauseln, flips, seed, cb=cb, eps=eps)
    ok = pruefe_modell(inst.klauseln, lauf.modell) if lauf.modell is not None else None
    return {"cdcl_antwort": erg.antwort, "cdcl_konflikte": erg.stat["konflikte"], "lauf": lauf, "modell_ok": ok, "m": len(inst.klauseln), "n": inst.n}

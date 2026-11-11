"""Lokale Suche gegen CDCL - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zwei Verfahren für dieselbe Aufgabe, eine erfüllende Belegung zu finden: CDCL lernt aus Konflikten und kann „unerfüllbar“ beweisen,
probSAT (stochastische lokale Suche) dreht immer wieder eine Variable einer verletzten Klausel um, hat kein Gedächtnis und keinen
Beweis. Die Demo zeigt probSAT Schritt für Schritt und zählt in Umdrehungen, Konflikten und Literal-Lesezugriffen (nie in Sekunden),
wo welches Verfahren mehr leistet. Die großen Messreihen sind vorgerechnet (nicht live).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import lks_algorithm as A
import lks_constants as C
import lks_evaluation as E
import lks_live as L
import lks_presets as P
import lks_scenario as S
import lks_visualization as V
from lks_layout import dunkles_design, kopf_css
from lks_presets import (
    init_session_state_defaults,
    load_permalink_settings,
    randomize_klein_seed,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Lokale Suche gegen CDCL – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _schrittlauf(formel, klein_n, klein_seed, seed, flips, cb, eps):
    inst = S.hand_formel() if formel == C.FORMEL_HAND else S.kleine_formel(klein_n, klein_seed)
    lauf = A.probsat_lauf(inst.n, inst.klauseln, min(flips, C.MAX_SCHRITT_FLIPS), seed, cb=cb, eps=eps, spur=True)
    return {"n": inst.n, "klauseln": [tuple(k) for k in inst.klauseln], "lauf": lauf, "modelle": A.alle_modelle(inst.n, inst.klauseln)}


@st.cache_data(show_spinner=False)
def _fall(fall, konflikte, flips, cb, eps, seed):
    """Ein Fall des Experiments 4 (Schubfach, Färbung, Handbeispiel) oder die zwei Läufe der erfüllbaren, aber nicht gefundenen Formel."""
    if fall == "hand8":
        inst = S.alle_klauseln(3)
        return {"inst_n": inst.n, "klauseln": inst.klauseln, "daten": E.messe_fall(inst, konflikte, C.HAND8_FLIPS, cb, eps, seed),
                "belegungen": A.verletzte_je_belegung(inst.n, inst.klauseln)}
    if fall == "schubfach5":
        inst = S.schubfach(5)
    else:
        inst = S.rampen(160, C.RAMPEN_UNSAT_SEED)
    return {"inst_n": inst.n, "klauseln": inst.klauseln, "daten": E.messe_fall(inst, konflikte, flips, cb, eps, seed)}


@st.cache_data(show_spinner=False)
def _misserfolg(n, verhaeltnis, formel_seed, seeds, flips, cb, eps):
    inst = S.zufall_formel(n, verhaeltnis, formel_seed - S.FORMEL_SEED_START)
    laeufe = []
    for sd in seeds:
        lauf = A.probsat_lauf(inst.n, inst.klauseln, flips, sd, cb=cb, eps=eps)
        laeufe.append((sd, lauf))
    return laeufe


def _klausel_zeile(i, k):
    return f"C{i + 1} {A.klausel_text(k)}"


# --- Kopf, Einleitung ----------------------------------------------------------------------------------------------------------------------

st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🎲 Lokale Suche gegen CDCL")
st.markdown(
    """
Zwei Wege zur selben Antwort: **CDCL** baut eine Belegung Stück für Stück auf, lernt aus jedem Konflikt eine neue Klausel und kann am Ende
**„unerfüllbar“ beweisen**. **probSAT** (stochastische lokale Suche) würfelt gleich eine ganze Belegung, **dreht** dann immer wieder eine Variable
einer verletzten Klausel **um**, auch wenn das kurzfristig verschlechtert, und hat **kein Gedächtnis und keinen Beweis**: ohne Lösung im Budget lautet
die Antwort „unbekannt“. Die Demo zeigt probSAT an einem Handbeispiel Schritt für Schritt und zählt in **Umdrehungen, Konflikten und Literal-Lesezugriffen**
(nie in Sekunden), wo welches Verfahren mehr leistet: auf wachsenden Zufallsformeln, auf Aufgaben mit Struktur und bei unerfüllbaren Formeln.

Weiter unten: die **Kernfrage** (Zufallsformeln wachsen), zwei Experimente (**Struktur**, **Unerfüllbar und Aufgeben**), die **Erklärtabelle**,
**🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/lokale-suche-sat-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Zwei Wege zum selben Ziel, einem **Plan**, in dem keine **Regel** verletzt ist. Beim **Umstellen** (stochastische lokale Suche, hier probSAT) wird ein ganzer Plan gewürfelt und dann immer wieder eine Aussage einer verletzten Regel umgekehrt, ohne Notizen und ohne Beweis. Beim **Aufbauen mit Notizen** (CDCL) wird der Plan Stück für Stück gebaut, aus jeder Sackgasse entsteht eine neue Regel, und am Ende kann der Löser **beweisen**, dass es keinen Plan gibt.

Die Demo zählt Umdrehungen, Konflikte und Lesezugriffe statt Sekunden. Sie zeigt, bei welchen Aufgaben welcher Weg weniger zählt: bei Zufallsformeln mit wachsender Größe das Umstellen, bei Aufgaben mit Aufbau das Lernen. Nur das Lernen kann „unerfüllbar“ sagen. Alles gilt nur für die gemessenen Aufgaben, eine Gewichtung und lesbaren Programmcode.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/lokale-suche-sat-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert probSAT", expanded=True):
    st.markdown(
        """
1. **Start.** Für jede Variable ein Münzwurf; das ergibt eine ganze Belegung, meist mit verletzten Klauseln.
2. **Klausel wählen.** Solange eine Klausel verletzt ist, wird eine davon gleichverteilt gezogen.
3. **Break zählen.** Für jedes Literal der Klausel: wie viele Klauseln würden verletzt, wenn seine Variable umgedreht wird? Das sind die Klauseln, die **nur** durch das
   aktuell wahre Literal dieser Variablen erfüllt sind (**break**).
4. **Würfeln und umdrehen.** Jede Variable der Klausel bekommt das Gewicht (ε + break)^(−cb), je weniger Schaden, desto größer; gezogen wird mit Wahrscheinlichkeit
   proportional zum Gewicht, auch eine Variable mit break > 0. Die gezogene Variable wird umgedreht.
5. **Aufhören.** Sobald keine Klausel verletzt ist, ist die Belegung ein Modell. Reicht das Budget an Umdrehungen nicht, endet der Lauf mit „unbekannt“: Ein Lauf ohne Lösung beweist nicht, dass es keine gibt.

Die Parameter cb = 2,3 und ε = 0,9 sind die Voreinstellung (cb nach Balint und Schöning 2012 für 3-SAT ohne Make-Anteil; ε = 0,9 ist die Voreinstellung der Kern-Fassung dieser Demo, das
Papier verwendet nach der Prüfung am Preprint ε = 1; die Wirkung von ε ist in der Demo nicht gemessen). In der Seitenleiste lassen sich beide ändern; die vorgerechneten Messreihen stehen fest auf diesen Voreinstellungen.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**probSAT**")
    seed = st.number_input("Zufalls-Seed der Läufe", 0, C.SEED_MAX, step=1, key="seed",
                           help="Ein Zufalls-Seed legt den Münzwurf am Start und alle Ziehungen fest (SplitMix64). Wirkt auf Schritt für Schritt, die Live-Messreihen und das Experiment „Unerfüllbar“.")
    flips = st.select_slider("Budget (Umdrehungen)", C.FLIP_OPTIONEN, key="flips", format_func=E.zahl,
                             help="Obergrenze der Umdrehungen je Lauf. Die vorgerechneten Messreihen stehen fest auf 300.000; Schritt für Schritt zeigt höchstens 2.000.")
    cb = st.select_slider("Exponent cb", C.CB_OPTIONEN, key="cb", format_func=E.dez,
                          help="Gewicht (ε + break)^(−cb): je größer cb, desto stärker bevorzugt probSAT Variablen ohne Schaden. 2,3 nach Balint/Schöning (3-SAT, ohne Make-Anteil); 2,06 ist ein früher gewählter Vergleichswert.")
    eps = st.select_slider("ε", C.EPS_OPTIONEN, key="eps", format_func=E.dez,
                           help="Verhindert Gewicht unendlich bei break = 0 und bestimmt, wie viel Gewicht ein Schaden von 0 gegenüber 1 bekommt.")
    st.markdown("**CDCL**")
    konflikte = st.select_slider("Budget (Konflikte)", C.KONFLIKT_OPTIONEN, key="konflikte", format_func=E.zahl,
                                 help="Obergrenze der Konflikte je Lauf. Die vorgerechneten Messreihen stehen fest auf 20.000.")
    st.button("🎲 Neuer Zufalls-Seed", on_click=randomize_seed, width="stretch")

seed, flips, cb, eps, konflikte = int(seed), int(flips), float(cb), float(eps), int(konflikte)

# --- Experiment 1: von Hand ---------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 probSAT Schritt für Schritt")
formel = st.radio("Formel", C.FORMELN, key="formel", horizontal=True,
                  help="Handbeispiel: fünf Variablen, sieben Klauseln, neun Modelle von 32 Belegungen. Oder eine kleine Zufallsformel (8 bis 12 Variablen, 4,26 Klauseln je Variable, "
                       "gerundet); sie kann auch unerfüllbar sein.")
if formel == C.FORMEL_KLEIN:
    c1, c2, c3 = st.columns([1, 1, 1])
    klein_n = int(c1.slider("Variablen n", *C.KLEIN_N, value=C.DEFAULT_KLEIN_N, key="klein_n",
                            help=f"Zufalls-3-SAT mit 4,26 Klauseln je Variable, gerundet (n = 12: {S.klauselzahl(12)} Klauseln)."))
    klein_seed = int(c2.number_input("Zufalls-Seed der Formel", 0, C.SEED_MAX, value=C.DEFAULT_KLEIN_SEED, step=1, key="klein_seed"))
    c3.write("")
    c3.button("🎲 Neue Formel", on_click=randomize_klein_seed, width="stretch")
else:
    klein_n, klein_seed = C.DEFAULT_KLEIN_N, C.DEFAULT_KLEIN_SEED

lauf_daten = _schrittlauf(formel, klein_n, klein_seed, seed, flips, cb, eps)
lauf = lauf_daten["lauf"]
schritte = lauf.schritte
modelle = lauf_daten["modelle"]
n_var = lauf_daten["n"]
signatur = (formel, klein_n, klein_seed, seed, flips, cb, eps)
if st.session_state.get("schritt_signatur") != signatur or not (0 <= st.session_state.get("schritt", -1) < len(schritte)):
    st.session_state["schritt"] = min(1, len(schritte) - 1)       # auf den Zustand nach der ersten Umdrehung (falls es einen gibt)
    st.session_state["schritt_signatur"] = signatur

m1, m2, m3, m4 = st.columns([3, 2, 2, 3])
m1.metric("Antwort", "Modell" if lauf.modell is not None else "unbekannt")
m2.metric("Umdrehungen", E.zahl(lauf.flips))
m3.metric("Lesezugriffe", E.zahl(lauf.lesezugriffe))
m4.metric("Modelle der Formel (Aufzählung)", f"{len(modelle)} von {2 ** n_var}",
          help="Alle 2^n Belegungen einzeln geprüft, unabhängig von probSAT. Bei 0 ist die Formel unerfüllbar.")
if lauf.modell is None and flips > C.MAX_SCHRITT_FLIPS:
    st.caption(f"Schritt für Schritt zeigt höchstens {E.zahl(C.MAX_SCHRITT_FLIPS)} Umdrehungen, das Budget in der Seitenleiste ist {E.zahl(flips)}.")

if len(schritte) > 1:
    nr = st.slider("Zustand nach k Umdrehungen", 0, len(schritte) - 1, key="schritt",
                   help="0: die gewürfelte Startbelegung. Jeder Schritt zeigt die Belegung vor der nächsten Umdrehung und deren Berechnung.")
else:
    nr = 0
    st.info("Die Startbelegung ist schon ein Modell; es gibt keine Umdrehung zu zeigen.")
s = schritte[nr]
st.info(E.schritt_text(s, n_var, lauf.modell is not None))

links, rechts = st.columns([6, 5])
with links:
    if s.klausel is not None:
        summe_bis = 0.0
        zeilen = []
        for j, (l, b, g) in enumerate(zip(s.literale, s.brk, s.gewichte)):
            summe_bis += g
            zeilen.append({"Literal": A.literal_text(l), "Variable": f"x{abs(l)} = {s.belegung[abs(l) - 1]}", "break": b, "Gewicht": A.zahl_text(g),
                           "Wahrscheinlichkeit": f"{100 * g / s.summe:.1f} %".replace(".", ","), "kumulierte Summe": A.zahl_text(summe_bis),
                           "gewählt": "◀" if j == s.gewaehlt else ""})
        st.markdown(f"**Klausel C{s.klausel}: Break und Gewichte** (cb = {E.dez(cb)}, ε = {E.dez(eps)})")
        st.dataframe(pd.DataFrame(zeilen), hide_index=True, width="stretch")
        st.caption(f"Lesezugriffe nach dieser Umdrehung: {E.zahl(s.lesezugriffe)} (Start: 3 · m = {3 * len(lauf_daten['klauseln'])}; je Umdrehung für jedes der drei Literale "
                   f"die Vorkommen des wahren Literals, dazu beim Umdrehen die Vorkommen beider Literale der gewählten Variablen).")
    else:
        st.markdown("**Ende des Laufs**")
        st.caption(f"Lesezugriffe insgesamt: {E.zahl(s.lesezugriffe)}.")
    st.markdown("**Klauseln unter der Belegung**")
    kz = []
    for i, k in enumerate(lauf_daten["klauseln"]):
        w = A.wahre_literale(k, s.belegung)
        kz.append({"Klausel": _klausel_zeile(i, k), "wahre Literale": w, "Status": "verletzt" if w == 0 else ("nur ein Literal wahr" if w == 1 else "erfüllt"),
                   "gewählt": "◀" if s.klausel == i + 1 else ""})
    st.dataframe(pd.DataFrame(kz), hide_index=True, width="stretch")
with rechts:
    st.plotly_chart(V.build_verlauf_hand(lauf.zahlen, nr), width="stretch", key="chart_verlauf_hand")
    st.caption("Die Kurve darf steigen: probSAT dreht auch Variablen um, die Klauseln verletzen (break > 0), und macht so Schritte, die die Zahl der verletzten Klauseln nicht senken.")
    if lauf.modell is not None and nr == len(schritte) - 1:
        bits = "".join("1" if lauf.modell[v] else "0" for v in range(1, n_var + 1))
        st.success(f"Modell {bits}: " + ", ".join(f"x{v} = {'wahr' if b else 'falsch'}" for v, b in sorted(lauf.modell.items()))
                   + (f". Es ist eines der {len(modelle)} Modelle der Aufzählung." if bits in modelle else ". ACHTUNG: nicht unter den aufgezählten Modellen."))
    elif lauf.modell is None and nr == len(schritte) - 1:
        if not modelle:
            st.warning("Kein Modell nach dem Budget. Die Aufzählung aller Belegungen zeigt: Die Formel ist unerfüllbar. probSAT konnte das nicht sagen und hätte auch mit mehr Umdrehungen nie ein Modell gefunden.")
        else:
            st.warning(f"Kein Modell nach dem Budget, obwohl die Formel {len(modelle)} Modelle hat: ein Lauf ohne Lösung beweist nichts.")
with st.expander("Die Klauseln der Formel"):
    st.markdown("  \n".join(_klausel_zeile(i, k) for i, k in enumerate(lauf_daten["klauseln"])))

st.markdown("---")

# --- Darstellung der Messreihen -------------------------------------------------------------------------------------------------------------


def _fehlt_datei():
    st.warning("Die vorgerechneten Messreihen (lks_messungen.json) fehlen; nur die Live-Messreihen stehen zur Verfügung.")


def _ref_kopf(art: str) -> str:
    meta = E.lade_messungen().get("meta", {})
    return (f"Vorgerechnet, nicht live (Messskript tools/messungen.py, Datei lks_messungen.json): {art} "
            f"Budgets {E.zahl(meta.get('flip_budget', C.BUDGET_REFERENZ_FLIPS))} Umdrehungen (probSAT) und {E.zahl(meta.get('cdcl_budget', C.BUDGET_REFERENZ_KONFLIKTE))} Konflikte (CDCL), "
            f"cb = {E.dez(meta.get('cb', C.DEFAULT_CB))}, ε = {E.dez(meta.get('eps', C.DEFAULT_EPS))}; die Regler cb, ε und die Budgets der Seitenleiste wirken hier nicht.")


def _zelle_zeile(label: str, z: E.Zelle) -> dict:
    return {"Aufgabe": label, "CDCL: erfüllbar / unerfüllbar / offen": f"{z.c_erf} / {z.c_unerf} / {z.c_unb}",
            "probSAT: gelöste Läufe": f"{z.p_gel} von {z.p_laeufe}", "probSAT: Formeln mit Lösung": f"{z.p_formeln} von {z.n_formeln}",
            "Median CDCL": "–" if z.median_cdcl is None else E.zahl(z.median_cdcl), "Median probSAT": "–" if z.median_probsat is None else E.zahl(z.median_probsat),
            "mehr Lesezugriffe": E.verhaeltnis_text(z)}


def _ergebnis_tabelle(zeilen_pro_instanz: list, instanz_label: str) -> pd.DataFrame:
    zeilen = []
    for z in zeilen_pro_instanz:
        c = z["cdcl"]
        p = z["probsat"]
        gel = [r for r in p if r["geloest"]]
        zeilen.append({instanz_label: z["seed"], "CDCL": {True: "erfüllbar", False: "unerfüllbar", None: "offen (Budget)"}[c["antwort"]],
                       "CDCL: Konflikte": E.zahl(c["konflikte"]), "CDCL: Lesezugriffe": E.zahl(c["lesezugriffe"]),
                       "probSAT: gelöst": f"{len(gel)} von {len(p)}",
                       "probSAT: Lesezugriffe (Median der gelösten)": E.zahl(sorted(r["lesezugriffe"] for r in gel)[len(gel) // 2]) if gel else "–",
                       "probSAT: kleinste Zahl verletzter Klauseln am Ende (ungelöste Läufe)": ", ".join(str(r["verletzt_am_ende"]) for r in p if not r["geloest"]) or "–"})
    return pd.DataFrame(zeilen)


# --- Kernfrage: Zufallsformeln wachsen ------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was passiert, wenn Zufallsformeln wachsen?")
st.markdown(
    "Zufalls-3-SAT mit 4,0, 4,2 und 4,26 Klauseln je Variable (4,26 liegt im Übergangsbereich von erfüllbar zu unerfüllbar), 100 bis 600 Variablen. "
    "Verglichen werden gelöste Formeln und Lesezugriffe der **gelösten** Fälle."
)
cn, cv = st.columns(2)
zufall_n = int(cn.select_slider("Variablen n der Messzelle", C.ZUFALL_N, key="zufall_n", help="Vorgerechnete Größen. Die Live-Messreihe darunter rechnet nur bis n = 150."))
zufall_v = float(cv.select_slider("Klauseln je Variable (m/n)", C.VERHAELTNISSE, key="zufall_v", format_func=E.dez))
daten = E.lade_messungen()
if not daten.get("zufall"):
    _fehlt_datei()
else:
    st.caption(_ref_kopf(f"{C.ANZAHL_FORMELN} feste Formeln je Zelle (Zufalls-Seeds 8000 bis {8000 + C.ANZAHL_FORMELN - 1}), 3 probSAT-Läufe je Formel (Zufalls-Seeds 1 bis 3)."))
    zelle = E.zelle_zufall(zufall_n, zufall_v)
    if zelle is None:
        st.info("Diese Zelle ist nicht vorgerechnet.")
    else:
        zk = E.kennzahlen(E.zeilen_von(zelle))
        kind, text = E.verdict_zufall(f"Zufalls-3-SAT n = {zufall_n}, m/n = {E.dez(zufall_v)}", zk, daten["meta"]["cdcl_budget"], daten["meta"]["flip_budget"])
        getattr(st, kind)(text)
    spalte = [(n, E.kennzahlen(E.zeilen_von(z))) for n in C.ZUFALL_N if (z := E.zelle_zufall(n, zufall_v))]
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(V.build_anzahl(spalte, f"Gelöste Formeln je n (m/n = {E.dez(zufall_v)})"), width="stretch", key="chart_anzahl")
    with g2:
        st.plotly_chart(V.build_median([(f"n = {n}", z.median_cdcl, z.c_erf, z.median_probsat, z.p_gel) for n, z in spalte],
                                       f"Lesezugriffe der gelösten Fälle (m/n = {E.dez(zufall_v)})"), width="stretch", key="chart_median")
    st.caption("Fehlt ein Balken, hat das Verfahren in dieser Zelle nichts gelöst. Ein Median über die Gelösten ist eine untere Schranke der Kosten des Verfahrens, sobald Fälle ungelöst bleiben; bei weniger als drei Werten wird die Ampel gelb (siehe Verdikt).")
    tab = []
    for n in C.ZUFALL_N:
        for v in C.VERHAELTNISSE:
            z = E.zelle_zufall(n, v)
            if z:
                tab.append({"n": n, "m/n": E.dez(v), **{k: w for k, w in _zelle_zeile("", E.kennzahlen(E.zeilen_von(z))).items() if k != "Aufgabe"}})
    with st.expander("Alle vorgerechneten Zellen"):
        st.dataframe(pd.DataFrame(tab), hide_index=True, width="stretch")
    with st.expander("Robustheit: cb = 2,3 gegen cb = 2,06"):
        st.caption("Dieselben Formeln und Zufalls-Seeds, nur der Exponent ist ein anderer. Nur für n = 300 und n = 600 gemessen (dort, wo CDCL im Budget nichts mehr löst).")
        rb = []
        for n in (300, 600):
            for v in C.VERHAELTNISSE:
                z = E.zelle_zufall(n, v)
                if z and "probsat_cb_alt" in z["formeln"][0]:
                    a = E.kennzahlen(z["formeln"], "probsat")
                    b = E.kennzahlen(z["formeln"], "probsat_cb_alt")
                    rb.append({"n": n, "m/n": E.dez(v), f"cb = {E.dez(C.DEFAULT_CB)}: gelöste Läufe": f"{a.p_gel} von {a.p_laeufe}",
                               f"cb = {E.dez(C.CB_ALT)}: gelöste Läufe": f"{b.p_gel} von {b.p_laeufe}",
                               f"cb = {E.dez(C.DEFAULT_CB)}: Median": "–" if a.median_probsat is None else E.zahl(a.median_probsat),
                               f"cb = {E.dez(C.CB_ALT)}: Median": "–" if b.median_probsat is None else E.zahl(b.median_probsat)})
        if rb:
            st.dataframe(pd.DataFrame(rb), hide_index=True, width="stretch")

with st.expander("🔁 Live nachrechnen (nur bis n = 150)"):
    st.caption("Dieselben Verfahren (Kern-Kopien von CDCL und probSAT) auf den ersten festen Formeln der gewählten Familie, mit den Budgets, cb, ε und dem Zufalls-Seed der Seitenleiste; "
               "ein probSAT-Lauf je Formel. Mit wenigen Formeln streuen die Mediane stark.")
    l1, l2 = st.columns(2)
    live_n = int(l1.slider("Variablen n (live)", C.LIVE_N[0], C.LIVE_N[1], value=C.DEFAULT_LIVE_N, step=C.LIVE_N[2], key="live_n"))
    live_anz = int(l2.slider("Zahl der Formeln", *C.LIVE_ANZAHL[:2], value=C.LIVE_ANZAHL[2], key="live_anzahl"))
    sig = (live_n, zufall_v, live_anz, konflikte, flips, cb, eps, seed)
    if st.button("Messreihe live starten", key="live_go_zufall", help="Ein Fortschrittsbalken zählt die fertigen Formeln; ein zweiter Klick mit denselben Einstellungen antwortet aus dem Zwischenspeicher."):
        st.session_state["live_zufall"] = {"sig": sig, "daten": L.zufall(*sig)}
    g = st.session_state.get("live_zufall")
    if g and g["sig"] == sig:
        d = g["daten"]
        zk = E.kennzahlen(d["formeln"])
        kind, text = E.verdict_zufall(f"Zufalls-3-SAT n = {d['n']}, m/n = {E.dez(d['verhaeltnis'])} (live)", zk, konflikte, flips)
        getattr(st, kind)(text)
        st.dataframe(_ergebnis_tabelle(d["formeln"], "Formel (Seed)"), hide_index=True, width="stretch")
        st.caption(f"Live gemessen, nicht vorgerechnet: {d['n']} Variablen, {d['m']} Klauseln, {len(d['formeln'])} feste Formeln, ein probSAT-Lauf je Formel (Zufalls-Seed {seed}).")
    elif g:
        st.caption("Die Einstellungen haben sich geändert: Messreihe erneut starten.")

st.markdown("---")

# --- Experiment: Struktur ---------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Und wenn die Aufgabe Struktur hat?")
st.markdown(
    "Aufträge auf Rampen (Konfliktgraph, jede Rampe eine Farbe), und Schur-Partitionen (Zahlen auf Mengen ohne a + b = c in einer Menge). "
    "Verglichen werden dieselben Größen wie oben; probSAT-Läufe sind nur auf den Instanzen gezählt, die CDCL als erfüllbar fand."
)
struktur_label = st.selectbox("Aufgabe", C.STRUKTUR_LABELS, key="struktur", help="Die Tabelle darunter zeigt alle drei vorgerechneten Aufgaben; das Verdikt gilt der gewählten.")
struktur = C.STRUKTUR_VON_LABEL[struktur_label]
if not daten.get("struktur"):
    _fehlt_datei()
else:
    meta = daten["meta"]
    st.caption(_ref_kopf("Rampen: 10 feste Konfliktgraphen (Seeds 500 bis 509), je 5 probSAT-Läufe; Schur: eine Instanz, 20 probSAT-Läufe (Zufalls-Seeds 1 bis 20)."))
    zs = {k: E.kennzahlen(E.zeilen_von(daten["struktur"][k])) for k in C.STRUKTUREN if k in daten["struktur"]}
    if struktur in zs:
        kind, text = E.verdict_struktur(C.STRUKTUREN[struktur], zs[struktur], meta["cdcl_budget"], meta["flip_budget"])
        getattr(st, kind)(text)
    st.plotly_chart(V.build_median([(C.STRUKTUREN[k], z.median_cdcl, z.c_erf, z.median_probsat, z.p_gel) for k, z in zs.items()], "Lesezugriffe der gelösten Fälle je Aufgabe"),
                    width="stretch", key="chart_struktur")
    tabelle = pd.DataFrame([_zelle_zeile(C.STRUKTUREN[k], z) for k, z in zs.items()])
    st.dataframe(tabelle, hide_index=True, width="stretch")
    st.markdown(f"**{C.LATIN12['label']}** (eingefrorene Zeile der Vormessung): CDCL {C.LATIN12['cdcl']}; probSAT {C.LATIN12['probsat']}.")
    st.caption(C.LATIN12["quelle"] + ".")

with st.expander("🔁 Live nachrechnen (kleiner als die Referenz)"):
    st.caption("Mit den Budgets, cb, ε und dem Zufalls-Seed der Seitenleiste. Rampen: die ersten festen Graphen mit je drei probSAT-Läufen (Zufalls-Seeds Seed bis Seed + 2); "
               "Schur: eine Instanz, die gewählte Zahl probSAT-Läufe (Zufalls-Seeds Seed, Seed + 1, …).")
    s1, s2 = st.columns(2)
    if struktur == "rampen160":
        live_gr = int(s1.slider("Aufträge je Graph (live)", *C.LIVE_RAMPEN_N[:2], value=C.DEFAULT_LIVE_RAMPEN_N, step=C.LIVE_RAMPEN_N[2], key="live_rampen_n"))
        live_s_anz = int(s2.slider("Zahl der Graphen", *C.LIVE_ANZAHL[:2], value=C.LIVE_ANZAHL[2], key="live_graphen"))
    else:
        live_gr = 0
        live_s_anz = int(s2.slider("Zahl der probSAT-Läufe", *C.LIVE_SCHUR_LAEUFE[:2], value=C.LIVE_SCHUR_LAEUFE[2], key="live_schur_laeufe"))
    sig = (struktur, live_gr, live_s_anz, konflikte, flips, cb, eps, seed)
    if st.button("Messreihe live starten", key="live_go_struktur", help="Ein Fortschrittsbalken zählt die fertigen Graphen bzw. Läufe; ein zweiter Klick mit denselben Einstellungen antwortet aus dem Zwischenspeicher."):
        st.session_state["live_struktur"] = {"sig": sig, "daten": L.struktur(*sig)}
    g = st.session_state.get("live_struktur")
    if g and g["sig"] == sig:
        d = g["daten"]
        z = E.kennzahlen(d["instanzen"])
        kind, text = E.verdict_struktur(d["label"] + " (live)", z, konflikte, flips)
        getattr(st, kind)(text)
        st.dataframe(_ergebnis_tabelle(d["instanzen"], "Instanz (Seed)"), hide_index=True, width="stretch")
    elif g:
        st.caption("Die Einstellungen haben sich geändert: Messreihe erneut starten.")

st.markdown("---")

# --- Experiment: Unerfüllbar und Aufgeben ----------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Unerfüllbar und Aufgeben")
st.markdown("Von den beiden Verfahren kann nur CDCL „unerfüllbar“ sagen. probSAT bricht nach dem Budget mit „unbekannt“ ab, auch bei einer **erfüllbaren** Formel, die es nicht findet.")
fall_label = st.selectbox("Fall", C.FALL_LABELS, key="fall")
fall = C.FALL_VON_LABEL[fall_label]

if fall == "zufall150":
    z150 = E.zelle_zufall(150, 4.26)
    if z150 is None:
        _fehlt_datei()
    else:
        zk = E.kennzahlen(E.zeilen_von(z150))
        st.caption(_ref_kopf("12 feste Formeln (n = 150, m/n = 4,26), je 3 probSAT-Läufe."))
        kind, text = E.verdict_anteil_unerfuellbar("Zufallsformeln n = 150, m/n = 4,26", zk, daten["meta"]["flip_budget"])
        getattr(st, kind)(text)
        st.dataframe(_ergebnis_tabelle(z150["formeln"], "Formel (Seed)"), hide_index=True, width="stretch")
elif fall == "misserfolg":
    gem = E.ersten_gemischten([z for n in (300, 600) for z in [E.zelle_zufall(n, 4.26), E.zelle_zufall(n, 4.2), E.zelle_zufall(n, 4.0)] if z])
    if gem is None:
        st.info("In den vorgerechneten Zellen mit n ≥ 300 gibt es keine Formel, bei der nur ein Teil der Läufe gelang.")
    else:
        seeds = (gem["geloest"][0], gem["nicht"][0])
        laeufe = _misserfolg(gem["n"], gem["verhaeltnis"], gem["formel_seed"], seeds, flips, cb, eps)
        st.caption(f"Aus den vorgerechneten Zellen: die erste Formel mit n ≥ 300, bei der mit den Voreinstellungen (cb = 2,3, ε = 0,9, 300.000 Umdrehungen) ein Lauf gelang und ein anderer nicht: "
                   f"n = {gem['n']}, m/n = {E.dez(gem['verhaeltnis'])}, Formel-Seed {gem['formel_seed']}, Zufalls-Seeds {seeds[0]} und {seeds[1]}. "
                   f"Die Läufe unten sind live gerechnet, mit den Einstellungen der Seitenleiste für Budget, cb und ε (der Zufalls-Seed der Seitenleiste wirkt hier nicht).")
        kind, text = E.verdict_misserfolg([(sd, l.modell is not None, l.flips, l.kleinste) for sd, l in laeufe])
        getattr(st, kind)(text)
        reihen = [(f"Zufalls-Seed {sd}: " + ("gelöst" if l.modell is not None else "unbekannt"),) + E.kurve_punkte(l, flips) + (C.COLOR_CDCL if l.modell is not None else C.COLOR_PROBSAT,)
                  for sd, l in laeufe]
        st.plotly_chart(V.build_kurven(reihen, flips, "Kleinste Zahl verletzter Klauseln gegen die Umdrehungen"), width="stretch", key="chart_misserfolg")
else:
    fd = _fall(fall, konflikte, flips, cb, eps, seed)
    d = fd["daten"]
    lauf4 = d["lauf"]
    umdrehungen = C.HAND8_FLIPS if fall == "hand8" else flips
    kind, text = E.verdict_unerfuellbar(C.FAELLE[fall], d["cdcl_antwort"], d["cdcl_konflikte"], lauf4.flips, lauf4.kleinste, lauf4.modell is not None, d["modell_ok"])
    getattr(st, kind)(text)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CDCL", {True: "erfüllbar", False: "unerfüllbar", None: "unbekannt (Budget)"}[d["cdcl_antwort"]])
    m2.metric("probSAT", "Modell" if lauf4.modell is not None else "unbekannt")
    m3.metric("kleinste Zahl verletzter Klauseln", lauf4.kleinste, help="Kleinste Zahl verletzter Klauseln, die auf dem Weg vorkam (Start eingeschlossen).")
    m4.metric("Variablen / Klauseln", f"{d['n']} / {d['m']}")
    st.plotly_chart(V.build_kurven([(f"probSAT, Zufalls-Seed {seed}",) + E.kurve_punkte(lauf4, umdrehungen) + (C.COLOR_PROBSAT,)], umdrehungen,
                                   "Kleinste Zahl verletzter Klauseln gegen die Umdrehungen"), width="stretch", key=f"chart_kurve_{fall}")
    if fall == "hand8":
        st.caption("Alle acht Klauseln über drei Variablen verbieten jede der acht Belegungen genau einmal.")
        st.dataframe(pd.DataFrame({"Belegung": [format(i, "03b") for i in range(8)], "verletzte Klauseln": fd["belegungen"]}), hide_index=True)
        st.caption(f"Die Aufzählung der acht Belegungen zeigt: jede verletzt genau {fd['belegungen'][0]} Klausel. Die kleinste Zahl verletzter Klauseln bleibt deshalb bei jeder Umdrehungszahl {lauf4.kleinste}.")
    if fall == "schubfach5":
        st.caption("Sechs Tauben, fünf Löcher: unerfüllbar (Schubfachprinzip). Die kleinste Zahl verletzter Klauseln erreicht 1; ein Modell gibt es nicht.")

st.caption("Die Fälle „Handbeispiel“, „Schubfach“ und „Färbung“ rechnen live mit dem Zufalls-Seed, dem Budget, cb und ε der Seitenleiste; die Fälle mit Zufallsformeln stammen aus den vorgerechneten Messreihen.")

st.markdown("---")

# --- Erklärtabelle ----------------------------------------------------------------------------------------------------------------------------

with st.expander("📋 Erklärtabelle: Verfahren und Begriffe"):
    st.markdown(
        """
| Begriff | Was es ist | Bezugsmenge | Annahme |
|---|---|---|---|
| **CDCL** | baut eine Teilbelegung auf, lernt aus jedem Konflikt eine Klausel und springt zurück | Konflikte, Entscheidungen, gelernte Klauseln | vollständig: mit genug Budget „erfüllbar“ oder „unerfüllbar“ |
| **probSAT** | lokale Suche über ganzen Belegungen: Umdrehen einer Variablen einer verletzten Klausel | Umdrehungen, Literal-Lesezugriffe | unvollständig: nur „Modell“ oder „unbekannt“; kein Gedächtnis, kein Neustart |
| **Break** einer Variablen | Zahl der Klauseln, die nur durch das aktuell wahre Literal dieser Variablen erfüllt sind | Klauseln, in denen das wahre Literal vorkommt | wird bei jeder Umdrehung neu gezählt (Zähler der wahren Literale je Klausel) |
| **Make** einer Variablen | Zahl der verletzten Klauseln, die das Umdrehen erfüllen würde | verletzte Klauseln mit dem Gegenliteral | **in dieser Demo nicht benutzt** (Gewichtung ohne Make-Anteil) |
| **Gewichtung** (ε + break)^(−cb) | Wahrscheinlichkeit proportional zum Gewicht, je Klausel nur über deren drei Variablen | die drei Literale der gewählten Klausel | polynomielle Form für 3-SAT; cb = 2,3, ε = 0,9 voreingestellt |
| **Literal-Lesezugriff** | gelesenes Literal beim Propagieren (CDCL) bzw. beim Zählen von Break und Umdrehen (probSAT) | Zählgröße | verschiedene Operationen: nur der Größenordnung nach vergleichbar, keine Zeitmessung |
        """
    )

st.markdown("---")

# --- Grenzen ----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Lesezugriffe sind vergleichbar** | Sie zählen verschiedene Operationen (Propagation gegen Break-Zählung) und sind nur der Größenordnung nach vergleichbar. Zeit ist nicht gemessen; die Python-Fassung beider Verfahren ist lesbar, nicht schnell. | – |
| **Gleiche Budgets** | 300.000 Umdrehungen gegen 20.000 Konflikte sind verschiedene Einheiten; ein größeres Budget des einen oder anderen verschiebt die Zahl der gelösten Fälle. | – |
| **Ein Medianvergleich über die Gelösten** | Löst ein Verfahren nicht alle Fälle, stammt sein Median aus den leichteren Fällen und ist eine untere Schranke seiner Kosten (Ampel gelb bei weniger als drei Werten). | – |
| **Zufallsformeln stehen für „keine Struktur“** | Gemessen sind nur Zufalls-3-SAT mit 4,0 bis 4,26 Klauseln je Variable und eine probSAT-Gewichtung (polynomiell, ohne Make-Anteil). Für 5-SAT und 7-SAT nennt das Papier eine andere Gewichtung als bessere. | Phasenübergang und DPLL: [sat-phasenuebergang-demo](https://github.com/sebastian-hanisch/sat-phasenuebergang-demo) |
| **Keine Hybride, keine C-Löser** | Gezeigt sind zwei getrennte Verfahren in Python. Aussagen über Löser, die beides verbinden, oder über optimierte Programme macht die Demo nicht. | Lernen und Neustarts: eigene Demos der Linie |
| **probSAT ohne Neustart und ohne Gedächtnis** | Ein Lauf kann im Budget scheitern, ein anderer Zufalls-Seed derselben Formel gelingen (Experiment „Unerfüllbar und Aufgeben“). Ein Neustartplan ist nicht gemessen. | Verwandte Idee „kleine Änderung, Verschlechterung erlaubt“ an Routen: [Trajektorien-Metaheuristiken](https://sebastianhanisch.net/konzepte-trajektorien-metaheuristiken.html), etwa [simulated-annealing-demo](https://github.com/sebastian-hanisch/simulated-annealing-demo) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/lokale-suche-sat-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist eine Formel in konjunktiver Normalform mit $n$ Variablen und $m$ Klauseln. Gesucht ist eine Belegung, die jede Klausel erfüllt (ein Modell). probSAT dreht in jedem Schritt eine Variable einer verletzten Klausel um; gezählt wird in Umdrehungen und Lesezugriffen, nicht in Sekunden.

| Symbol | Bedeutung |
|---|---|
| $n,\ m$ | Zahl der Variablen und der Klauseln |
| $\beta$ | Belegung aller Variablen mit 0 oder 1 |
| $\mathrm{break}(v)$ | Zahl der Klauseln, die nur durch das aktuell wahre Literal von $x_v$ erfüllt sind (Schaden beim Umdrehen) |
| $\varepsilon,\ c_b$ | Parameter der Gewichtung; je größer $c_b$, desto stärker werden Umdrehungen ohne Schaden bevorzugt |
| $w_v,\ P(v)$ | Gewicht einer Variablen und ihre Wahrscheinlichkeit, umgedreht zu werden |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/lokale-suche-sat-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben ist eine Formel in konjunktiver Normalform mit den Klauseln $C_1, \dots, C_m$ über den Variablen $x_1, \dots, x_n$; gesucht ist eine Belegung $\beta \in \{0,1\}^n$, die jede Klausel erfüllt (ein Modell).

| Symbol | Bedeutung |
|---|---|
| $\beta$ | aktuelle Belegung (alle $n$ Variablen) |
| $C$ | eine verletzte Klausel mit den Variablen $v_1, v_2, v_3$ |
| $\mathrm{break}(v)$ | Zahl der Klauseln, die nur durch das aktuell wahre Literal von $x_v$ erfüllt sind |
| $\varepsilon, c_b$ | Parameter der Gewichtung (Voreinstellung $0{,}9$ und $2{,}3$) |
| $w_v$ | Gewicht der Variablen $x_v$ |
| $u$ | gleichverteilte Zufallszahl in $[0, 1)$ |

**Break.** Für eine Belegung $\beta$ und eine Variable $x_v$:
$$\mathrm{break}(v) = \bigl|\{\, C_j : \text{das aktuell wahre Literal von } x_v \text{ ist das einzige wahre Literal von } C_j \,\}\bigr|$$

**Gewicht und Wahl.** Aus der gewählten verletzten Klausel $C$ wird die Variable $x_v$ mit
$$w_v = (\varepsilon + \mathrm{break}(v))^{-c_b}, \qquad P(v) = \frac{w_v}{w_{v_1} + w_{v_2} + w_{v_3}}$$
umgedreht. Umgesetzt wird das mit einer Zufallszahl $u$: gewählt wird das erste Literal, dessen kumulierte Gewichtssumme mindestens $u$ mal die Gesamtsumme beträgt:
$$k^{*} = \min \Bigl\{\, k : \sum_{i \le k} w_{v_i} \ge u \cdot \sum_{i \le 3} w_{v_i} \Bigr\}$$

**Handbeispiel (Schritt 0, Zufalls-Seed 20).** Belegung 00000, verletzt ist nur $C_1 = (x_1 \lor x_2 \lor x_3)$. Die Break-Werte sind $0, 1, 1$, also mit $\varepsilon = 0{,}9$ und $c_b = 2{,}3$:
$$w = (0{,}9^{-2{,}3},\; 1{,}9^{-2{,}3},\; 1{,}9^{-2{,}3}) \approx (1{,}2742,\; 0{,}2285,\; 0{,}2285)$$
**Aufwand.** Gezählt werden Literal-Lesezugriffe: beim Start $3m$ für das Füllen der Zähler der wahren Literale je Klausel, je Umdrehung die Vorkommen des wahren Literals jeder der drei Variablen (Break-Zählung) und die Vorkommen beider Literale der umgedrehten Variablen.

**Antworten.** probSAT liefert nur „Modell“ oder „unbekannt“; kann es keine Belegung ohne verletzte Klausel erreichen (unerfüllbare Formel), bleibt $\min_\beta |\{\text{verletzte Klauseln}\}| \ge 1$, und die Antwort bleibt „unbekannt“.

**Literatur.** probSAT nach Balint und Schöning, *Choosing probability distributions for stochastic local search and the role of make versus break*, SAT 2012, LNCS 7317, S. 16–29 (Volltext gelesen): Auswahl der Variablen allein nach Make und Break; für 3-SAT die polynomielle Gewichtung mit $c_b \approx 2{,}3$ ohne Make-Anteil. Die Konfliktanalyse von CDCL ist Thema einer anderen Demo der Linie.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)

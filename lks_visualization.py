"""Plotly-Figuren: Verlauf der verletzten Klauseln, Anzahl gelöster Formeln, Mediane der Lesezugriffe, Kurven (alle Achsen fest, `fixedrange`)."""

import math

import plotly.graph_objects as go

import lks_constants as C

SCHRIFT = dict(size=12)


def _fest(fig, hoehe: int, legende: bool = True):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=hoehe, margin=dict(l=55, r=20, t=45, b=55), showlegend=legende, font=SCHRIFT,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.38, x=0))
    return fig


def build_verlauf_hand(zahlen: list, aktuell: int):
    """Zahl der verletzten Klauseln nach 0, 1, 2, … Umdrehungen; der gezeigte Schritt ist rot."""
    xs = list(range(len(zahlen)))
    fig = go.Figure(go.Scatter(x=xs, y=zahlen, mode="lines+markers", line=dict(color=C.COLOR_LINIE), marker=dict(size=6),
                               hovertemplate="nach %{x} Umdrehungen: %{y} verletzte Klauseln<extra></extra>", name="verletzte Klauseln"))
    if 0 <= aktuell < len(zahlen):
        fig.add_trace(go.Scatter(x=[aktuell], y=[zahlen[aktuell]], mode="markers", marker=dict(size=13, color=C.COLOR_WAHL, symbol="circle-open", line=dict(width=3)),
                                 name="gezeigter Zustand", hoverinfo="skip"))
    fig.update_layout(title="Verletzte Klauseln über den Umdrehungen", xaxis_title="Umdrehungen", yaxis_title="verletzte Klauseln")
    fig.update_yaxes(range=[-0.3, max(zahlen + [1]) * 1.15 + 0.3], rangemode="tozero")
    fig.update_xaxes(range=[-0.5, max(len(zahlen) - 0.5, 1.5)])
    return _fest(fig, 300)


def build_anzahl(zeilen: list, titel: str):
    """Gruppierte Balken je n: von CDCL gefundene erfüllbare, von CDCL bewiesene unerfüllbare Formeln, von probSAT gelöste Formeln (mindestens ein Lauf).

    `zeilen`: [(n, Zelle)]."""
    xs = [f"n = {n}" for n, _ in zeilen]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[z.c_erf for _, z in zeilen], name="CDCL: erfüllbar gefunden", marker_color=C.COLOR_CDCL, text=[z.c_erf for _, z in zeilen], textposition="outside"))
    fig.add_trace(go.Bar(x=xs, y=[z.c_unerf for _, z in zeilen], name="CDCL: unerfüllbar bewiesen", marker_color="#8fbfb9", text=[z.c_unerf for _, z in zeilen], textposition="outside"))
    fig.add_trace(go.Bar(x=xs, y=[z.p_formeln for _, z in zeilen], name="probSAT: Modell in mindestens einem Lauf", marker_color=C.COLOR_PROBSAT,
                         text=[z.p_formeln for _, z in zeilen], textposition="outside"))
    gesamt = max((z.n_formeln for _, z in zeilen), default=1)
    fig.update_layout(title=titel, barmode="group", yaxis_title="Formeln", uniformtext_minsize=9)
    fig.update_yaxes(range=[0, gesamt * 1.18])
    return _fest(fig, 360)


def build_median(daten: list, titel: str):
    """Mediane der Lesezugriffe (logarithmisch) je Beschriftung; Verfahren ohne gelöste Fälle fehlen, die Basis steht im Hover.

    `daten`: [(Beschriftung, Median CDCL | None, Werte CDCL, Median probSAT | None, Werte probSAT)]."""
    fig = go.Figure()
    for idx, (name, farbe) in enumerate((("CDCL", C.COLOR_CDCL), ("probSAT", C.COLOR_PROBSAT))):
        xs = [d[0] for d in daten if d[1 + 2 * idx] is not None]
        ys = [d[1 + 2 * idx] for d in daten if d[1 + 2 * idx] is not None]
        basis = [d[2 + 2 * idx] for d in daten if d[1 + 2 * idx] is not None]
        fig.add_trace(go.Bar(x=xs, y=ys, name=name, marker_color=farbe, customdata=basis,
                             hovertemplate="%{x}: Median %{y:,.0f} Lesezugriffe (aus %{customdata} gelösten Fällen)<extra>" + name + "</extra>"))
    hoch = max([v for d in daten for v in (d[1], d[3]) if v] + [10])
    fig.update_layout(title=titel, barmode="group", yaxis_title="Lesezugriffe (Median, log.)")
    fig.update_yaxes(type="log", range=[1, math.log10(hoch) + 0.4])
    return _fest(fig, 360)


def build_kurven(reihen: list, budget: int, titel: str):
    """Kleinste Zahl verletzter Klauseln gegen die Umdrehungen (Treppenkurven, x logarithmisch). `reihen`: [(Beschriftung, xs, ys, Farbe)]."""
    fig = go.Figure()
    hoch = 1
    for name, xs, ys, farbe in reihen:
        fig.add_trace(go.Scatter(x=[max(x, 1) for x in xs], y=ys, mode="lines", line=dict(shape="hv", color=farbe, width=2.5), name=name,
                                 hovertemplate="nach %{x} Umdrehungen: kleinste Zahl verletzter Klauseln %{y}<extra></extra>"))
        hoch = max(hoch, max(ys))
    fig.add_vline(x=budget, line=dict(color="rgba(150,150,150,0.8)", dash="dot"))
    fig.update_xaxes(type="log", range=[0, math.log10(max(budget, 10)) + 0.05])
    fig.update_yaxes(range=[-0.3, hoch * 1.1 + 0.5])
    fig.update_layout(title=titel, xaxis_title="Umdrehungen (logarithmisch)", yaxis_title="kleinste Zahl verletzter Klauseln bisher")
    return _fest(fig, 360)

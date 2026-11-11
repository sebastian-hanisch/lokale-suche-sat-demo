"""Zweig-Tests: jede einstellbare Variante weicht auf mindestens einer Instanz von der Nachbarvariante ab (kein toter Zweig, keine Nullspalte)."""

import lks_algorithm as A
import lks_instanzen as I
import lks_scenario as S


def _laeufe(**kw):
    out = []
    for seed in range(20):
        inst = I.rand3(30, 128, 700 + seed)
        l = A.probsat_lauf(inst.n, inst.klauseln, 1500, seed, **kw)
        out.append((l.flips, l.lesezugriffe, l.kleinste))
    return out


def test_cb_aendert_laeufe():
    assert _laeufe(cb=2.3) != _laeufe(cb=2.06) and _laeufe(cb=2.3) != _laeufe(cb=3.5) and _laeufe(cb=1.5) != _laeufe(cb=2.3)


def test_eps_aendert_laeufe():
    assert _laeufe(eps=0.9) != _laeufe(eps=0.5) and _laeufe(eps=0.9) != _laeufe(eps=2.0)


def test_seed_aendert_laeufe():
    a = [A.probsat_lauf(30, I.rand3(30, 128, 5).klauseln, 1500, s).lesezugriffe for s in range(10)]
    assert len(set(a)) > 1


def test_budget_wirkt():
    inst = S.schubfach(4)
    kurz, lang = A.probsat_lauf(inst.n, inst.klauseln, 100, 1), A.probsat_lauf(inst.n, inst.klauseln, 5000, 1)
    assert kurz.flips == 100 and lang.flips == 5000 and kurz.lesezugriffe < lang.lesezugriffe and lang.kleinste <= kurz.kleinste


def test_startbelegung_wirkt():
    inst = I.rand3(20, 80, 3)
    a = A.probsat_lauf(20, inst.klauseln, 500, 1, start={v: False for v in range(1, 21)})
    b = A.probsat_lauf(20, inst.klauseln, 500, 1)
    assert (a.flips, a.lesezugriffe) != (b.flips, b.lesezugriffe)


def test_formelfamilien_unterscheiden_sich_und_haben_klauseln():
    kleine = S.kleine_formel(10, 0)
    assert kleine.n == 10 and len(kleine.klauseln) == 43 and kleine.klauseln != S.hand_formel().klauseln
    assert S.zufall_formel(100, 4.26, 0).klauseln != S.zufall_formel(100, 4.26, 1).klauseln
    assert len(S.zufall_formel(300, 4.2, 0).klauseln) == 1260 and len(S.zufall_formel(600, 4.26, 0).klauseln) == 2556
    r, s = S.rampen(60, 500), S.schur(13, 3)
    assert r.meta["einkleidung"] == "rampen" and s.meta["art"] == "schur" and r.klauseln != s.klauseln

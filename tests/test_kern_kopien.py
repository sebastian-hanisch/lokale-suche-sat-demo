"""Die kopierten Kern-Module (`lks_rng`, `lks_instanzen`, `lks_cdcl`, `lks_probsat`): wörtliche Kopie, Regressionswerte, Einheiten mit Handrechnung.

Die Kopien stammen aus `sat-cp-planung/kern/` (Kern-Version im Modulkopf). Die Vergleichsprüfung mit dem Kern läuft nur, solange der Ordner
neben dem Repo liegt; die übrigen Tests bleiben als Regression bei der Kopie (SplitMix64-Werte, Instanzerzeuger, CDCL-Einheiten, probSAT).
"""

import re
from pathlib import Path

import pytest

import lks_instanzen as I
from lks_cdcl import Loeser, luby, solve
from lks_probsat import probsat
from lks_rng import SplitMix64

ROOT = Path(__file__).resolve().parent.parent
KERN = ROOT.parent / "sat-cp-planung" / "kern"
VERSION = {"rng": "5d5d8f45d0e1eddf", "instanzen": "6795de796b66fff8", "cdcl": "832b2c10dfdea62d", "probsat": "8caf126238c62c92"}


def _lies(pfad: Path) -> str:
    return pfad.read_bytes().decode("utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("modul", list(VERSION))
def test_kopie_gleicht_dem_kern_bis_auf_kopf_und_importe(modul):
    quelle = KERN / f"{modul}.py"
    if not quelle.exists():
        pytest.skip("kern/ liegt nicht neben dem Repo")
    kopie = _lies(ROOT / f"lks_{modul}.py")
    kopf = kopie.split("\n", 2)
    assert VERSION[modul] in kopf[0] and f"kern/{modul}.py" in kopf[0]
    rest = kopie.split("\n", 2)[2]
    rest = re.sub(r"^from lks_rng import", "from rng import", rest, flags=re.M)
    assert rest == _lies(quelle)


def test_kern_version_stimmt_mit_hashes_txt():
    hashes = KERN / "HASHES.txt"
    if not hashes.exists():
        pytest.skip("kern/ liegt nicht neben dem Repo")
    eintraege = {zeile.split()[1]: zeile.split()[0] for zeile in hashes.read_text(encoding="utf-8").splitlines() if zeile.strip()}
    for modul, version in VERSION.items():
        assert eintraege[f"{modul}.py"] == version


# --- SplitMix64 und Instanzen -------------------------------------------------------------------------------------------------------------

def test_splitmix_bekannte_werte():
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    h = SplitMix64(12345)
    assert [h.next() for _ in range(3)] == [2454886589211414944, 3778200017661327597, 2205171434679333405]


def test_splitmix_hilfsmethoden():
    g = SplitMix64(5)
    xs = [g.random() for _ in range(1000)]
    assert all(0 <= x < 1 for x in xs) and 0.45 < sum(xs) / 1000 < 0.55
    liste = list(range(20))
    SplitMix64(3).shuffle(liste)
    assert sorted(liste) == list(range(20)) and liste != list(range(20))


def test_rand3_referenzwerte_und_praefix():
    # Referenzwerte aus red_scenario.random_formula (Komplexitätsklassen): n = 5, m = 3, Seed 7
    assert I.rand3(5, 3, 7).klauseln == [(3, -2, -1), (-4, -1, 5), (1, 2, -3)]
    kurz, lang = I.rand3(20, 30, 1).klauseln, I.rand3(20, 40, 1).klauseln
    assert lang[:30] == kurz and all(len({abs(l) for l in c}) == 3 for c in lang)


def test_schubfach_schur_faerbung_handwerte():
    inst = I.pigeonhole(2)                      # 3 Tauben, 2 Löcher
    assert inst.n == 6 and len(inst.klauseln) == 3 + 2 * 3
    assert solve(inst.n, inst.klauseln).antwort is False
    assert solve(*I.schur(13, 3)[:2]).antwort is True and solve(*I.schur(14, 3)[:2]).antwort is False      # S(3) = 13
    dreieck = I.faerbung(3, [(0, 1), (1, 2), (0, 2)], 2)
    assert solve(dreieck.n, dreieck.klauseln).antwort is False
    a, b = I.flat_graph(40, 4.0, 3), I.flat_graph(40, 4.0, 3)
    assert a.klauseln == b.klauseln and len(a.meta["kanten"]) == 80
    r = I.rampen_instanz(30, 3.0, 2, 4)
    assert r.meta["einkleidung"] == "rampen" and r.meta["rampen"] == 4


# --- CDCL-Einheiten -----------------------------------------------------------------------------------------------------------------------

def test_luby_folge():
    assert [luby(i) for i in range(1, 16)] == [1, 1, 2, 1, 1, 2, 4, 1, 1, 2, 1, 1, 2, 4, 8]
    with pytest.raises(ValueError):
        luby(0)


def _lehrbeispiel(**kw):
    # Von Hand: c1 = (¬1 ∨ 2), c2 = (¬1 ∨ 3 ∨ 5), c3 = (¬2 ∨ 4), c4 = (¬3 ∨ ¬4)
    return Loeser(5, [(-1, 2), (-1, 3, 5), (-2, 4), (-3, -4)], **kw)


@pytest.mark.parametrize("watch", [True, False])
def test_konfliktanalyse_1uip_handrechnung(watch):
    """Entscheidung ¬5 (Stufe 1), dann 1 (Stufe 2): 1 → 2 (c1), 1 ∧ ¬5 → 3 (c2), 2 → 4 (c3), c4 ist verletzt. 1-UIP ist die Entscheidung 1 selbst.
    Gelernt wird (¬1 ∨ 5), Rücksprung auf Stufe 1, LBD 2."""
    s = _lehrbeispiel(watch=watch)
    s.entscheide(-5)
    assert s.propagiere() is None
    s.entscheide(1)
    k = s.propagiere()
    assert k is not None
    klausel, rueck, lbd = s.analysiere(k)
    assert sorted(klausel) == [-1, 5] and klausel[0] == -1 and rueck == 1 and lbd == 2


def test_cdcl_antworten_mit_modellpruefung():
    erg = solve(3, [(1, 2, 3), (-1, 2), (-2, 3)])
    assert erg.antwort is True and I.pruefe_modell([(1, 2, 3), (-1, 2), (-2, 3)], erg.modell)
    assert solve(1, [(1,), (-1,)]).antwort is False


# --- probSAT (Kopie) ----------------------------------------------------------------------------------------------------------------------

def test_probsat_findet_modelle_und_zaehlt():
    erfolge = 0
    for seed in range(10):
        inst = I.rand3(60, 200, seed)                           # m/n = 3,3: leicht erfüllbar
        r = probsat(inst.n, inst.klauseln, 50000, seed)
        assert r.lesezugriffe > 0
        if r.modell is not None:
            erfolge += 1
            assert I.pruefe_modell(inst.klauseln, r.modell) and r.verletzt_am_ende == 0
    assert erfolge == 10


def test_probsat_deterministisch_und_ehrlich_bei_unerfuellbar():
    inst = I.rand3(40, 150, 2)
    a, b = probsat(inst.n, inst.klauseln, 5000, 7), probsat(inst.n, inst.klauseln, 5000, 7)
    assert (a.flips, a.lesezugriffe, a.modell) == (b.flips, b.lesezugriffe, b.modell)
    schub = I.pigeonhole(4)
    r = probsat(schub.n, schub.klauseln, 2000, 1)
    assert r.modell is None and r.flips == 2000 and r.verletzt_am_ende >= 1   # kann „unerfüllbar“ nicht sagen, nur „nichts gefunden“


def test_probsat_start_belegung():
    kl = [(1, 2), (-1, 3)]
    r = probsat(3, kl, 100, 0, start={1: True, 2: False, 3: True})          # die Startbelegung erfüllt schon alles: 0 Umdrehungen
    assert r.flips == 0 and r.modell == {1: True, 2: False, 3: True}

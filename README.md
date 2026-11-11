# Lokale Suche gegen CDCL – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-lokale-suche-sat-demo.streamlit.app/)**

Demo der Linie **SAT und Constraint Programming** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Sie steht als **Kontrast** neben dem Konfliktlernen: derselbe Zweck (eine erfüllende Belegung finden), eine andere Bauweise, nämlich **kein Gedächtnis und keine Beweise**. Gezeigt wird probSAT, eine stochastische lokale Suche, an einem Handbeispiel Schritt für Schritt und im Vergleich mit CDCL auf Zufalls-3-SAT als Wachstumsmaß, auf Aufträgen auf Rampen (3-Färbung eines Konfliktgraphen) und auf Schur-Partitionen. Verbunden ist sie mit der Linie der Trajektorien-Metaheuristiken (dieselbe Idee „kleine Änderung, Verschlechterung erlaubt“, dort an Routen).

## Warum dieses Problem

**CDCL** baut eine Belegung auf, lernt aus jedem Konflikt eine Klausel und kann „unerfüllbar“ beweisen. **probSAT** würfelt eine ganze Belegung und dreht immer wieder eine Variable einer verletzten Klausel um, bevorzugt solche, die wenige andere Klauseln verletzen. Findet es nichts, lautet die Antwort „unbekannt“. Die Demo misst in **Umdrehungen, Konflikten und Literal-Lesezugriffen** (nie in Sekunden), wo welches Verfahren mehr leistet: **In den gemessenen Zufallszellen wird der Vorsprung der lokalen Suche mit wachsendem n größer (bei 100 Variablen und 4,2 bis 4,26 Klauseln je Variable braucht sie noch mehr Lesezugriffe als CDCL, bei 300 Variablen im Median 33- bis 69-mal weniger, bei m/n = 4,2 und 4,26 allerdings mit nur einem CDCL-Wert, also nur als Richtwert; bei 600 Variablen löst CDCL im Budget keine Formel; mit anderen Formeln verschiebt sich der Faktor bei n = 150 von 2,6 / 5,5 / 1,8 auf 5,1 / 10,2 / 4,6, siehe Stabilität); auf den beiden gemessenen Strukturfamilien (Rampen, eine Schur-Instanz) kehrt es sich um (Rampen: probSAT im Median 34-mal mehr Lesezugriffe, Schur k = 4, n = 43: 4530-mal mehr, beide probSAT-Mediane nur über die gelösten Läufe); und nur CDCL kann „unerfüllbar“ sagen.** Die Aussagen gelten für die gemessenen Zellen, die eine Gewichtung von probSAT und die Python-Fassung beider Verfahren (Voraussetzungen unten bei den Befunden).

## Modell

- **probSAT.** Start: je Variable ein Münzwurf. Solange eine Klausel verletzt ist, wird eine verletzte Klausel gleichverteilt gezogen und aus ihr eine Variable mit Wahrscheinlichkeit proportional zu (ε + break)^(−cb) umgedreht; break ist die Zahl der Klauseln, die nur durch das aktuell wahre Literal dieser Variablen erfüllt sind. Kein Make-Anteil, kein Neustart, kein Gedächtnis. Voreinstellung cb = 2,3 (Balint und Schöning, SAT 2012, LNCS 7317: für 3-SAT ohne Make-Anteil, Volltext gelesen) und ε = 0,9 (Voreinstellung der Kern-Fassung der Linie; das Papier verwendet nach der Prüfung am Preprint ε = 1, die Wirkung von ε ist in der Demo nicht gemessen).
- **CDCL.** Kern-Kopie der Linie (1-UIP-Konfliktanalyse, Aktivität, Phasenspeicher, Luby-Neustarts, Watched Literals), Konfliktbudget 20.000 in den vorgerechneten Messreihen.
- **Aufwand.** Vergleichseinheit sind **Literal-Lesezugriffe**: bei CDCL gelesene Literale der Propagation und der Konfliktanalyse, bei probSAT 3·m beim Füllen der Zähler, je Umdrehung die Vorkommen der wahren Literale der drei Variablen (Break-Zählung) und die Vorkommen beider Literale der umgedrehten Variablen. Das sind Zählgrößen **verschiedener Operationen**, nur der Größenordnung nach vergleichbar. Ein Median steht nur über die **gelösten** Fälle eines Verfahrens und ist eine untere Schranke seiner Kosten, sobald Fälle ungelöst bleiben; die Ampel wird gelb, wenn ein Median aus weniger als drei Werten stammt (Konvention der Demo).
- **Antworten.** CDCL: erfüllbar, unerfüllbar oder (am Budget) unbekannt. probSAT: Modell oder unbekannt, nie „unerfüllbar“.
- **Instanzen.** Alle Zufallsinstanzen über den ganzzahligen SplitMix64-Generator (gleiche Werte auf jeder Plattform und Python-Version). Zufalls-3-SAT n = 100, 150, 300, 600 mit m/n = 4,0 / 4,2 / 4,26 (4,26 im Übergangsbereich), je 12 feste Formeln (Zufalls-Seeds 8000 bis 8011); Rampen: 10 feste Konfliktgraphen mit 160 Aufträgen, mittlerem Grad 4,5 und 3 Rampen (Seeds 500 bis 509); Schur k = 4, n = 43 und k = 3, n = 13; Schubfach h = 5 und alle 8 Klauseln über 3 Variablen für „unerfüllbar“.
- Mathematik und Symboltabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| probSAT mit Spur, Verlauf, Zähler | `lks_algorithm.py` | eigener Code; läuft Zug um Zug wie die Kern-Kopie (Flips, Lesezugriffe, Modell gleich, `tests/test_algorithm.py`) und liefert dazu das Protokoll je Umdrehung |
| probSAT (Kern) | `lks_probsat.py` | **wörtliche Kopie** des Kern-Moduls `probsat.py` der Linie (Kern-Version 8caf126238c62c92); nur der Import ist auf `lks_rng` umgestellt (`tests/test_kern_kopien.py`); die Messreihen rechnen mit ihr |
| CDCL | `lks_cdcl.py` | Kopie des Kern-Moduls `cdcl.py` (832b2c10dfdea62d) |
| SplitMix64 | `lks_rng.py` | Kopie des Kern-Moduls `rng.py` (5d5d8f45d0e1eddf) |
| Instanzerzeuger | `lks_instanzen.py` | Kopie des Kern-Moduls `instanzen.py` (6795de796b66fff8) |
| Handbeispiel, Formelfamilien | `lks_scenario.py` | Handbeispiel (n = 5), kleine Zufallsformeln, feste Formeln der Messreihen |
| Messreihen, Kennzahlen, Verdikte | `lks_evaluation.py` | Verdikte sind reine Funktionen; jede Zahl im Text stammt aus den Kennzahlen |
| Vorgerechnete Messreihen | `lks_messungen.json` | geschrieben von `tools/messungen.py` |

Experimente in der App: **probSAT Schritt für Schritt** (Handbeispiel oder kleine Zufallsformel mit 8 bis 12 Variablen), **Kernfrage** (Zufallsformeln wachsen, mit Robustheitszeile cb = 2,06 gegen 2,3), **Struktur** (Rampen, Schur, eine eingefrorene Zeile zu lateinischen Quadraten), **Unerfüllbar und Aufgeben** (fünf Fälle), dazu eine Erklärtabelle. Die großen Messreihen sind **vorgerechnet, nicht live**; die Live-Messreihen rechnen nur bis n = 150 (Zufall), bis 160 Aufträge (Rampen) und an den beiden Schur-Instanzen.

## Befunde (gemessen, keine Behauptungen)

Die Zahlen dieser Tabelle stehen in `tests/test_claims.py` (Messung: `lks_messungen.json`, Skript `tools/messungen.py`). Zufallsformeln: **12 feste Formeln je Zelle** (Zufalls-Seeds 8000 bis 8011), **3 probSAT-Läufe je Formel** (Zufalls-Seeds 1 bis 3, also 36 Läufe je Zelle), cb = 2,3, ε = 0,9, Budgets 300.000 Umdrehungen (probSAT) und 20.000 Konflikte (CDCL, ein Lauf je Formel). „Offen“ heißt: CDCL hat im Konfliktbudget weder ein Modell gefunden noch Unerfüllbarkeit bewiesen. Mediane der Lesezugriffe nur über die gelösten Fälle des Verfahrens, die Zahl der Werte steht dabei.

| Frage | Befund |
|---|---|
| **Gelöste Formeln bei m/n = 4,0** | CDCL findet bei n = 100 / 150 / 300 / 600 in 12 / 12 / 7 / 0 von 12 Formeln ein Modell (n = 300: 5 offen, n = 600: 12 offen); probSAT löst in jeder Zelle in mindestens einem Lauf alle 12 Formeln, in 36 / 36 / 35 / 35 von 36 Läufen (`test_claim_wachstum_cdcl_entscheidet_weniger_probsat_loest_bis_n_600`). |
| **Übergangsbereich (m/n = 4,2 und 4,26)** | Bei n = 100 und 150 entscheidet CDCL alle 12 Formeln: bei 4,2 6 erfüllbar und 6 unerfüllbar (beide n), bei 4,26 6 / 6 (n = 100) und 4 / 8 (n = 150). probSAT löst dort genau die von CDCL als erfüllbar gefundenen Formeln, in allen drei Läufen, und nie eine unerfüllbare. Bei n = 300 findet CDCL nur 1 Formel (11 offen, beide Verhältnisse), probSAT löst 25 bzw. 18 von 36 Läufen (9 bzw. 6 Formeln); bei n = 600 entscheidet CDCL keine Formel, probSAT löst 21 bzw. 12 von 36 Läufen (9 bzw. 6 Formeln) (`test_claim_zufallszelle`, `test_claim_bis_n_150_loest_probsat_genau_die_von_cdcl_gefundenen_formeln_und_nie_eine_unerfuellbare`). |
| **Lesezugriffe (Median der Gelösten)** | Verhältnis CDCL zu probSAT bei m/n = 4,0 / 4,2 / 4,26: n = 100: 1,5 / **0,4** / **0,5** (probSAT braucht bei 4,2 und 4,26 das 2,7- bzw. 2,2-Fache von CDCL); n = 150: 2,6 / 5,5 / 1,8; n = 300: **33** / 69 / 61. Bei n = 300 stammt der CDCL-Median für 4,2 und 4,26 aus **je einem** gelösten Fall und ist eine untere Schranke seiner Kosten; auch der probSAT-Median steht nur über die gelösten Läufe (25 bzw. 18 von 36), das Verhältnis dort ist deshalb ein Richtwert und kein belegter Mindestwert. Bei m/n = 4,0 (7 CDCL-Werte) gilt das nicht in dieser Schärfe, dort löst probSAT 35 von 36 Läufen. Bei n = 600 gibt es keinen CDCL-Median. Die Lesezugriffe beider Verfahren zählen verschiedene Operationen und sind nur der Größenordnung nach vergleichbar (`test_claim_lesezugriffe_verhaeltnis_je_zelle`). |
| **Gleiche Formel, anderer Zufalls-Seed** | Bei 11 der 144 Zufallsformeln (alle Zellen zusammen) gelang nur ein Teil der drei probSAT-Läufe, davon 9 bei n = 600 (1 / 4 / 4 bei m/n = 4,0 / 4,2 / 4,26), 2 bei n = 300. Beispiel: n = 300, m/n = 4,2, Formel-Seed 8008: Zufalls-Seed 3 findet nach 27.426 Umdrehungen ein Modell, die Seeds 1 und 2 nicht in 300.000 (`test_claim_gemischte_formeln_gleiche_formel_anderer_seed`, `test_claim_misserfolg_erfuellbare_formel_ein_lauf_scheitert`). |
| **Robustheit gegen cb** | Mit cb = 2,06 statt 2,3 (dieselben Formeln und Seeds, nur n = 300 und 600) weicht die Zahl gelöster Läufe in keiner der sechs Zellen um mehr als einen Lauf ab (36 / 25 / 18 bei n = 300, 34 / 20 / 11 bei n = 600 gegen 35 / 25 / 18 und 35 / 21 / 12); die Mediane der probSAT-Läufe unterscheiden sich (z. B. n = 300, m/n = 4,26: 991.560 gegen 728.636) (`test_claim_robustheit_cb_2_06_gegen_2_3`). |
| **Struktur: Aufträge auf Rampen** | 10 feste Graphen (160 Aufträge, 3 Rampen, mittlerer Grad 4,5): CDCL 6 erfüllbar, 4 unerfüllbar (Seeds 501, 504, 505, 509). probSAT löst auf den 6 erfüllbaren Graphen 23 von 30 Läufen (5 Läufe je Graph), auf den unerfüllbaren erwartungsgemäß keinen. Median Lesezugriffe: CDCL 27.570,5 (6 Werte), probSAT 929.074 (23 Werte), also **34-mal** mehr für probSAT (`test_claim_struktur`). |
| **Struktur: Schur** | Eine Instanz, 20 probSAT-Läufe (Zufalls-Seeds 1 bis 20): k = 4, n = 43: CDCL 2.835 Lesezugriffe (1 Wert), probSAT 12.842.630 (**3 von 20** Läufen gelöst), 4530-mal mehr, untere Schranke. k = 3, n = 13: CDCL 1.276, probSAT 22.297 (20 von 20 Läufen), 17-mal mehr (`test_claim_struktur`). |
| **Lateinisches Quadrat (eingefroren)** | Ordnung 12, Lücken 0,58, 4 Instanzen: CDCL löst alle 4, probSAT **0 von 20** Läufen. Diese Zeile ist eine Konstante der Vormessung (andere Instanzfamilie, Zufallsgenerator Python-`random`, cb = 2,06) und in dieser Demo nicht nachgerechnet; der Erzeuger liegt nicht in der Demo (`test_claim_latin12_zeile_ist_konstante_der_vormessung`). |
| **Unerfüllbar** | Zufallsformeln n = 150, m/n = 4,26: CDCL beweist 8 von 12 als unerfüllbar, bei den 24 probSAT-Läufen auf diesen Formeln gibt es kein Modell. Alle 8 Klauseln über 3 Variablen: CDCL nach 4 Konflikten „unerfüllbar“, probSAT nach 1.000 Umdrehungen mit kleinster Zahl verletzter Klauseln 1 (jede der 8 Belegungen verletzt genau eine). Schubfach h = 5 (30 Variablen, 81 Klauseln): CDCL nach 159 Konflikten „unerfüllbar“, probSAT nach 300.000 Umdrehungen (Zufalls-Seed 20) kleinste Zahl 1. Unerfüllbare Färbung (Graph-Seed 501, 480 Variablen, 1.240 Klauseln): CDCL nach 151 Konflikten, probSAT (Seed 20, 300.000 Umdrehungen) kleinste Zahl 1 (`test_claim_unerfuellbare_faelle`, `test_claim_zufall_150_426_anteil_unerfuellbar`). Über alle 144 Zufallsformeln und die Strukturinstanzen löst probSAT keine von CDCL als unerfüllbar bewiesene Formel (`test_probsat_loest_nie_eine_von_cdcl_bewiesen_unerfuellbare_formel`). |
| **Handbeispiel** | n = 5, 7 Klauseln, 9 Modelle von 32 Belegungen, Zufalls-Seed 20, cb = 2,3, ε = 0,9: 3 Umdrehungen, Lesezugriffe 32 / 44 / 54, Gewichte 1,2742 / 0,2285 / 0,2285, Modell 10000 (von Hand nachgerechnet in `tests/test_algorithm.py`). |

### Stabilität (Gegenprobe, nicht Teil der Tests)

Die Gegenprobe mit **anderen zwölf Formeln** (Skript `tools/gegenprobe.py`, Formel-Seeds 9000 bis 9011, n = 150 und 300, sonst gleiche Verfahren und Budgets; Ausgabe `tools/gegenprobe_ausgabe.txt`) ergab:

| Zelle | CDCL erfüllbar / unerfüllbar / offen | probSAT gelöste Läufe | Median CDCL (Werte) / probSAT (Werte) |
|---|---|---|---|
| n = 150, 4,0 | 12 / 0 / 0 | 36 von 36 | 194.598 (12) / 37.990 (36) |
| n = 150, 4,2 | 8 / 4 / 0 | 24 von 36 | 469.079 (8) / 46.206 (24) |
| n = 150, 4,26 | 8 / 4 / 0 | 24 von 36 | 561.835 (8) / 123.171 (24) |
| n = 300, 4,0 | 3 / 0 / 9 | 36 von 36 | 10.022.604 (3) / 220.959 (36) |
| n = 300, 4,2 | 0 / 0 / 12 | 30 von 36 | – / 738.800 (30) |
| n = 300, 4,26 | 0 / 0 / 12 | 19 von 36 | – / 1.025.351 (19) |

Die Richtung reproduziert sich: bei n = 150 ist probSAT in allen drei Zellen günstiger (Faktor 5,1 / 10,2 / 4,6; in der Hauptreihe 2,6 / 5,5 / 1,8), bei n = 300 löst CDCL höchstens 3 von 12 Formeln, probSAT 36 / 30 / 19 von 36 Läufen. **Die Zahlen schwanken mit der Formelmenge**: CDCL findet bei n = 300, m/n = 4,0 in der Hauptreihe 7, in der Gegenprobe 3 Formeln; bei n = 300, m/n = 4,2 dort 1, hier keine; der Anteil unerfüllbarer Formeln bei n = 150, m/n = 4,26 ist 8 von 12 gegen 4 von 12. Das Verhältnis der Mediane bei n = 150 ist deshalb nur der Größenordnung nach belegt, die Reihenfolge „n = 100: CDCL günstiger bei 4,2 und 4,26, ab n = 150 probSAT günstiger“ nur für die Hauptreihe (n = 100 ist in der Gegenprobe nicht gemessen).

## Ehrliche Grenzen

- **Eine Gewichtung, ein Verfahren.** Gemessen ist probSAT mit der polynomiellen Gewichtung ohne Make-Anteil, ohne Neustart, an 3-SAT-Familien. Für 5-SAT und 7-SAT nennt das Papier eine andere Gewichtung als bessere. „Die lokale Suche gewinnt bei Zufallsformeln“ gilt nur für die gemessenen Zellen (n = 150 bis 600, m/n = 4,0 bis 4,26) und diese Gewichtung, bei n = 100 und 4,2 bis 4,26 sagt die Messung das Gegenteil.
- **Wenige Formeln.** 12 feste Formeln je Zelle, 10 Konfliktgraphen, bei Schur eine Instanz; die Gegenprobe zeigt Schwankungen (siehe Stabilität). Ein Median über die Gelösten ist eine untere Schranke der Kosten des Verfahrens, sobald Fälle ungelöst bleiben; die Ampel in der App wird gelb, wenn er aus weniger als drei Werten stammt: das betrifft n = 300 mit m/n = 4,2 und 4,26 (ein CDCL-Wert) und beide Schur-Instanzen (ein CDCL-Wert).
- **Budgets verschiedener Einheiten.** 300.000 Umdrehungen gegen 20.000 Konflikte; „offen“ bei CDCL heißt nur „im Budget nichts entschieden“. Mit einem anderen Budget verschieben sich die Zahlen gelöster Fälle. Gemessen ist nur dieses Paar.
- **Lesezugriffe sind Zählgrößen verschiedener Operationen**, nur der Größenordnung nach vergleichbar. **Zeit ist nicht gemessen**; beide Verfahren laufen als lesbarer Python-Code. Aussagen über optimierte Löser in C macht die Demo nicht.
- **Keine Hybride.** Ob moderne Löser CDCL und lokale Suche verbinden, steht in keiner der gelesenen Quellen und wird nicht behauptet; gezeigt sind zwei getrennte Verfahren.
- **Das Median-Verhältnis mischt Instanzmengen.** Jedes Verfahren hat seinen Median über die eigenen gelösten Fälle; bei n = 100 und 150 sind das dieselben Formeln, bei n = 300 nicht.
- **Ein Lauf ohne Lösung beweist nichts.** Bei 11 Formeln gelang nur ein Teil der drei Läufe; wie viele Läufe nötig sind, um eine erfüllbare Formel „fast sicher“ zu lösen, ist nicht gemessen.
- **Lateinische Quadrate sind nicht nachgerechnet.** Die Zeile ist eine eingefrorene Konstante der Vormessung mit anderer Instanzfamilie und anderem Parameter (cb = 2,06).
- **ε = 0,9** ist die Voreinstellung der Kern-Fassung; das Papier verwendet nach der Prüfung am Preprint ε = 1. Die Wirkung von ε ist nicht gemessen (die vorgerechneten Reihen stehen fest auf 0,9), ebenso nicht die von cb außer der Robustheitszeile 2,06 gegen 2,3.
- **Deutungen sind als solche gekennzeichnet.** Die Demo misst, wo welches Verfahren weniger zählt, nicht warum.

## Befunde und Korrekturen gegenüber dem Plan

- **Neue Formeln, neue Zahlen.** Der Plan nennt Zahlen der Vormessung (Python-`random`, 8 Formeln, ein Lauf je Formel); die Demo misst mit SplitMix64 neu, mit 12 Formeln und 3 Läufen je Formel. Plan bei n = 300, m/n = 4,0: probSAT löst 7 von 8, CDCL 2 von 8, rund 54-mal weniger Lesezugriffe; hier probSAT 12 von 12 Formeln (35 von 36 Läufen), CDCL 7 von 12, Verhältnis **33**. Bei n = 600 (4,0) reproduziert sich „probSAT alles, CDCL nichts“ (12 von 12 gegen 0 von 12). Bei n = 150 lösen beide dieselben Formeln, wie im Plan. Die Zahlen des Plans gelten als überholt.
- **Neu gegenüber dem Plan: n = 100.** Dort braucht probSAT bei m/n = 4,2 und 4,26 das 2,7- bzw. 2,2-Fache der Lesezugriffe von CDCL; die Kernbotschaft „der Vorsprung der lokalen Suche wird in den gemessenen Zellen mit wachsendem n größer“ bleibt, aber sie setzt erst ab n = 150 ein (n = 150: Faktor 2,6 / 5,5 / 1,8 statt 7,8 / 2,5 / 3,5 im Plan).
- **Die Verhältnisse bei n = 300 sind teils untere Schranken.** Bei 4,2 und 4,26 stammt der CDCL-Median aus je einem Fall (Plan: „nur 2 Werte“ bei 4,0); die App färbt diese Zellen gelb und nennt den Grund.
- **Struktur.** Rampen: CDCL 27.570,5 gegen probSAT 929.074 (Plan 21.054 gegen 1.080.892, Faktor 34 statt 51); probSAT löst 23 von 50 Läufen (Plan 34 von 50; hier 4 von 10 Graphen unerfüllbar, dort 2 von 10). Schur k = 4, n = 43: probSAT 3 von 20 Läufen (Plan 1 von 5). Schur k = 3, n = 13: 22.297 statt 36.767 Lesezugriffe, 20 von 20. Die Richtung des Plans reproduziert sich in allen drei Fällen.
- **Parameter.** cb = 2,3 wie im Plan; die Robustheitszeile cb = 2,06 gegen 2,3 reproduziert „der Befund ändert sich nicht“ (höchstens ein Lauf Unterschied in sechs Zellen). Der Plan nennt auch ε = 0,9 „nach Balint/Schöning“; das Papier verwendet nach der Prüfung am Preprint ε = 1, deshalb steht ε hier als Voreinstellung der Kern-Fassung.
- **Handbeispiel.** Stimmt mit der Handrechnung des Plans überein (Seed 20, 3 Umdrehungen, 32 / 44 / 54 Lesezugriffe, Modell 10000). **Abweichung vom Vertrag des Plans:** die verletzte Klausel wird aus der Liste der Kern-Kopie gezogen (Reihenfolge der Aufnahme, beim Entfernen rückt das letzte Element nach), nicht aus der nach Klauselnummer sortierten Liste. Im Handbeispiel steht in jedem Schritt genau eine Klausel in der Liste, die Werte sind gleich; bei mehreren verletzten Klauseln unterscheiden sich die Läufe beider Regeln. Die Schritt-für-Schritt-Ansicht zeigt die Liste in der Reihenfolge der Kern-Kopie, damit sie und die Messreihen denselben Lauf rechnen (`test_gleichlauf_mit_der_kern_kopie`).
- **Eingefrorene Zeile.** Lateinisches Quadrat 12 steht als Konstante der Vormessung (Quelle `out_v16_struktur.txt`), nicht als Messung dieser Demo.
- **Messreihe auf Knopfdruck.** Der Plan lässt n = 300 und 600 live oder eingefroren; sie sind eingefroren („vorgerechnet, nicht live“). Live rechnen Zufallsformeln n = 50 bis 150, Rampen bis 160 Aufträge und die zwei Schur-Instanzen; ein probSAT-Lauf je Formel mit dem Zufalls-Seed der Seitenleiste.
- **Aufnahme der Auswahlen in die Einstellungen.** Formel, Messzelle, Aufgabe und Fall stehen im Hauptbereich und sind trotzdem Teil der Presets und der Adresszeile; deshalb hebt auch ihre Änderung die Markierung des Presets auf.
- **Erklärtabelle** als Expander statt als Tab; **nicht aufgenommen:** die Aussage „moderne Löser kombinieren beides“ (nicht belegt).

## Verifikation

Die Suite hat 203 Tests (`pytest --collect-only -q tests`).

- **Kern** (`tests/test_algorithm.py`, 29 Tests): das Handbeispiel von Hand (neun Modelle, Zufallsstrom für Seed 20, Gewichte 1,2742 / 0,2285, Lesezugriffe 32 / 44 / 54, Modell 10000); je Umdrehung eine **Neuberechnung** der verletzten Klauseln, der Break-Werte und der Gewichte aus der Belegung (die Zähler der wahren Literale und die Liste der verletzten Klauseln stimmen nach jeder Umdrehung); Lesezugriffe aus den Vorkommen; Gleichlauf mit der Kern-Kopie; Determinismus; Gewichte monoton fallend in break; Auswahlhäufigkeit bei 100.000 Ziehungen innerhalb 1 % der Sollverteilung; Umnummerieren der Variablen; gemeldete Modelle erfüllen alle Klauseln, unerfüllbare Formeln werden nie gelöst.
- **Orakel** (`tests/test_oracle_lokale_suche_sat.py`, 31 Tests): Aufzählung aller 2^n Belegungen (n ≤ 12) für Modelle und Erfüllbarkeit gegen CDCL und probSAT; CDCL gegen OR-Tools CP-SAT auf 30 Zufallsformeln (`importorskip`); **probSAT gegen eine naive Neuberechnung** in 25 Läufen (gleiche Umdrehungen, Lesezugriffe und Modelle); Gewichte gegen numpy; Auswahlverteilung gegen `numpy.random.default_rng(...).choice`. Beim Bau lief dieselbe Prüfung als Scratch-Lauf mit 240 Zufallsformeln (n = 20 bis 68, m/n = 3,8 bis 4,5, davon 163 erfüllbar und 77 unerfüllbar): CDCL gegen CP-SAT, probSAT-Modelle gegen Modellprüfung und CP-SAT, probSAT gegen die naive Neuberechnung, Fehler 0 (Scratch-Lauf, nicht im Repo).
- **Kopien des Kerns** (`tests/test_kern_kopien.py`): wörtliche Kopie bis auf Kopfzeilen und Import, Kern-Version gegen `HASHES.txt` (läuft nur, solange der Planungsordner neben dem Repo liegt), Regression von SplitMix64 und Instanzerzeugern, CDCL-Einheiten, probSAT.
- **Randfälle** (`tests/test_edge_cases.py`): leere Formel, Einheitsklausel, Widerspruchspaar, Budget 0, n = 3, Startbelegung, Klauseln ohne doppelte Variable, Zahlenformate.
- **Zweige** (`tests/test_zweige.py`): cb, ε, Zufalls-Seed, Budget und Startbelegung ändern die Läufe; keine Nullspalte.
- **Verdikte** (`tests/test_verdicts.py`): reine Funktionen, jede Schwelle (Ampel gelb bei weniger als drei gelösten Fällen) und jede Zahl im Text an handgesetzten Zeilen; jedes Preset durchläuft jedes Verdikt (`tests/test_claims.py`).
- **Claims** (`tests/test_claims.py`, 31 Tests): die Zahlen der Tabelle „Befunde“ aus `lks_messungen.json`, dazu die Neumessung der Fälle des Experiments „Unerfüllbar“ und einer Formel mit n = 300. **Messdaten** (`tests/test_messungen.py`): Aufbau, probSAT löst nie eine von CDCL bewiesen unerfüllbare Formel, Neumessung einer Zelle und der Live-Funktionen gegen die Datei. Nicht in den Tests stehen die Zahlen der Gegenprobe, die Zeile zu lateinischen Quadraten (Konstante) und die Plan-Zahlen unter „Befunde und Korrekturen“.
- **Presets und Layout** (`tests/test_presets.py`, `tests/test_layout.py`): vollständig, erlaubte Werte, erstes Preset gleich Standardeinstellung, Permalink rastet ein, Schnellstart in der Seitenleiste, jede Änderung jedes Reglers (auch der Auswahlen im Hauptbereich) hebt die Hervorhebung auf.
- **Oberfläche** (`tests/test_app.py`, `tests/test_app_inhalt.py`, `tests/test_footer.py`, `tests/test_runtime_imports.py`): AppTest-Rauchtest (jeder Button einschließlich der Live-Messreihen, jeder Slider an Minimum und Maximum), Inhalt (Handbeispiel-Werte, jedes Preset, jeder Fall, Permalink), Footer, Laufzeit-Importe gegen `requirements.txt`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Schritt für Schritt, Kernfrage, Struktur, Unerfüllbar, Erklärtabelle, Grenzen, Mathematik |
| `lks_algorithm.py` | probSAT mit Spur und Verlauf, Gewichte, Aufzählung der Modelle |
| `lks_cdcl.py`, `lks_instanzen.py`, `lks_probsat.py`, `lks_rng.py` | wörtliche Kopien der Kern-Module (Herkunft und Kern-Version im Kopf) |
| `lks_constants.py` | Regler-Grenzen, Aufgaben, Fälle, Farben, Presets |
| `lks_evaluation.py` | Messreihen, Kennzahlen, Verdikte |
| `lks_layout.py` | Fester Kopf (Stylesheet) |
| `lks_live.py` | Live-Knöpfe: Zwischenspeicher (`st.cache_data`, je Einheit) und Fortschrittsanzeige (zählt die fertigen Einheiten) |
| `lks_messungen.json` | vorgerechnete Messreihen (je Formel CDCL und drei probSAT-Läufe) |
| `lks_presets.py` | Permalink (Einrasten), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `lks_scenario.py` | Handbeispiel, Formelfamilien |
| `lks_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur als Gegenprobe in den Tests) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tools/messungen.py` | Messskript der vorgerechneten Messreihen |
| `tools/gegenprobe.py`, `tools/gegenprobe_ausgabe.txt` | Gegenprobe mit anderen Formelmengen und ihre Ausgabe (nicht Teil der Tests) |
| `tests/` | Handrechnung, Orakel, Randfälle, Zweige, Verdikte, Claims, Messdaten, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Andere Verfahren der lokalen Suche** (WalkSAT-Varianten, Sparrow, Neustarts, Tabu): nur probSAT mit der polynomiellen Gewichtung.
- **Hybride** (CDCL mit Phasen aus lokaler Suche, Rephasing): nicht gemessen; ob moderne Löser beides verbinden, steht in keiner der gelesenen Quellen und wird nicht behauptet.
- **Zeitmessung und Löser in C:** die Demo zählt, sie misst keine Sekunden.
- **Lateinische Quadrate und Industrieinstanzen:** der Erzeuger für lateinische Quadrate liegt nicht in der Demo; sie erscheinen nur als eingefrorene Zeile der Vormessung.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, pandas und NumPy.

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).

# Recherche: Layout-Regeln für automatisch erzeugte Schaltpläne

**Zweck:** Datenlage für einen möglichen künftigen Auto-Layouter.
Gezogen aus vier Quellen-Welten: Normen, Praxis-Konventionen,
Layout-Algorithmik (EDA/Graphdrawing) und LLM-basierte Ansätze.
Stand: September 2026.

---

## 1. Die Normen-Welt (wie eine Schaltung auszusehen hat)

### DIN EN 61082 / IEC 61082-1:2014 — Darstellungsregeln für Schaltpläne

Die maßgebliche Norm für **Anordnung und Aufbau** (nicht Symboloptik — die
regelt DIN EN 60617). Die Teile 2–6 wurden in die 61082-1:2014 konsolidiert.

Kerninhalte laut Norm-Umfeld:
- Regeln für **strukturierte Erstellung** von Stromlaufplänen
- **Linienführung und Anschlussdarstellung**
- **Beschriftung und Identifikation** von Bauteilen
- Signalfluss **links nach rechts** bzw. oben nach unten
- Funktionsgruppen-Strukturierung (feinere Kennzeichnung: DIN EN 81346)

> Die Volltext-Norm ist kostenpflichtig; die wesentlichen konkreten Regeln
> sind über Lehrbücher und die Wikipedia-Ableitungen (unten) frei zugänglich.

### Stromlaufplan-Konventionen (de.wikipedia «Stromlaufplan», abgeleitet aus 61082)

**Aufgelöste Darstellung (Klassisches Steuerungs-Schaltschema):**
- Hauptleiter (Außen-/Neutralleiter) **horizontal am oberen und unteren Rand**
  über die ganze Zeichnung
- Einzelne Strompfade **senkrecht dazwischen**, **durchnummeriert**
  (Strompfadnummerierung → Referenzierbarkeit)
- Anordnung **strikt nach Stromdurchlauffolge** der Bauteile
- **Möglichst kreuzungsfrei** zeichnen; Pfade dürfen sich nicht überlappen
  (deshalb wird z. B. der PE-Leiter oft weggelassen)

**Funktionsgruppen:**
- Aufteilung in Sektionen nach Baugruppen (Motor-/Steuer-/Beleuchtungskreis)
- Verbindungen weit auseinander liegender Gruppen über **Referenzen**
  (alphanumerische Kennzeichen), **nicht** über gezeichnete Leitungen
- Prominente Potentiale bekommen Kennungen

**Beschriftung:**
- Jedes Bauteil: Gruppenzuordnung + Identifikationsnummer (R1, R2, …)
- Zusammengehörige Teile über Signalnamen verknüpfbar
- Dargestellt wird der **energielose/ausgeschaltete Zustand**

**Vereinfachungsformen** (für uns interessante Ideen):
- Übersichtsschaltplan: gleiche Parallelzweige zu einer eindimensionalen
  Darstellung mit Stranganzahl-Markierung zusammenfassen
- Blockschaltplan: Funktionsblöcke bündeln

### Leiterdiagramm / Ladder Diagram (IEC 61131-3, SPS-Welt)

- **Zwei vertikale Sammelschienen** (Power Rails) links/rechts
  (US: L1/L2, IEC: L+/M)
- **Horizontale Sprossen (Rungs)** zwischen den Rails
- „Energiefluss" konzeptionell **von links nach rechts** pro Sprosse
- Eingänge links, Ausgänge rechts in der Sprosse
- Parallelzweige = horizontale Aufzweigungen innerhalb einer Sprosse,
  Serienlogik = Aneinanderreihung in der Sprosse

**→ Für Prüfungs-Schaltungen (Serie/Parallel) ist genau dieses Rails-Rungs-**
**Muster das natürliche Grundgerüst — regulär, symmetrisch, selbsterklärend.**

---

## 2. Layout-Algorithmik (wie Programme das berechnen)

### ELK Layered / Sugiyama-Framework (via netlistsvg → elkjs)

netlistsvg (Open Source) zeichnet aus einer Yosys-Netzliste Schemata per
ELK-JavaScript-Port. Pipeline und Phasen:

1. **Netzliste → Graph:** Bauteile = Knoten, Netze = Kanten, **Pins = explizite
   Ports** an den Knoten (Ankerpunkte!)
2. **Layering:** Knoten werden horizontalen Schichten zugewiesen
   (links-nach-rechts-Fluss nach Abhängigkeit)
3. **Crossing Minimization:** Knoten innerhalb der Schichten umordnen,
   Kantenkreuzungen minimieren (Barycenter/Median-Heuristik, Sweeps)
4. **Node Placement:** exakte Koordinaten in den Schichten
5. **Orthogonales Edge Routing:** rechtwinklige Leitungsführung zu den Ports

Stärken für uns: Ports als Anker (entspricht unseren Polen/Trennpunkten!),
orthogonale Kanten, hierarchische/verbundene Graphen.

### «Weave»: Verified Netlist-to-Schematic (arXiv 2607.03835, 2026)

Aktuelles Paper (LTspice-Ausgabe, formal verifiziert). Konkrete Regeln:

**Anordnung**
- Spalten folgen **links-nach-rechts-Signalfluss**
- Vertikale Ordnung per Barycenter-Regel
- **Symmetrische Paare werden gespiegelt** platziert (Arsintescu-Ansatz)
- Funktionsblöcke: inkrementelle Platzierung entlang der Flussrichtung
- Knotenboxen = Symbolkörper **plus Reserve** für Pin-Ausleitungen
  (→ garantiert überlappungsfrei)

**Leitungen**
- Orthogonales Routing gemeinsam mit der Platzierung
- **Minimierungsziele: Kreuzungen, Biegungen, Leitungslänge**
- Masse/Versorgung als **Flags statt gezeichnete Leitungen**
  (entlastet den Graphen, hält Struktur lesbar)
- Klassische Router: Maze-Search, A*, Pattern-Routing, Rectilinear Steiner
  Trees für Multi-Terminal-Netze

**Raster & Abstände**
- **Grid-Snap alles** (dort 16 Einheiten) — Ports exakt auf Grid
- «Safe Mode»: verbreiterter Kanalabstand als konservativste Fallback-Stufe
- Bewertungsmetriken: GED, MSSIM, AEM (gegen Designer-Urteil kalibriert)

**Warnung des Papers:** Ästhetik ist NICHT das Optimierungsziel von Weave —
Priorität ist verifizierte Konnektivität. Für uns umgekehrt: Unsere Topologie
kommt vom LLM (einfache Serie/Parallel), unser Fokus liegt auf Ästhetik.

### Ästhetik-Forschung (Purchase et al., Graphdrawing)

Die klassischen, durch Nutzerstudien validierten Ästhetik-Kriterien:
1. **Kreuzungen minimieren** (stärkster Lesbarkeitsfaktor)
2. **Biegungen minimieren** (orthogonale Kanten)
3. **Leitungslänge/kantengesamtlänge minimieren**
4. **Fläche kompakt halten**
5. **Orthogonalität maximieren**
6. Symmetrie strukturwidrig (nur wo die Schaltung symmetrisch ist!)

---

## 3. LLM-basierte Ansätze (EEschematic, 2025)

MLLM-Agent (Gemini), SPICE-Netzliste → analoger Schaltplan. Relevante Lehren:

- **Kein One-Shot:** iteratives Verfeinern mit **visuellem Feedback** ist der
  Kern (rendern → Bild bewerten lassen → korrigieren)
- **Dual darstellen:** JSON (prüfbar) UND gerendertes Bild (bewertbar)
- **Few-Shot-Substrukturen:** kanonische Bausteine mit Platzierungs-/
  Orientierungsregeln als Referenz — Layout nicht dem Zufall überlassen
- **Deterministisches algorithmisch, LLM für Bewertung/Korrektur** —
  Verdrahtung durch eigenen Algorithmus
- Symmetrie, Kompaktheit, räumliche Regelmäßigkeit als explizite Kriterien
- Grenzen: komplexe Schaltungen erreichen deutlich schlechtere Ästhetik-Scores

**→ Bestätigt unsere Architektur-Entscheidung:** LLM liefert nur Topologie,
deterministischer Layouter die Geometrie. Optional später eine
Render-Feedback-Schleife als Qualitäts-Check.

---

## 4. Destillierter Regelkatalog für unseren Layouter

Abgeleitet aus allen Quellen, gemappt auf unsere Code-Basis
(20-px-Raster, 80-px-Polabstand, Origin am Pol, Trennpunkte in JSON):

### A. Grundgerüst (Struktur)
| Regel | Quelle |
|---|---|
| R1 Leiterdiagramm-Grundmuster: 2 Sammelschienen, Zweige dazwischen | IEC 61131 / 61082 |
| R2 Haupt-/Signalpfad links nach rechts | 61082, Weave, ELK |
| R3 Reihen-Kette: Pole auf 80-px-Vielfache → lückenlose gerade Kette | eigene Geometrie |
| R4 Parallelzweige: vertikal bündig zwischen gemeinsamen Knoten, gleicher horizontaler Abstand (Slot-Raster à 80 px + Leitungszwischenraum) | Ladder/61082 |
| R5 Strompfadnummerierung der Zweige (Beschriftung/Referenz) | 61082 Praxis |
| R6 Funktionsgruppen räumlich gruppieren; Trennung ggf. durch Abstand | 61082 |

### B. Platzierung
| Regel | Quelle |
|---|---|
| P1 Alle Positionen aufs 20-px-Raster snappen, Pole auf 80-px-Raster | Weave (Grid-Snap) |
| P2 Batterie/Quelle links (bzw. als linke Ader), Schalter früh im Pfad, Verbraucher rechts | 61082 Praxis |
| P3 Symmetrische Schaltungsteile gespiegelt/gespaltensymmetrisch platzieren | Weave/Arsintescu |
| P4 Bauteil-Reservebox: Symbolkörper + Platz für Labels/Ausleitungen, keine Überlappung | Weave |
| P5 Gesamtbild am Ende zentrieren (Balancierung) | Purchase/Ästhetik |

### C. Leitungen
| Regel | Quelle |
|---|---|
| L1 Ausschließlich orthogonal (Manhattan), nie diagonal | alle |
| L2 Kreuzungen minimieren (Zweig-Reihenfolge per Barycenter) | Purchase/ELK |
| L3 Biegungen minimieren; maximal 1 Biegung pro Verbindung anstreben | Purchase/Weave |
| L4 Keine Leitungen durch Symbole hindurch | Praxis |
| L5 GND/V+ als Flag/Symbol statt langer Rückleiter (optional) | Weave |
| L6 Gleiche Leitungsabstände zwischen Parallelzweigen (Slot-Raster) | Ladder |

### D. Beschriftung
| Regel | Quelle |
|---|---|
| B1 Labels an den Standard-Platzhalterpositionen der Symbole (bereits in JSON definiert) | eigene Basis |
| B2 Konsistentes Benennungsschema R1, R2… pro Gruppe | 61082/81346 |
| B3 Werte (4,7 kΩ, 12 V) unter/hinter dem Namen, einheitlich | Praxis |
| B4 Überlappungs-Check Labels ↔ Symbole/Leitungen | Weave (Reservebox) |

### E. Bewertung (automatisierbare Qualitätsmetriken)
- Anzahl Kreuzungen = 0 (bei Serie/Parallel erreichbar)
- Anzahl Biegungen minimal
- Alle Reihen-Knoten einer Kette identische y-Koordinate (Test!)
- Alle Parallelzweige identischer horizontaler Abstand (Test!)
- Alles auf Raster (Test!)
- Bounding-Box zentriert, Verhältnis ausgewogen

---

## 5. Architektur-Folgerungen (wo welche Logik liegt)

1. **Layouter-Algorithmus** (R1–R6, P1–P5, L1–L6): Code, `core/layout.py`,
   rein deterministisch, mit E-Regeln als Unit-Tests abgesichert
2. **Zeichnerische Präferenzen** (Slot-Breite, Rails-Ausrichtung, Label-Abstände,
   Batterie-Positionierung): Konfiguration (`layout_rules.json`)
3. **Symbol-Optik**: bleibt in `symbols/*.symbol.json` (Status quo)
4. **LLM (später)**: liefert nur Topologie/Netzliste + Werte; optional
   Render-Feedback-Schleife nach EEschematic-Vorbild als Qualitäts-Check

## 6. Quellen

- [IEC 61082-1:2014 (Preview)](https://standards.iteh.ai/catalog/standards/iec/129a81b3-4c7b-4bd9-92c1-2e90fd482ca2/iec-61082-1-2014)
- [IEC: Graphics & Figures Empfehlung](https://www.iec.ch/standards-development/graphics-figures)
- [Normen-Überblick smartengineers.com](https://smartengineers.com/normen-standards-schaltplaene-60617-61082/)
- [Wikipedia: Stromlaufplan](https://de.wikipedia.org/wiki/Stromlaufplan)
- [Wikipedia: Schaltzeichen (DIN EN 60617)](https://de.wikipedia.org/wiki/Schaltzeichen)
- [netlistsvg (GitHub)](https://github.com/nturley/netlistsvg) ·
  [elkjs](https://github.com/kieler/elkjs) ·
  [ELK Layered Referenz](https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html) ·
  [ELK Layered Blog 2025](https://eclipse.dev/elk/blog/posts/2025/25-08-21-layered.html) ·
  [netlistsvg Observable-Erklärung](https://old.observablehq.com/@nturley/netlistsvg-how-to-draw-a-better-schematic-than-graphviz-par/2)
- [Weave: Verified Netlist-to-Schematic (arXiv 2607.03835)](https://arxiv.org/html/2607.03835v1)
- [Automatic Analog Schematic Diagram Generation (ACM 2022)](https://dl.acm.org/doi/10.1145/3551901.3556486)
- [EEschematic (Emergent Mind)](https://www.emergentmind.com/topics/eeschematic)
- [Purchase: Metrics for Graph Drawing Aesthetics](https://www.semanticscholar.org/paper/Metrics-for-Graph-Drawing-Aesthetics-Purchase/be7e4c447ea27e0891397ae36d8957d3cbcea613)
- [Ladder-Diagramm-Grundlagen (PLCTalk)](https://www.plctalk.net/technical-articles/understanding-ladder-diagram/) ·
  [Schneider Electric: Ladder Logic](https://blog.se.com/industry/machine-and-process-management/2022/08/05/ladder-logic-programming-a-detailed-insight/)

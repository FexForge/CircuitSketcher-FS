# SchaltungsZeichner – Funktionsübersicht

## 1. Zeichenfläche

- Unendliche Arbeitsfläche (-5000 … +5000 in beiden Achsen), Raster 20 px
- Magnetisches Snapping: alle Bauteile, Leitungs-Endpunkte und Vorschauen rasten am Raster
- Pan mit mittlerer Maustaste, Zoom mit dem Mausrad (0,1× … 10×)
- Raster per Checkbox in der Toolbar ein-/ausblendbar
- Antialiasing und hardwarebeschleunigtes Rendering

## 2. Symbol-Bibliothek (datengetrieben)

Bauteile sind **keine** hartcodierten Klassen, sondern JSON-Definitionen unter
`symbols/*.symbol.json`. Beim Start lädt `src/symbols/library.py` alle Dateien,
validiert sie und gruppiert sie in der Palette nach Kategorie.

Derzeit enthalten (18 Symbole):

| Kategorie | Symbole |
|---|---|
| Energiequellen | Batterie |
| Passive Bauteile | Widerstand, Spule, Kondensator, Sicherung |
| Halbleiter | Diode, LED |
| Verbraucher | Lampe, Motor |
| Messgeräte | Voltmeter, Amperemeter (das Symbol „Strom" ist als Durchführung ausgeblendet — `hidden: true`; Messwerte setzt man über die Werkzeuge *Spannung*/*Strom*) |
| Steuerung | Schalter, Schalter Öffner/Schließer, Taster Öffner/Schlieesser |
| Sonstiges | Erde (1-polig; trennt keine Leitung, dient als Andockpunkt) |

Jedes Symbol definiert:
- zwei **Orientierungen** (horizontal/vertikal) mit eigener Zeichnung,
- **Platzhalter** (z. B. `name`, `resistance`, `voltage`, `current`) mit Position & Ausrichtung,
- optionale **Verbindungspunkte**,
- `bounds` (Begrenzungsrechteck) und `origin` (Dreh-/Positionierungsmittelpunkt),
- `default_values` für die Platzhalter.

Neue Symbole werden über den integrierten **Symbol-Editor** erstellt (kein Code nötig).

## 3. Bauteil-Operationen

- **Platzieren** mit halbtransparenter Vorschau, die der Maus folgt — beim
  Verlassen des Zeichenbereichs wird die Vorschau ausgeblendet (platzierte
  Bauteile und eine laufende Leitungszeichnung bleiben unberührt)
- **4-stufige Rotation**: 0° → 90° → 180° → 270° → 0°
  (Rechtsklick auf Vorschau oder auf gesetztes Bauteil → *Drehen*)
- **Skalieren** (Vergrößern ×1,2 / Verkleinern ×0,8) über das Kontextmenü
- **Verschieben** per Drag mit Raster-Snapping
- **Zweistufige Klick-Logik auf Beschriftungen:** Solange ein Bauteil *nicht*
  ausgewählt ist, fällt der Klick durch den Platzhalter-Text hindurch auf das
  Bauteil (auswählen/verschieben — auch auf Symbole, deren Beschriftung auf dem
  Körper sitzt, z. B. Messgeräte). Erst bei bereits ausgewähltem Bauteil lässt
  sich die Beschriftung selbst greifen und feinpositionieren.
- **Griffpunkte an Beschriftungen:** Bei Auswahl eines Bauteils erscheinen an
  allen Platzhalter-Texten kleine Griffpunkte (weiße Kreise, zoomunabhängig) —
  daran lässt sich der Text greifen und frei verschieben, ohne das Bauteil zu
  bewegen. Der Versatz wird wie beim direkten Ziehen gespeichert.
- **Kopieren/Einfügen/Duplizieren** (Ctrl+C/V/D): kopiert ausgewählte Bauteile
  und Leitungen — Leitungen, die an Polen ausgewählter Bauteile andocken,
  automatisch mit (Teilschaltungen bleiben verbunden). Einfügen landet versetzt
  nahe dem Original; Messwert-Annotationen werden mitkopiert.
- **Pfeiltasten-Feinverschiebung**: Pfeiltaste = 1 px (ohne Raster-Snap),
  Shift+Pfeiltaste = Rasterschritt.
- **Löschen** über Kontextmenü oder Entf-Taste
- **Eigenschaften** per Doppelklick (Platzhalter-Werte) oder direkter Doppelklick
  auf einen Platzhalter-Text

## 4. Leitungen

- Kontinuierliches Zeichnen: Jeder Klick beendet die aktuelle Leitung und
  startet die nächste sofort am Endpunkt (Linienzüge); **Rechtsklick oder ESC**
  beendet das Zeichnen (laufendes Segment wird verworfen, fertige bleiben)
- Live-Vorschau folgt der Maus und snappt ans Raster
- 4 vordefinierte Farben (Schwarz/Rot/Grün/Blau), über Toolbar-Dropdown wählbar
- Farbauswahl wirkt auf neue Leitungen und auf die aktuelle Auswahl
- Ausgewählte Leitungen erhalten blaue Highlight-Umrandung
- Leitungen sind verschieb- und löschbar
- **Enden-Griffpunkte**: Bei Auswahl erscheinen an beiden Enden Griffpunkte
  (weiße Kreise, zoomunabhängig). Ziehen verkürzt/verlängert die Leitung bzw.
  setzt das Ende neu — mit Raster-Snap und **magnetischem Andocken** am
  nächsten Bauteil-Pol. Undo-fähig.
- **Automatisches Aufteilen**: Wird ein 2-poliges Bauteil auf eine bestehende
  Leitung platziert oder gezogen, wird die Leitung an den
  beiden Polen des Bauteils getrennt und angedockt — **in allen drei
  Richtungen**: beim Platzieren auf einer Leitung, beim **Verschieben eines
  bestehenden Bauteils** auf eine Leitung (Andocken beim Loslassen) und beim
  **Ziehen einer neuen Leitung über ein bestehendes Bauteil** (Trennen an
  dessen Polen). **Überlappungs-Regel:** entscheidend ist, dass die Pole-
  Spanne des Bauteils die Leitung schneidet — es muss nicht die Bauteilmitte
  auf der Leitung liegen. Ragt nur eine Bauteilhälfte über den Anfang oder
  das Ende einer Leitung hinaus, wird die Leitung bis zum überdeckten Pol
  zurückgekürzt (statt gar nicht zu trennen). An einem Pol beginnende oder
  endende Leitungen gelten als bereits angeschlossen und werden nicht erneut
  getrennt; quer stehende Bauteile werden nicht angedockt (Hinweis in der
  Statusleiste) —
  **achsengerecht**: die
  neuen Leitungsenden werden senkrecht auf die bisherige Leitungslinie
  projiziert, dadurch bleiben Leitungen immer gerade (keine schrägen
  Anschlüsse, auch bei leicht asymmetrischen Symbolen). Gilt für alle
  2-poligen Symbole (Widerstand, Batterie, Lampe, Messgeräte, Schalter,
  Taster). **Quer zur Leitung stehende Bauteile werden nicht getrennt**
  (Hinweis in der Statusleiste: passend drehen).
  **Pole-Erkennung:** vorrangig die im Symbol-Editor gesetzten
  **Anschlusspunkte (Trennpunkte)** — `connection_points` in der
  Symboldefinition; alle mitgelieferten Symbole sind befüllt. Fehlen sie,
  schätzt das Programm die Pole (kleine Anschlusskreise r ≤ 6, sonst die
  äußeren Linien-Enden). Das Symbol „Strom" ist eine Durchführung und trennt
  nicht (dient aber als Andockpunkt für Leitungsenden).

## 5. Messwert-Annotationen (Spannung & Strom)

- Palette → Gruppe **Messwerte** mit den Werkzeugen **Spannung** und **Strom**
- **Spannungsbogen** (blau): Klick auf ein Bauteil setzt einen leicht
  gebogenen Bogen über das Bauteil; der Wert (z. B. „20 V", „15 mV",
  „10 kV") wird im Dialog abgefragt. **Doppelklick** ändert den Wert,
  **Ziehen** verschiebt den Bogen, **Rechtsklick** bietet Bearbeiten/Löschen.
- **Strompfeil** (rot): Klick auf eine Leitung setzt ein gefülltes Dreieck
  in Leitungsrichtung auf die Leitung; Wert z. B. „20 A", „15 mA", „10 kA".
  **Rechtsklick → „Richtung drehen"** dreht den Pfeil um 180°
  (links↔rechts, oben↔unten).
- **Spannungsbogen drehen**: Rechtsklick → „Richtung drehen" spiegelt den
  Bogen (Messpfeil am linken statt rechten Ende; Feld `flip` in der Datei).
- Beide Annotationen sind **Kind-Elemente** ihres Ziels: sie folgen beim
  Verschieben/Drehen und werden mitgelöscht; die Beschriftung bleibt
  aufrecht (Gegenrotation)
- Serialisierung: optionales Top-Level-Feld `annotations` (siehe
  Datei-Operationen); Undo/Redo deckt Platzieren, Verschieben, Ändern und
  Löschen ab

## 6. Undo / Redo

Vollständige, **snapshot-basierte** Undo/Redo-Funktion (Stack-Tiefe 50).
Rückgängig machbar sind:

- Bauteil platziert
- Leitung platziert
- Bauteil/Leitung verschoben
- Bauteil gedreht oder skaliert
- Bauteil-Eigenschaften/Platzhalter geändert
- Messwert-Annotation platziert, verschoben, geändert oder gelöscht
- Elemente gelöscht
- Zeichenfläche geleert
- Schaltung geladen

Bedienung: **Ctrl+Z** (Rückgängig), **Ctrl+Y** (Wiederherstellen).

## 7. Datei-Operationen

| Format | Export | Import | Hinweis |
|---|---|---|---|
| JSON | ✅ | ✅ | Voller Schaltungszustand (Komponenten + Leitungen + Messwerte) |
| PNG  | ✅ | – | Nur der aktuell sichtbare Ausschnitt |
| SVG  | ✅ | – | Komplette Szene als Vektorgrafik |

JSON-Struktur (Beispiel):

```json
{
  "version": "1.0",
  "components": [
    {
      "type": "symbol",
      "symbol_id": "resistor",
      "x": 100, "y": 200,
      "orientation": "horizontal",
      "rotation_step": 0,
      "scale_factor": 1.0,
      "placeholder_values": { "name": "R1", "resistance": "4,7 kΩ" }
    }
  ],
  "wires": [
    {
      "type": "wire",
      "start_x": 100, "start_y": 200,
      "end_x": 200, "end_y": 200,
      "color": [0, 0, 0]
    }
  ],
  "annotations": [
    { "type": "voltage", "component": 0, "x": 40.0, "y": -48.0, "value": "20 V" },
    { "type": "current", "wire": 0, "x": 150.0, "y": 200.0, "angle": 0.0, "value": "15 mA" }
  ]
}
```

> `rotation_step` kodiert die 4 Lagen (0=0°, 1=90°, 2=180°, 3=270°).
> `orientation` wird aus Gründen der Abwärtskompatibilität zusätzlich gespeichert.
> `annotations` ist optional und fehlt in älteren Dateien. Spannungs-Bögen
> referenzieren ihre Komponente per Index mit **lokalen** Koordinaten (relativ
> zum Bauteil), Strom-Pfeile ihre Leitung per Index mit **Szenen-Koordinaten**
> plus Winkel in Grad.

## 8. Symbol-Editor

Aufrufbar über **Werkzeuge → Symbol-Editor…**. Bietet:

- Feines Raster (20 px Major mit 10× Unterteilung = 2 px Minor)
- Werkzeuge: Linie, Kreis, Anschlusspunkt, Startpunkt (Origin),
  Platzhalter (Name/Spannung/Strom/Widerstand), Auswahl
- Pro Orientierung (horizontal/vertical) eigene Zeichnung
- Linienfarbe wählbar (auch für bestehende Auswahl)
- Öffnen/Speichern/Speichern unter, Änderungsmarker (`*`) im Titel
- Beim Schließen wird die Bibliothek automatisch neu geladen

## 9. Benutzeroberfläche

- **Menüleiste**: Datei, Bearbeiten, Werkzeuge, Hilfe
- **Toolbar**: Raster an/aus, Linienfarbe, Zoom (rein/raus/reset), Alles löschen
- **Linke Palette**: *Auswählen* als eigener Eintrag ganz oben, danach die
  nach Kategorien gruppierten Symbol-Buttons + Werkzeuge (*Leitung*) und
  *Messwerte* (*Spannung*, *Strom*). Versteckte Symbole (`hidden: true` in der
  Symbol-JSON) erscheinen nicht, bleiben aber für gespeicherte Dateien ladbar.
- **Statusleiste**: Kontextsensitive Meldungen (Modus, Platzierung, Rotation …)

## 10. Professionelle Ausstattung (v1.3)

- **Automatische Knotenpunkte**: An T- und X-Verzweigungen (drei oder mehr
  Leitungsrichtungen an einem Punkt, auch wenn eine Leitung den Punkt nur
  durchläuft) wird ein gefüllter Verbindungspunkt gezeichnet — Norm-Konvention:
  Punkt = verbunden, kein Punkt = kreuzung ohne Verbindung. Erkennung erfolgt
  live bei jedem Neuzeichnen; die Punkte erscheinen in der Ansicht und in
  PNG-/SVG-Export und beim Drucken.
- **A4-Blattrahmen mit Schriftfeld** (Ansicht → *A4-Blattrahmen*): A4 quer
  mit Innenrahmen und Titelblock (Titel, Fach/Thema, Name/Klasse, Datum) —
  editierbar über *Ansicht → Schriftfeld bearbeiten…*, wird mitgespeichert
  (`sheet`-Feld in der Datei) und mitgedruckt.
- **Drucken** (Datei → *Drucken…*, Ctrl+P): passt den Inhalt auf die Seite
  ein (inklusive Blattrahmen und Knotenpunkten).
- **Datei-Komfort**:
  - **Änderungsmarker** `*` im Fenstertitel bei ungespeicherten Änderungen;
    beim Beenden wird nachgefragt (Speichern/Verwerfen/Abbrechen).
  - **Zuletzt geöffnet**-Menü (bis 8 Einträge).
  - **Absturzsicherung**: alle 3 Minuten wird bei ungespeicherten Änderungen
    automatisch gesichert (Datei → *Absturzsicherung wiederherstellen…*).
  - **Doppelklick-Dateiendung**: `.sz` wird vom Installer registriert —
    Doppelklick öffnet die Schaltung direkt (auch `.sz.json`/`.json`).
  - **Beispieldateien** liegen unter `examples/` (Reihen- und
    Parallelschaltung mit Messwerten).
- **Rechtsklick auf Leitung**: *Farbe* (4 Presets, undo-fähig) und *Löschen*
  direkt am Objekt.

## 11. Funktionsschema-Simulation (nur in der FS-Variante)

- **Simulationsmodus** (Toolbar ▶/■/⟲, ESC beendet): Schalter/Taster per Klick
  bedienen — Lampen leuchten, Spulen ziehen an, geschlossene Kontakte zeigen
  eine Brücke, der Strompfad wird rot hervorgehoben.
- **Schienen L/N** (400 px) als Sammelleiter; T-Andocken wie bei Leitungen.
- **Relais-Logik**: Kontakte folgen der Spule mit gleichem Namen (K1 …);
  **Selbsthaltung** wird korrekt ausgewertet (Fixpunkt-Löser).
- **Zeitrelais**: anzugs-/abfallverzögerte Kontakte, Verzögerung einstellbar
  (Takt 10 Hz).
- **Kontakt-Spiegel als Element** (Palette): pro Relais platzierbar — zeigt
  Art, Position und aktuelle Stellung aller zugeordneten Kontakte, live
  während der Simulation (Spulenzustand im Kopf, grün = geschlossen).
  Rechtsklick: Relais zuweisen; wird mit der Datei gespeichert. Der
  **Toolbar-Button 🪞** öffnet zusätzlich die Gesamtübersicht als Dialog.
- **Symbole in Ruhelage**: Schalter/Taster/Kontakte sind stromlos gezeichnet —
  Schliesser ruht offen (Hebel abgehoben), Öffner ruht geschlossen (Hebel
  liegt auf); erst bei Betätigung/Anzug kehrt sich die Stellung um.
- **Motor mit Richtungsanzeige**: Platzhalter «direction» (rechts/links),
  Richtungspfeil-Overlay im Lauf.
- **Messgeräte mit realen Werten**: Ohm'sche Netzwerke (Batterie + Widerstände)
  werden numerisch gelöst (Knotenpotenzialanalyse); Volt-/Amperemeter zeigen
  echte Werte inkl. automatischer Einheit (mA/mV …), sonst «—».
- **Leitung nach Platzierung** (Ansicht-Menü, Standard an): nach dem Platzieren
  startet die nächste Leitung automatisch am nächsten Pol.

## Technische Details

- **Framework**: PyQt5 (≥ 5.15.0)
- **Rendering**: QGraphicsView / QGraphicsScene, QPainter
- **Python**: 3.8+ empfohlen
- **Symbol-Format**: JSON (`*.symbol.json`)

## Was bewusst *nicht* enthalten ist

- **Keine Simulation**: Das Programm berechnet keine Ströme/Spannungen; es ist
  ein reines Zeichenwerkzeug.
- **Kein Auto-Routing** für Leitungen (punktuell, gerade Linien).
- **Keine Verbindungspunkt-Logik in den aktuellen Symbolen** (die Mechanik
  existiert im Code, ist aber in den JSON-Definitionen deaktiviert).

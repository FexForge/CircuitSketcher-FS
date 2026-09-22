# SchaltungsZeichner FS (CircuitSketcher-FS)

**[Deutsch](#deutsch)** | **[English](#english)**

---

<a name="deutsch"></a>

## Deutsch

Funktionsschema-Variante des SchaltungsZeichners: Zeichnen **und**
interaktiv simulieren. Geschrieben in Python mit PyQt5.

> Das Basis-Zeichenprogramm liegt in
> [CircuitSketcher](https://github.com/FexForge/CircuitSketcher); dieses Repo
> ergänzt den Funktionsschema-Simulator.

### Funktionen

**Zeichnen** — alles aus dem Basis-Programm:
- Rasterbasierte, unendliche Zeichenfläche (20 px-Raster) mit magnetischem Snapping
- Datengetriebene Symbol-Bibliothek (`symbols/*.symbol.json`) + grafischer Symbol-Editor
- 4-stufige Rotation, Skalieren, Verschieben, mehrfarbige Leitungen
- Bearbeitbare Platzhalter pro Bauteil, Undo/Redo, JSON speichern/laden, PNG/SVG-Export

**Simulieren** (Toolbar ▶ / ■ / ⟲):
- Schalter und Taster per Klick bedienen — mehrfach, auch während der Simulation
- **Relais-Logik**: Kontakte folgen der Spule mit gleichem Namen (K1, K2 …,
  Zeitrelais KT1 …); **Selbsthaltung** wird korrekt ausgewertet
- **Zeitrelais**: anzugs- und abfallverzögerte Kontakte, Verzögerung einstellbar
- Lampen leuchten, Motoren laufen mit Richtungspfeil, Strompfad rot hervorgehoben
- **Kontakt-Spiegel** als platzierbares Element: zeigt alle Kontakte eines
  Relais mit Art, Position und aktueller Stellung — live
- Schienen L (oben) / N (unten) mit Griffpunkten zum Verlängern/Verkürzen
- Volt-/Amperemeter mit realen DC-Werten, wenn das Netz berechenbar ist
- Symbole zeigen die **Ruhelage** (stromlos): Schliesser offen, Öffner geschlossen

### Installation & Start

```bash
pip install -r requirements.txt
python main.py [beispiel.sz.json]
```

### Fertige Builds

Die CI baut bei jedem Release-Tag automatisch **Windows-ZIP** und
**macOS-DMG** (Apple Silicon): siehe
[Releases](https://github.com/FexForge/CircuitSketcher-FS/releases).
Beispiel beim Start mitliefern: `examples/beispiel-funktionsschema-selbsthaltung.sz.json`
(EIN/AUS-Selbsthaltung mit Kontakt-Spiegel).

### Projektstruktur

```
main.py                  Einstiegspunkt
symbols/                 Symboldefinitionen (inkl. Relais-/Zeitkontakte, Schienen)
src/
├── canvas/              Zeichenfläche, Knotenpunkte, A4-Blatt
├── components/          Bauteile, Leitungen, Messwert-Annotationen,
│                        Kontakt-Spiegel (contact_mirror.py)
├── simulation/          Netzliste, Löser (Relais/Zeitrelais), DC-Messwerte,
│                        Simulations-Overlay
└── ui/                  Hauptfenster, Palette, Symbol-Editor
tests/                   25 Tests (Simulation, Serialisierung, Bedienung)
```

### Lizenz

Copyright (c) 2026 FexForge (<https://github.com/FexForge>)

Dieses Programm ist freie Software: Sie können es unter den Bedingungen der
**GNU General Public License Version 3** (wie von der Free Software Foundation
veröffentlicht) weitergeben und/oder modifizieren. Den vollständigen Lizenztext
siehe [LICENSE](LICENSE) bzw. <https://www.gnu.org/licenses/gpl-3.0.html>.

**Hinweis zur Lizenzwahl:** Diese Software nutzt [PyQt5](https://www.riverbankcomputing.com/software/pyqt/),
das unter der GPL v3 bzw. einer kommerziellen Riverbank-Lizenz steht. Die freie
Weitergabe dieser Anwendung setzt daher die GPL v3 voraus.

**Quellcode (GPL §6):** Der vollständige Quellcode ist öffentlich verfügbar auf
GitHub: <https://github.com/FexForge/CircuitSketcher-FS>. Probleme und Anfragen bitte als
[Issue](https://github.com/FexForge/CircuitSketcher-FS/issues) melden. Beim Weiterleiten
bitte die LICENSE-Datei mitbeigeben.

---

<a name="english"></a>

## English

Function-schema variant of SchaltungsZeichner: draw **and** interactively
simulate. Written in Python with PyQt5.

> The base drawing program lives in
> [CircuitSketcher](https://github.com/FexForge/CircuitSketcher); this repo
> adds the function-schema simulator.

### Features

**Drawing** — everything from the base program:
- Grid-based, infinite canvas (20 px grid) with magnetic snapping
- Data-driven symbol library (`symbols/*.symbol.json`) + graphical symbol editor
- 4-step rotation, scaling, moving, multi-colored wires
- Editable placeholders per component, undo/redo, JSON save/load, PNG/SVG export

**Simulating** (toolbar ▶ / ■ / ⟲):
- Click switches and pushbuttons to operate them — repeatedly, even during simulation
- **Relay logic**: contacts follow the coil with the same name (K1, K2 …,
  timing relays KT1 …); **latching** is evaluated correctly
- **Timing relays**: pickup- and dropout-delayed contacts, configurable delay
- Lamps light up, motors run with a direction arrow, the current path is highlighted in red
- **Contact mirror** as a placeable element: shows all contacts of one relay
  with type, position and current state — live
- Rails L (top) / N (bottom) with drag handles to lengthen/shorten
- Volt-/ammeters with real DC values whenever the network is solvable
- Symbols show the **rest position** (de-energized): NO contacts open, NC contacts closed

### Installation & Start

```bash
pip install -r requirements.txt
python main.py [example.sz.json]
```

### Ready-made Builds

The CI builds a **Windows ZIP** and a **macOS DMG** (Apple Silicon)
automatically on every release tag: see
[Releases](https://github.com/FexForge/CircuitSketcher-FS/releases).
Example to load at startup: `examples/beispiel-funktionsschema-selbsthaltung.sz.json`
(ON/OFF latching circuit with contact mirror).

### Project Structure

```
main.py                  Entry point
symbols/                 Symbol definitions (incl. relay/timing contacts, rails)
src/
├── canvas/              Canvas, junction dots, A4 sheet
├── components/          Components, wires, measurement annotations,
│                        contact mirror (contact_mirror.py)
├── simulation/          Netlist, solver (relays/timing), DC measurements,
│                        simulation overlay
└── ui/                  Main window, palette, symbol editor
tests/                   25 tests (simulation, serialization, interaction)
```

### License

Copyright (c) 2026 FexForge (<https://github.com/FexForge>)

This program is free software: you can redistribute it and/or modify it under
the terms of the **GNU General Public License Version 3** as published by the
Free Software Foundation. See [LICENSE](LICENSE) or
<https://www.gnu.org/licenses/gpl-3.0.html> for the full license text.

**License note:** This software uses [PyQt5](https://www.riverbankcomputing.com/software/pyqt/),
which is licensed under GPL v3 or a commercial Riverbank license. Free
redistribution of this application therefore requires GPL v3.

**Source code (GPL §6):** The complete source code is publicly available on
GitHub: <https://github.com/FexForge/CircuitSketcher-FS>. Please report problems
and questions as an [issue](https://github.com/FexForge/CircuitSketcher-FS/issues).
When sharing, please include the LICENSE file.

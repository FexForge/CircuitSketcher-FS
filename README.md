# SchaltungsZeichner (CircuitSketcher)

Ein visuelles Drag-and-Drop-Werkzeug zum Zeichnen elektrischer Schaltpläne,
geschrieben in Python mit PyQt5.

> Hinweis: Der interne Fenstertitel lautet „SchaltungsZeichner". CircuitSketcher
> ist der Projekt-/Verzeichnisname.

## Funktionen

- Rasterbasierte, unendliche Zeichenfläche (20 px-Raster) mit magnetischem Snapping
- Datengetriebene Symbol-Bibliothek: Bauteile werden aus `symbols/*.symbol.json` geladen
- Eigener grafischer Symbol-Editor zum Erstellen neuer Bauteile ohne Code-Änderung
- **4-stufige Rotation** (0° / 90° / 180° / 270°)
- Skalieren, Verschieben, Löschen von Bauteilen und Leitungen
- Leitungen in mehreren Farben zeichnen (Klick-Klick-Verfahren mit Live-Vorschau)
- Bearbeitbare Platzhalter pro Bauteil (Name, Spannung, Strom, Widerstand)
- **Undo/Redo** (snapshot-basiert, alle Aktionen)
- Speichern/Laden als JSON, Export als PNG und SVG
- Pan mit mittlerer Maustaste, Zoom mit dem Mausrad

## Installation

```bash
pip install -r requirements.txt
```

## Start

```bash
python main.py
```

## Setup.exe bauen (Windows, Inno Setup)

Ein Befehl erstellt die komplette Installer-Datei (benötigt einmalig
[Inno Setup](https://jrsoftware.org/isdl.php) auf dem Build-Rechner):

```bash
python make_release.py
```

Ergebnis: **`release/SchaltungsZeichner-Setup.exe`** — eine einzige Datei zum
Weitergeben. Der Empfänger führt sie per Doppelklick aus (deutscher Assistent,
Lizenzseite GPL, Installation pro Benutzer nach
`%LOCALAPPDATA%\Programs\SchaltungsZeichner`, **keine Admin-Rechte**,
optionale Desktop-Verknüpfung).

- Startmenü-Eintrag mit Icon, Eintrag unter „Apps & Features" inkl. Deinstaller
- **Symbole liegen als echte Dateien unter `<Programmordner>\symbols`** —
  Änderungen/Neue Symbole aus dem Symbol-Editor bleiben dauerhaft erhalten.
  **Updates überschreiben benutzerdefinierte Symbole nicht** (`onlyifdoesntexist`).
- Stille Installation/Deinstallation möglich:
  `SchaltungsZeichner-Setup.exe /VERYSILENT /DIR=...` bzw. `unins000.exe /VERYSILENT`
- Inno-Skript: `installer/setup.iss` (Onedir-Build via PyInstaller, EXE-Icon
  aus `assets/favicon.ico`)

> Hinweis: Der frühere Onefile-Build entpackte Symbole bei jedem Start in ein
> temporäres Verzeichnis — Änderungen gingen verloren. Der Onedir-Installer
> löst das; die Pfad-Logik (`src/symbols/library.py`) bevorzugt einen
> `symbols`-Ordner neben der EXE.

## Projektstruktur

```
main.py                  Einstiegspunkt
requirements.txt         Abhängigkeiten (PyQt5)
symbols/                 Symboldefinitionen (JSON, editierbar im Symbol-Editor)
src/
├── canvas/grid_canvas.py            QGraphicsView mit Raster, Pan, Zoom
├── components/
│   ├── base_component.py            Abstrakte Basisklasse + Platzhalter
│   ├── symbol_component.py          Aus JSON gerendertes Bauteil (4er-Rotation)
│   └── wire.py                      Verbindungslinie mit Farbauswahl
├── symbols/library.py               Lädt/validiert die *.symbol.json-Dateien
└── ui/
    ├── main_window.py               Hauptfenster, Menüs, Toolbar, Undo/Redo
    ├── component_toolbar.py         Dynamische Bauteil-Palette
    └── symbol_editor.py             Grafischer Editor für eigene Symbole
```

Siehe auch [FEATURES.md](FEATURES.md), [QUICKSTART.md](QUICKSTART.md),
[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) und
[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md).

## Lizenz

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

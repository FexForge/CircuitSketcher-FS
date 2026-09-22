# SchaltungsZeichner – Projektstruktur

## Verzeichnislayout

```
CircuitSketcher/
├── main.py                          Einstiegspunkt (QApplication + MainWindow)
├── requirements.txt                 Abhängigkeiten
├── README.md / FEATURES.md / …      Dokumentation
│
├── symbols/                         Symboldefinitionen (JSON, datengetrieben)
│   ├── resistor.symbol.json
│   ├── battery.symbol.json
│   ├── switch.symbol.json
│   ├── switch_normally_open.symbol.json
│   ├── switch_normally_closed.symbol.json
│   ├── pushbutton_normally_open.symbol.json
│   ├── pushbutton_normally_closed.symbol.json
│   ├── lamp.symbol.json
│   ├── ammeter.symbol.json
│   ├── voltmeter.symbol.json
│   └── Strom.symbol.json
│
└── src/
    ├── __init__.py
    ├── canvas/
    │   └── grid_canvas.py           QGraphicsView: Raster, Snapping, Pan, Zoom
    ├── components/
    │   ├── __init__.py
    │   ├── base_component.py        Abstrakte Basis, Platzhalter, Kontextmenü
    │   ├── symbol_component.py      JSON-gerendertes Bauteil, 4er-Rotation
    │   └── wire.py                  Verbindungslinie, Enden-Griffpunkte, Farben
    ├── symbols/
    │   ├── __init__.py              Re-Exports
    │   └── library.py               Loader + SymbolDefinition/OrientationData
    └── ui/
        ├── __init__.py
        ├── main_window.py           Hauptfenster, Menüs, Toolbar, Undo/Redo
        ├── component_toolbar.py     Dynamische Bauteil-Palette
        ├── symbol_editor.py         Grafischer Symbol-Editor (Dialog)
        └── about_dialog.py          Über-Dialog (Logo + E-Mail-Kontakt)

`assets/` – statische Ressourcen (z. Zt. `logo.png` für den Über-Dialog;
fehlt die Datei, läuft der Dialog ohne Logo).
```

## Modulbeschreibungen

### `main.py`
Erzeugt die `QApplication`, instanziiert `MainWindow` und tritt in die
Ereignisschleife ein.

### `src/canvas/grid_canvas.py` – `GridCanvas`
- `QGraphicsView` mit großzügiger `sceneRect` (-5000 … +5000)
- Zeichnet Major/Minor-Raster in `drawBackground()`
- `snap_to_grid(point, use_minor)` rundet auf Rasterpunkte
- Pan mit mittlerer Maustaste, Zoom mit Mausrad (begrenzt 0,1×–10×)
- Zoom/Reset-Helper, Sichtbarkeits- und Unterteilungs-Setter

### `src/symbols/library.py` – Symbol-Loader
- Liest alle `*.symbol.json` aus `symbols/`, sortiert nach Kategorie/Name
- `SymbolDefinition` (dataclass): id, name, category, default_values, orientations
- `OrientationData` (dataclass): items, placeholders, connection_points, bounds, origin
- Validierung: jede Definition muss `horizontal` **und** `vertical` enthalten;
  mindestens ein Zeichen-Item pro Orientierung
- Bounds/Origin werden automatisch abgeleitet, falls in JSON fehlend
- Gibt `(definitions, errors)` zurück – defekte Dateien verhindern den Start nicht

### `src/components/base_component.py` – `BaseComponent`
- Abstrakte `QGraphicsItem`-Basis für alle Bauteile
- Verwaltet `placeholder_items/values/configs` (editierbare Textknoten)
- `_PlaceholderTextItem`: Doppelklick-Editierung einzelner Platzhalter
- Raster-Snapping in `itemChange()`
- Kontextmenü: Drehen, Vergrößern/Verkleinern, Löschen
- `_push_undo_from_component()`: Brücke zur MainWindow für Undo-Snapshots
- `setRotation()` begrenzt auf Vielfache von 90° (0/90/180/270)

### `src/components/symbol_component.py` – `SymbolComponent`
- Konkrete Bauteile, gerendert aus einer `SymbolDefinition`
- **`rotation_step` (0–3)** steuert die 4 Lagen:
  gerade Schritte → horizontal-Orientierung, ungerade → vertical-Orientierung.
  Zusätzliches Qt-Rotation um 180° für Schritt 2/3 liefert alle 4 Ansichten.
- `apply_orientation()`: baut Render-Items, Bounds, Platzhalter auf
- `_apply_rotation_transform()` + `rotation_angle_deg` (Property)
- `paint()`: zeichnet Linien/Kreise mit optionaler Auswahl-Highlight

### `src/components/wire.py` – `Wire`
- `QGraphicsLineItem` mit eigener Farbe (4 Presets)
- `update_end_point()` für die Live-Vorschau beim Zeichnen
- Raster-Snapping, Auswahl-Highlight
- `color_rgb()` / `set_color()` für die Farbsteuerung aus der Toolbar

### `src/ui/main_window.py` – `MainWindow`
- Baut UI auf: Palette, Canvas, Menüleiste (Datei/Bearbeiten/Werkzeuge/Hilfe), Toolbar
- Erweitert die Scene-Mouse-Events (Placement, Wire-Drawing, Vorschau)
- **Undo/Redo** (snapshot-basiert):
  - `_capture_snapshot()` / `_restore_snapshot()` (JSON der Szene)
  - `_push_undo_snapshot()` vor jeder verändernden Aktion
  - `undo()` / `redo()` mit Stack-Tiefe 50
- Save/Load nutzt dieselben Snapshot-Helfer (konsistentes Format)
- Export PNG (nur sichtbarer Ausschnitt) / SVG (komplette Szene)
- Farbauswahl-Logik für Leitungen (inkl. Auswahl-Synchronisation)

### `src/ui/component_toolbar.py` – `ComponentToolbar`
- Erzeugt pro Kategorie eine `QGroupBox` mit Buttons
- Tooltips aus Name + Beschreibung + Dateiname
- Werkzeug-Gruppe (Leitung, Auswählen) fix am Ende
- Signal `component_selected(str)` an MainWindow

### `src/ui/symbol_editor.py` – `SymbolEditorDialog`
- Größtes Modul (~1300 Zeilen): eigener Mini-Editor mit feinem Raster
- Editierbare Elemente: `SymbolLineItem`, `SymbolCircleItem`,
  `SymbolPlaceholderItem`, `SymbolConnectionItem`, `SymbolAnchorItem`
- Tools: Auswahl, Linie, Kreis, Anschluss, Startpunkt, Platzhalter-Typen
- Pro Orientierung (horizontal/vertical) unabhängige Szene
- Serialisierung in dasselbe `*.symbol.json`-Format wie die Bibliothek
- Beim Schließen: Bibliothek wird in MainWindow neu geladen

## Symbol-JSON-Format

```jsonc
{
  "version": "1.0",
  "id": "resistor",                  // optional, fällt auf Dateiname zurück
  "name": "Widerstand",
  "category": "Passive Bauteile",
  "default_values": { "name": "R", "resistance": "1 kΩ" },
  "description": "Optionale Beschreibung",
  "orientations": {
    "horizontal": {
      "items": [
        { "type": "line", "start": [-20,-8], "end": [20,-8] },
        { "type": "circle", "center": [0,0], "radius": 4 }
        // optional: "color": [r,g,b] pro Item
      ],
      "placeholders": [
        { "type": "placeholder", "key": "name",
          "position": [0,-24], "alignment": "center" }
      ],
      "connection_points": [],       // [[x,y], …] – aktuell meist leer
      "bounds":  { "min": [-44,-24], "max": [44,24] },
      "origin":  [-40, 0]            // Rotations-/Platzierungsmittelpunkt
    },
    "vertical": { /* analog */ }
  }
}
```

`bounds` und `origin` können weggelassen werden – sie werden dann automatisch
aus den Items/Platzhaltern/Verbindungspunkten abgeleitet.

## Erweiterungspunkte

1. **Neues Symbol**: Symbol-Editor verwenden oder `*.symbol.json` händisch
   anlegen, Programm neu starten.
2. **Neue Platzhalter-Typen**: in `PLACEHOLDER_LABELS` (symbol_editor.py) und
   `PLACEHOLDER_PROMPTS` (base_component.py / symbol_component.py) ergänzen.
3. **Verbindungspunkt-Logik aktivieren**: in den Symbol-JSONs `connection_points`
   befüllen und in `wire.py`/`main_window.py` ein Attachment implementieren.
4. **Weitere Export-Formate**: neue Methode in `MainWindow` neben `export_png/svg`.

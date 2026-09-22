# SchaltungsZeichner – Implementierungsstand

Stand: August 2026. Dieses Dokument beschreibt den **tatsächlichen** Stand des
Codes (nicht eine alte Spezifikation).

## Status: voll funktionsfähig

Alle Kern-Features sind implementiert und per Smoke-Test verifiziert
(Programmstart headless, Symbol-Laden, Rotation, Undo/Redo, Snapshot-Roundtrip).

## Implementierte Anforderungen

### 1. Zeichenfläche ✅

| Anforderung | Status | Ort |
|---|---|---|
| Rasterbasierte Zeichenfläche | ✅ | `grid_canvas.py:55` (`drawBackground`) |
| Magnetisches Snapping | ✅ | `grid_canvas.py:95` (`snap_to_grid`), `base_component.py:185` (`itemChange`) |
| Unendliche Arbeitsfläche + Pan + Zoom | ✅ | `grid_canvas.py:38,134,175` |

### 2. Datengetriebene Symbol-Bibliothek ✅

| Anforderung | Status | Ort |
|---|---|---|
| Symbole aus JSON laden | ✅ | `library.py:54` (`load_symbol_definitions`) |
| Validierung (beide Orientierungen, Items) | ✅ | `library.py:102,126` |
| 11 fertige Symbole | ✅ | `symbols/*.symbol.json` |
| Dynamische Palette nach Kategorie | ✅ | `component_toolbar.py:47` (`set_symbols`) |

### 3. Bauteil-Operationen ✅

| Anforderung | Status | Hinweis |
|---|---|---|
| Platzieren mit Vorschau | ✅ | `main_window.py` (`canvas_mouse_move/press`) |
| **4-stufige Rotation** (0/90/180/270°) | ✅ | `symbol_component.py` (`rotation_step`) |
| Skalieren | ✅ | `base_component.py:96` (`scale_component`) |
| Verschieben mit Snapping | ✅ | `base_component.py:185` |
| Löschen | ✅ | Kontextmenü + Entf |
| Platzhalter bearbeiten | ✅ | Doppelklick / Doppelklick auf Text |

### 4. Leitungen ✅

| Anforderung | Status |
|---|---|
| Klick-Klick-Zeichnen mit Live-Vorschau | ✅ |
| Farbauswahl (4 Presets), auch für Auswahl | ✅ |
| Raster-Snapping, Auswahl-Highlight | ✅ |

### 5. Undo / Redo ✅ (snapshot-basiert)

| Anforderung | Status |
|---|---|
| Vollständige Undo/Redo für alle Aktionen | ✅ |
| Stack-Tiefe 50 | ✅ |
| Einbindung in Platzieren/Bewegen/Drehen/Skalieren/Löschen/Eigenschaften/Clear/Load | ✅ |
| Tastatur (Ctrl+Z / Ctrl+Y) | ✅ |

Implementierung in `main_window.py` über `_capture_snapshot` /
`_restore_snapshot` / `_push_undo_snapshot`. Komponentenseitiger Einstieg
über `BaseComponent._push_undo_from_component()`.

### 6. Datei-Operationen ✅

| Format | Export | Import |
|---|---|---|
| JSON (voller Zustand, inkl. `rotation_step` & `scale_factor`) | ✅ | ✅ |
| PNG (sichtbarer Ausschnitt) | ✅ | – |
| SVG (komplette Szene) | ✅ | – |

Save/Load nutzen dieselben Snapshot-Helfer wie Undo/Redo → konsistentes Format.
Alte Dateien ohne `rotation_step` werden aus `orientation` abgeleitet (abwärtskompatibel).

### 7. Symbol-Editor ✅

Vollständiger grafischer Editor unter **Werkzeuge → Symbol-Editor…**
(siehe [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)).

## Architektur

```
QGraphicsItem
└── BaseComponent                (abstrakt: Platzhalter, Snapping, Kontextmenü, Undo-Brücke)
    └── SymbolComponent          (JSON-gerendert, rotation_step 0–3)

QGraphicsLineItem
└── Wire                         (Farbe, Auswahl-Highlight)

QGraphicsView
└── GridCanvas                   (Raster, Pan, Zoom)
    └── QGraphicsScene           (Platzierung, Wire-Drawing, Vorschau)
        └── → MainWindow         (UI, Menüs, Toolbar, Undo/Redo, Export)

QDialog
└── SymbolEditorDialog           (eigener Editor für *.symbol.json)
```

## Cleanup-Historie (diese Sitzung)

- ✅ PyQt5 installiert (Programm ist jetzt startbar)
- ✅ 6 hartcodierte Komponenten-Dateien entfernt (`resistor.py`, `battery.py`,
  `switch.py`, `lamp.py`, `ammeter.py`, `voltmeter.py`) – waren ungenutzter Totcode
- ✅ Müll entfernt: `temp.tmp`, `1/2/3.json`, `1111.png`, `222.png`, `WELCOME.txt`
- ✅ 4-stufige Rotation implementiert (vorher nur horizontal/vertikal)
- ✅ Undo/Redo vollständig implementiert (vorher nur Stub)
- ✅ Alle 5 Dokumente an den tatsächlichen Code-Stand angepasst

## Bekannte Grenzen (keine Bugs)

- **Keine Simulation**: reines Zeichenwerkzeug, keine Strom-/Spannungsberechnung.
- **Kein Auto-Routing** für Leitungen (gerade, punkt-zu-punkt).
- **Verbindungspunkte in Symbolen leer**: Mechanik existiert, ist aber in den
  JSON-Definitionen nicht befüllt; Leitungen attachen nicht automatisch.
- **PNG-Export**: nur der aktuell sichtbare Ausschnitt (bewusste Designentscheidung).

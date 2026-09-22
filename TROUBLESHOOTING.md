# SchaltungsZeichner – Fehlersuche

## Programm startet nicht

**`ModuleNotFoundError: No module named 'PyQt5'`**
PyQt5 fehlt. Installieren:
```bash
pip install -r requirements.txt
```

**`python` öffnet den Microsoft Store**
Der `python`-Alias ist nicht konfiguriert. Stattdessen den echten Interpreter
nutzen, z. B.:
```bash
py main.py
# oder vollständiger Pfad, z. B.:
"C:\Users\<user>\AppData\Local\Programs\Python\Python312\python.exe" main.py
```

**Beim Start erscheinen „Symbol-Ladefehler" in der Statusleiste**
Eine `*.symbol.json` ist fehlerhaft. Details stehen in der Konsole
(`[Symbol-Ladefehler] <datei>: <meldung>`). Häufige Ursachen:
- Orientierung fehlt: jede Definition braucht `horizontal` **und** `vertical`.
- Orientierung ohne `items`.

Die fehlerhafte Datei blockiert nicht den Rest; alle gültigen Symbole werden
trotzdem geladen.

## Bauteile / Interaktion

**Bauteil lässt sich nicht platzieren**
- Zuerst in der linken Palette einen Bauteil-Button klicken (Statusleiste zeigt
  „…platzieren (aktuell N°)").
- Dann auf die **Zeichenfläche** klicken, nicht auf die Palette oder Toolbar.

**Vorschau dreht sich nicht**
- Rechtsklick erfolgt auf die **halbtransparente Vorschau**, nicht auf die
  leere Fläche. Es erscheint ein kleines Menü mit *Drehen (90°)*.

**Platzhalter-Texte fehlen**
- Doppelklick auf das Bauteil öffnet die Eingabedialoge. Leere Platzhalter
  zeigen `[Name]` / `[Spannung]` / … als Platzhaltertext.

**Leitungen lassen sich nicht zeichnen**
- In der Palette **Leitung** wählen (nicht *Auswählen*).
- Erster Klick = Start, zweiter Klick = Ende. Werkzeug bleibt aktiv.

**Leitungen greifen nicht an Bauteilen**
- Aktuelles Verhalten: Leitungen sind frei positionierbar und attachen nicht
  automatisch (Verbindungspunkte in den Symbolen sind leer). Siehe
  [IMPLEMENTATION_SUMMARY.md → Bekannte Grenzen](IMPLEMENTATION_SUMMARY.md).

## Undo / Redo

**Ctrl+Z zeigt „Nichts zum Rückgängigmachen"**
- Der Undo-Stack ist leer (Startzustand oder alle Aktionen schon rückgängig).
- Nach Neu/Laden/Clear wird der vorherige Zustand als einziger Eintrag abgelegt.

**Bewegung ist nicht rückgängig machbar**
- Bewegungen werden beim **Loslassen** der Maus aufgezeichnet. Falls eine
  Bewegung nicht undo-fähig war, war vermutlich kein Werkzeug im
  *Auswählen*-Modus aktiv.

## Dateien / Export

**PNG-Export zeigt nur einen Ausschnitt**
- Gewollt: PNG exportiert absichtlich nur den sichtbaren Bereich.
  Für die komplette Szene stattdessen **SVG exportieren** oder vorher
  herauszoomen.

**SVG ist riesig oder leer**
- SVG rendert die komplette `sceneRect` (-5000 … +5000). Vorher auf 100 % zoomen
  und den gewünschten Bereich zentrieren, oder ein paar Bauteile platzieren,
  damit die Szene sichtbaren Inhalt hat.

**Alte `.json`-Schaltungen laden, aber Bauteile haben falsche Drehung**
- Alte Dateien kennen kein `rotation_step`. Beim Laden wird die in `orientation`
  (horizontal/vertical) gespeicherte Ausrichtung verwendet; 180°/270°-Lagen aus
  alten Versionen gab es nicht. Einmal neu speichern, danach ist die Datei
  aktuell.

## Symbol-Editor

**Neues Symbol erscheint nicht in der Palette**
- Nach dem Speichern im Editor diesen **schließen** – erst dann lädt
  `MainWindow` die Bibliothek neu.
- Datei muss auf `*.symbol.json` enden und im `symbols/`-Verzeichnis liegen.

**Symbol-Editor meldet „Keine Zeichnung" beim Speichern**
- Mindestens eine Orientierung muss `items` enthalten. Leere Orientierungen
  werden beim Speichern automatisch übersprungen.

## Sonstiges

**Statusleiste ist leer / Meldung verschwindet zu schnell**
- Die Statusleiste zeigt nur die letzte Meldung. Viele Aktionen überschreiben
  sich gegenseitig; das ist normal.

**Leistung bei sehr vielen Bauteilen**
- Das Raster wird pro Viewport-Repaint gezeichnet. Bei extrem vielen Bauteilen
  kann das Snapping/Zeichnen spürbar werden. Raster über die Checkbox in der
  Toolbar deaktivieren hilft in der Regel.

Bei hartnäckigen Problemen: Programm von der Konsole starten
(`python main.py`), um evt. geworfene Exceptions zu sehen.

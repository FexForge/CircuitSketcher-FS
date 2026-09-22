# SchaltungsZeichner – Kurzanleitung

## Installation & Start

```bash
pip install -r requirements.txt
python main.py
```

## Erste Schaltung in 60 Sekunden

1. **Bauteil wählen**: In der linken Palette einen Button klicken (z. B. *Widerstand*).
2. **Rotieren (optional)**: Rechtsklick auf die halbtransparente Vorschau → *Drehen (90°)*.
   Schaltet durch 0° → 90° → 180° → 270°.
3. **Platzieren**: Linksklick auf die Zeichenfläche. Das Bauteil rastet am Raster ein.
4. **Verbinden**: In der Palette *Leitung* wählen → Startpunkt klicken → Endpunkt klicken.
5. **Beschriften**: Doppelklick auf das Bauteil öffnet die Eingabedialoge
   (Name, Widerstand, Spannung … je nach Symbol).
6. **Speichern**: Datei → Speichern (Ctrl+S) oder Export als PNG/SVG.

## Wichtige Interaktionen

| Aktion | Bedienung |
|---|---|
| Bauteil platzieren | Palette → Linksklick auf Canvas |
| Vorschau drehen | Rechtsklick auf Vorschau → *Drehen* |
| Bauteil drehen/skalieren/löschen | Rechtsklick auf gesetztes Bauteil |
| Leitung zeichnen | *Leitung*-Werkzeug → Start klicken → Ende klicken; **Rechtsklick oder ESC** beendet das Zeichnen |
| Leitungsfarbe wählen | Toolbar-Dropdown *Linienfarbe* (ändert auch Auswahl) |
| Spannung beschriften | Palette → *Messwerte* → *Spannung* → Bauteil anklicken, Wert eingeben (z. B. 20 V) — Doppelklick ändert später |
| Strom beschriften | Palette → *Messwerte* → *Strom* → Leitung anklicken, Wert eingeben (z. B. 15 mA) — Rechtsklick dreht die Richtung |
| Bewegen | *Auswählen*-Werkzeug → Bauteil/Leitung ziehen |
| Auswählen (mehrere) | *Auswählen*-Werkzeug → Gummiband aufziehen |
| Löschen | Auswahl → Entf |
| Ausschnitt verschieben (Pan) | Mittlere Maustaste ziehen |
| Zoomen | Mausrad |
| Rückgängig / Wiederherstellen | Ctrl+Z / Ctrl+Y |
| Kopieren / Einfügen / Duplizieren | Ctrl+C / Ctrl+V / Ctrl+D (Leitungen an Polen werden mitkopiert) |
| Feinverschieben | Pfeiltasten = 1 px, Shift+Pfeil = Rasterschritt |
| Drucken (A4 eingepasst) | Ctrl+P — Blattrahmen über *Ansicht → A4-Blattrahmen* |

## Tastenkürzel

| Kürzel | Funktion |
|---|---|
| Ctrl+N | Neu |
| Ctrl+O | Öffnen |
| Ctrl+S | Speichern |
| Ctrl+Z | Rückgängig |
| Ctrl+Y | Wiederherstellen |
| Entf | Auswahl löschen |
| **ESC** | **Auf Auswählen-Modus schalten** (bricht auch eine laufende Leitung ab) |

## Bauteil auf Leitung platzieren (automatisches Andocken)

Wird ein **2-poliges Bauteil** (Widerstand, Batterie, Lampe, Messgeräte,
Schalter, Taster) direkt auf eine bestehende **Leitung** gesetzt, wird die
Leitung automatisch an den beiden Polen **aufgeteilt**: der linke Teil dockt
an den Eingangspol, der rechte Teil an den Ausgangspol an. Farbe der Leitung
bleibt erhalten; die Statusleiste meldet „… N Leitung(en) aufgeteilt".

Dieselbe Trennung passiert auch, wenn ein **bestehendes Bauteil per Drag auf
eine Leitung** geschoben wird (Andocken beim Loslassen) oder wenn eine **neue
Leitung über ein bestehendes Bauteil** gezogen wird (Trennung an dessen
Polen).
Das Symbol **„Strom"** ist ausgenommen — es ist eine Durchführung und trennt
die Leitung nicht.

> Trefferzone: der Platzierungspunkt muss innerhalb eines Rasterabstands
> (20 px) auf der Leitung liegen — das deckt auch diagonale Leitungen ab.

## Leitungsenden mit Griffpunkten bearbeiten

Leitung **auswählen** (Auswahlmodus, Klick auf die Leitung) → an beiden Enden
erscheinen **Griffpunkte** (weiße Kreise). Diese lassen sich ziehen:

- **Ende verschieben**: Griffpunkt ziehen — die Leitung wird kürzer/länger
  bzw. aufs neue Ziel gezogen.
- **Einrasten**: das Ende rastet am Raster ein und dockt zusätzlich
  **magnetisch** am nächsten Bauteil-Pol (Anschlusskreis) an, wenn einer
  in der Nähe ist.
- Die Änderung ist **rückgängig** (Ctrl+Z) wie jede andere Aktion.

## Eigene Symbole erstellen

Werkzeuge → **Symbol-Editor…** öffnet einen vollwertigen grafischen Editor mit
feinem Raster. Dort lassen sich Linien, Kreise, Platzhalter und Anschlusspunkte
für beide Orientierungen (horizontal/vertikal) zeichnen. Gespeichert wird als
`<name>.symbol.json` im `symbols/`-Verzeichnis; beim Schließen des Editors wird
die Bibliothek automatisch neu geladen und das neue Bauteil erscheint in der Palette.

**Wichtig — Anschlusspunkte (Trennpunkte):** Mit dem Werkzeug *Anschluss
(Trennpunkt)* werden zwei Punkte auf der Symbol-Zeichnung gesetzt. Diese
definieren, **wo in der Schaltung Leitungen getrennt und das Bauteil angedockt
wird** (beim Platzieren auf eine Leitung) und **wo Leitungsenden magnetisch
einrasten**. Alle mitgelieferten Symbole sind bereits damit versehen. Fehlen die
Anschlüsse, schätzt das Programm die Pole (kleine Anschlusskreise bzw. äußere
Linien-Enden).

Details zur Symbol-Dateistruktur siehe [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

## Fehlersuche

Siehe [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

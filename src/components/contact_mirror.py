"""Kontaktspiegel als platzierbares Grafik-Element (Funktionsschema).

Zeigt für EIN Relais (Zuordnung über den Namen, z. B. "K1" — gleiche Logik
wie bei Relaiskontakten) alle zugeordneten Kontakte mit Art, Position und
aktueller Stellung. Während der Simulation schlägt der Spiegel live mit.
"""

from PyQt5.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QFont, QPen
from PyQt5.QtWidgets import QGraphicsItem, QMenu

from ..simulation.solver import CONTACTS, COIL_SYMBOLS

WIDTH = 200.0
HEADER_H = 30.0
ROW_H = 22.0
PAD = 8.0

FRAME = QColor(90, 96, 108)
HEADER_BG = QColor(232, 236, 243)
BODY_BG = QColor(252, 253, 255)
TEXT = QColor(30, 34, 40)
MUTED = QColor(120, 126, 136)
CLOSED = QColor(46, 160, 67)      # Kontakt geschlossen
OPEN_COLOR = QColor(176, 182, 192)  # Kontakt offen
COIL_ON = QColor(220, 53, 69)     # Spule angezogen


class ContactMirrorItem(QGraphicsItem):
    """Spiegel-Element: Kontakte eines Relais mit aktueller Stellung."""

    def __init__(self, relay_name, engine_provider=None, grid_size=20):
        super().__init__()
        self.relay_name = str(relay_name or "K1").strip() or "K1"
        self.engine_provider = engine_provider  # () -> SimEngine | None
        self.grid_size = int(grid_size)
        self.is_mirror = True
        self.setFlag(self.ItemIsMovable, True)
        self.setFlag(self.ItemIsSelectable, True)
        self.setZValue(60)

    # ------------------------------------------------------------------
    # Daten aus der Szene lesen
    # ------------------------------------------------------------------
    def _engine(self):
        if self.engine_provider is None:
            return None
        try:
            return self.engine_provider()
        except RuntimeError:
            return None

    def _coils_and_contacts(self):
        coils, contacts = [], []
        scene = self.scene()
        if scene is None:
            return coils, contacts
        for item in scene.items():
            sid = getattr(item, "symbol_id", "")
            if sid in COIL_SYMBOLS:
                coils.append(item)
            elif sid in CONTACTS:
                contacts.append(item)
        return coils, contacts

    def _relay_data(self):
        """(Spule|None, [(Art, Spalte, Zeile, geschlossen), ...])"""
        engine = self._engine()
        want = self.relay_name.strip()
        coils, contacts = self._coils_and_contacts()
        coil = None
        for c in coils:
            if str(c.placeholder_values.get("name", "")).strip() == want:
                coil = c
                break
        own = [c for c in contacts
               if str(c.placeholder_values.get("name", "")).strip() == want]
        own.sort(key=lambda c: (c.x(), c.y()))
        rows = []
        for c in own:
            is_no, timing = CONTACTS[c.symbol_id]
            kind = "Schliesser" if is_no else "Öffner"
            if timing == "pickup":
                kind += " (Anzug)"
            elif timing == "dropout":
                kind += " (Abfall)"
            col = int(round(c.x() / self.grid_size))
            row = int(round(c.y() / self.grid_size))
            if engine is not None:
                closed = bool(engine.contact_closed.get(c))
            else:
                closed = not is_no  # Ruhelage: Schliesser offen, Öffner zu
            rows.append((kind, col, row, closed))
        return coil, rows

    def _height(self):
        _, rows = self._relay_data()
        return HEADER_H + max(len(rows), 1) * ROW_H + PAD

    def refresh(self):
        """Nach Szenen-Änderungen (Zuweisung, Undo, Sim-Takt) neu zeichnen."""
        self.prepareGeometryChange()
        self.update()

    # ------------------------------------------------------------------
    # Zeichnen
    # ------------------------------------------------------------------
    def boundingRect(self):
        return QRectF(0.0, 0.0, WIDTH, self._height())

    def paint(self, painter, _option, _widget):
        try:
            self._paint(painter)
        except RuntimeError:
            pass  # C++-Objekt während der Simulation bereits gelöscht

    def _paint(self, painter):
        engine = self._engine()
        coil, rows = self._relay_data()
        height = self._height()
        selected = self.isSelected()

        painter.setPen(QPen(FRAME, 2 if selected else 1))
        painter.setBrush(QBrush(BODY_BG))
        painter.drawRoundedRect(QRectF(1.0, 1.0, WIDTH - 2.0, height - 2.0), 6, 6)

        # Kopfzeile: Name + Spulen-Zustand
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(HEADER_BG))
        painter.drawRoundedRect(QRectF(1.0, 1.0, WIDTH - 2.0, HEADER_H), 6, 6)
        painter.drawRect(QRectF(1.0, HEADER_H / 2.0, WIDTH - 2.0, HEADER_H / 2.0))

        painter.setPen(QPen(TEXT))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(QPointF(PAD, 19.0), self.relay_name)

        painter.setFont(QFont("Segoe UI", 8))
        header_right = WIDTH - PAD
        if coil is None:
            painter.setPen(QPen(MUTED))
            painter.drawText(QRectF(0, 4, header_right - 30, 20),
                             Qt.AlignRight, "kein Relais")
        elif engine is not None:
            if engine.coil_latched.get(self.relay_name.strip()):
                painter.setPen(QPen(COIL_ON))
                painter.drawText(QRectF(0, 4, header_right - 6, 20),
                                 Qt.AlignRight, "⚡ angezogen")
            else:
                painter.setPen(QPen(MUTED))
                painter.drawText(QRectF(0, 4, header_right - 6, 20),
                                 Qt.AlignRight, "abgefallen")
        else:
            delay = str(coil.placeholder_values.get("delay", "2 s"))
            label = ("Zeit " + delay if coil.symbol_id == "timer_coil"
                     else "Sofortrelais")
            painter.setPen(QPen(MUTED))
            painter.drawText(QRectF(0, 4, header_right - 6, 20),
                             Qt.AlignRight, label)

        # Kontaktzeilen
        painter.setFont(QFont("Segoe UI", 8))
        if not rows:
            painter.setPen(QPen(MUTED))
            painter.drawText(QRectF(PAD, HEADER_H, WIDTH - 2 * PAD, ROW_H),
                             Qt.AlignVCenter, "(keine Kontakte zugewiesen)")
            return
        for i, (kind, col, row, closed) in enumerate(rows):
            y = HEADER_H + i * ROW_H
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(CLOSED if closed else OPEN_COLOR))
            painter.drawRect(QRectF(PAD, y + (ROW_H - 10.0) / 2.0, 10.0, 10.0))
            painter.setPen(QPen(TEXT))
            painter.drawText(QPointF(PAD + 18.0, y + 15.0), kind)
            painter.setPen(QPen(MUTED))
            painter.drawText(QRectF(0, y, WIDTH - PAD, ROW_H),
                             Qt.AlignVCenter | Qt.AlignRight,
                             f"{col}/{row}")

    # ------------------------------------------------------------------
    # Bedienung
    # ------------------------------------------------------------------
    def _window(self):
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        return view.window() if view is not None else None

    def _mark_dirty(self):
        window = self._window()
        if window is not None:
            mark = getattr(window, "_mark_dirty", None)
            if callable(mark):
                mark()

    def _notify_mirrors(self):
        window = self._window()
        refresh = getattr(window, "refresh_mirrors", None)
        if callable(refresh):
            refresh()

    def mouseDoubleClickEvent(self, event):
        event.accept()
        # Dialog nicht im Maus-Dispatch öffnen (Absturzregel)
        QTimer.singleShot(0, self._edit_relay)

    def _edit_relay(self):
        from PyQt5.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self._window(), "Kontakt-Spiegel",
            "Relais (z. B. K1 oder KT1):", text=self.relay_name)
        if ok and text.strip():
            self.relay_name = text.strip()
            self.refresh()
            self._mark_dirty()
            self._notify_mirrors()

    def _set_relay(self, name):
        self.relay_name = str(name).strip() or self.relay_name
        self.refresh()
        self._mark_dirty()
        self._notify_mirrors()

    def contextMenuEvent(self, event):
        event.accept()
        screen_pos = event.screenPos()
        # Menü nicht im Maus-Dispatch öffnen
        QTimer.singleShot(0, lambda: self._open_menu(screen_pos))

    def _open_menu(self, screen_pos):
        from PyQt5.QtGui import QCursor
        menu = QMenu("Kontakt-Spiegel", self._window())
        assign = menu.addMenu("Relais zuweisen")
        coils, _contacts = self._coils_and_contacts()
        names = []
        for coil in coils:
            name = str(coil.placeholder_values.get("name", "")).strip()
            if name and name not in names:
                names.append(name)
        names.sort(key=lambda n: (len(n), n))
        if not names:
            assign.setEnabled(False)
        for name in names:
            assign.addAction(name, lambda checked=False, n=name: self._set_relay(n))
        menu.addAction("Umbenennen…", self._edit_relay)
        menu.addSeparator()
        menu.addAction("Löschen", self._delete)
        menu.exec_(QCursor.pos() if not screen_pos.isNull() else screen_pos)

    def _delete(self):
        window = self._window()
        if window is not None:
            push = getattr(window, "_push_undo_snapshot", None)
            if callable(push):
                push()
        scene = self.scene()
        if scene is not None:
            scene.removeItem(self)
        if window is not None:
            window._mark_dirty()

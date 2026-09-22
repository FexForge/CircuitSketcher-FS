"""A4-Blattrahmen mit Schriftfeld (Titelblock) als Szenen-Dekoration.

Optional einblendbar (Ansicht → A4-Blatt): A4 quer bei 4 px/mm (1188×840 px)
mit Innenrahmen und Schriftfeld unten rechts. Die Felder (Titel, Fach,
Datum, Name, Klasse, Punkte) werden über Ansicht → Schriftfeld bearbeiten…
gepflegt und gehören zum gespeicherten Dateiformat (Top-Level-Feld "sheet"),
sodass sie Drucken und Export überleben.

Wie die Knotenpunkte ist der Rahmen reine Dekoration: leere shape(), keine
Klick-Blockade, nicht selektierbar, nicht Teil der Bauteil-Logik.
"""
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem

# A4 quer: 297 x 210 mm bei 4 px/mm
SHEET_WIDTH = 1188.0
SHEET_HEIGHT = 840.0
MARGIN = 40.0
FRAME_COLOR = QColor(120, 120, 120)
FIELD_LINES = [
    # (Zeile im Block, Beschriftung, Schlüssel)
    (0, "Titel", "title"),
    (1, "Fach / Thema", "subject"),
    (2, "Name / Klasse", "name"),
    (3, "Datum / Punkte", "date"),
]

DEFAULT_SHEET_META = {
    "visible": False,
    "title": "",
    "subject": "",
    "name": "",
    "date": "",
}


class SheetFrameItem(QGraphicsItem):
    """Zeichnet Rahmen + Schriftfeld; Metadaten hält das MainWindow."""

    is_decoration = True

    BLOCK_WIDTH = 440.0
    BLOCK_HEIGHT = 112.0

    def __init__(self, get_meta):
        super().__init__()
        self.get_meta = get_meta  # Callable -> dict (Fenster-Status)
        self.setZValue(1)  # hinter Leitungen/Bauteilen
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        return QRectF(-MARGIN, -MARGIN,
                      SHEET_WIDTH + 2 * MARGIN, SHEET_HEIGHT + 2 * MARGIN)

    def shape(self):
        # Dekoration ohne Trefferfläche
        return QPainterPath()

    def paint(self, painter, option, widget):
        meta = self.get_meta() or {}
        pen = QPen(FRAME_COLOR, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        # Außenkante + Innenrahmen
        painter.drawRect(QRectF(0, 0, SHEET_WIDTH, SHEET_HEIGHT))
        inner = QRectF(MARGIN, MARGIN,
                       SHEET_WIDTH - 2 * MARGIN, SHEET_HEIGHT - 2 * MARGIN)
        painter.drawRect(inner)
        # Schriftfeld unten rechts im Innenrahmen
        block = QRectF(inner.right() - self.BLOCK_WIDTH,
                       inner.bottom() - self.BLOCK_HEIGHT,
                       self.BLOCK_WIDTH, self.BLOCK_HEIGHT)
        painter.drawRect(block)
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        for row in range(1, len(FIELD_LINES)):
            y = block.top() + row * self.BLOCK_HEIGHT / len(FIELD_LINES)
            painter.drawLine(QPointF(block.left(), y), QPointF(block.right(), y))
        painter.drawLine(QPointF(block.left() + 150, block.top()),
                         QPointF(block.left() + 150, block.bottom()))
        # Beschriftung + Werte
        font = painter.font()
        base_size = font.pointSize()
        for row, label, key in FIELD_LINES:
            y = block.top() + (row + 0.5) * self.BLOCK_HEIGHT / len(FIELD_LINES)
            small = painter.font()
            small.setPointSize(max(7, base_size - 2))
            painter.setFont(small)
            painter.drawText(QPointF(block.left() + 8, y - 4), label)
            painter.setFont(font)
            value = str(meta.get(key, "") or "")
            painter.drawText(QPointF(block.left() + 160, y + 6), value)

"""Automatische Knotenpunkte (Verzweigungspunkte) als Szenen-Dekoration.

Zeichnet gefüllte Punkte an Stellen, an denen sich drei oder mehr Leitungs-
richtungen treffen (T- und X-Verzweigungen) — die Norm-Konvention: Punkt =
elektrisch verbunden, kein Punkt = kreuzung ohne Verbindung. Die Punkte
werden zur Laufzeit aus den aktuellen Leitungen berechnet und erscheinen
damit auch in PNG-/SVG-Export (sie sind reguläre Szenen-Items).

Erkennung (pro Leitungsende):
- Richtungen aller Leitungen, die an diesem Punkt ENDEN, plus
- BEIDE Richtungen jeder Leitung, die den Punkt DURCHLÄUFT (innerhalb des
  Segments) — so entsteht der Punkt auch, wenn eine durchgehende Leitung
  an ihrer Mitte eine abzweigende Leitung erhält,
- ein Bauteil-Pol am Punkt zählt wie ein Leitungsende hinzu.

Ab drei Richtungen wird ein Knotenpunkt gezeichnet.
"""
import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem

from ..components.symbol_component import SymbolComponent
from ..components.wire import Wire


def _point_key(point):
    """Punkt auf 1-px-Raster quantisieren (Vergleich ohne Float-Rauschen)."""
    return (round(point.x()), round(point.y()))


def _direction_angle(start, end):
    delta = end - start
    if delta.isNull():
        return None
    # Auf 22.5°-Sektoren quantisieren: fast kollinear zählt als gleiche Richtung
    angle = math.degrees(math.atan2(delta.y(), delta.x()))
    return round(angle / 22.5) * 22.5


def _point_on_segment(point, start, end):
    """Liegt der Punkt (nahezu) AUF dem Segment — streng zwischen den Enden?"""
    seg = end - start
    seg_sq = seg.x() ** 2 + seg.y() ** 2
    if seg_sq == 0:
        return False
    t = ((point.x() - start.x()) * seg.x()
         + (point.y() - start.y()) * seg.y()) / seg_sq
    if t <= 0.001 or t >= 0.999:
        return False
    foot = QPointF(start.x() + t * seg.x(), start.y() + t * seg.y())
    return (point - foot).manhattanLength() <= 1.0


class JunctionDotsItem(QGraphicsItem):
    """Dekorations-Item: zeichnet bei jedem repaint die Knotenpunkte neu.

    `owner` ist das MainWindow (Zugriff auf temp_wire, um die Zeichen-Vorschau
    nicht mitzuzählen). shape() ist LEER — die Dekoration darf keine Klicks
    schlucken (trotz großem boundingRect).
    """

    is_decoration = True
    DOT_RADIUS = 3.4
    DOT_COLOR = QColor(20, 20, 20)

    def __init__(self, owner=None):
        super().__init__()
        self.owner = owner
        self.setZValue(15)  # über Leitungen, unter Griffpunkten (z=20)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        if self.scene() is None:
            return QRectF()
        return self.scene().sceneRect()

    def shape(self):
        # Dekoration: keine Trefferfläche (Standard-shape() = boundingRect
        # würde sonst die gesamte Zeichenfläche blockieren).
        return QPainterPath()

    def _active_wires(self):
        scene = self.scene()
        if scene is None:
            return []
        temp = getattr(self.owner, "temp_wire", None)
        return [
            w for w in scene.items()
            if isinstance(w, Wire) and w is not temp and w.line().length() > 0
        ]

    def junction_points(self):
        wires = self._active_wires()
        ends = []  # (Punkt, {Winkel})
        for wire in wires:
            start, end = wire.start_point, wire.end_point
            a1 = _direction_angle(start, end)
            a2 = _direction_angle(end, start)
            if a1 is not None:
                ends.append((start, {a1 % 360}))
            if a2 is not None:
                ends.append((end, {a2 % 360}))
        # Punkte zusammenfassen
        merged = {}
        for point, angles in ends:
            merged.setdefault(_point_key(point), set()).update(angles)
        # Durchlaufene Leitungen ergänzen beide Richtungen
        for key, angles in list(merged.items()):
            point = QPointF(key[0], key[1])
            for wire in wires:
                if _point_on_segment(point, wire.start_point, wire.end_point):
                    a1 = _direction_angle(wire.start_point, wire.end_point)
                    a2 = _direction_angle(wire.end_point, wire.start_point)
                    if a1 is not None:
                        angles.add(a1 % 360)
                    if a2 is not None:
                        angles.add(a2 % 360)
        # Bauteil-Pole zählen wie ein Leitungsende
        pin_keys = set()
        scene = self.scene()
        if scene is not None:
            for item in scene.items():
                if not isinstance(item, SymbolComponent):
                    continue
                getter = getattr(item, "get_pole_points", None)
                if not callable(getter):
                    continue
                for pole in getter():
                    pin_keys.add(_point_key(pole))
        dots = []
        for key, angles in merged.items():
            count = len(angles) + (1 if key in pin_keys else 0)
            if count >= 3:
                dots.append(QPointF(key[0], key[1]))
        return dots

    def paint(self, painter, option, widget):
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.DOT_COLOR))
        radius = self.DOT_RADIUS
        for point in self.junction_points():
            painter.drawEllipse(point, radius, radius)

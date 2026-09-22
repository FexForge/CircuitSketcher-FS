"""Simulations-Darstellung als Szenen-Dekoration.

Zeichnet ÜBER der Zeichnung (z=16, unter Griffpunkten):
- unter Strom stehende Leitungen (roter Strompfad)
- leuchtende Lampen (gelb gefüllt), laufende Motoren (Richtungspfeil)
- angezogene Spulen (grün markiert, Name hervorgehoben)
- geschlossene Kontakte: Brückenlinie zwischen den Polen
- Messwerte an Volt-/Amperemetern (reale Werte, '—' wenn nicht berechenbar)

shape() ist leer (Dekoration darf keine Klicks schlucken).
"""
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QPainterPath, QPen
from PyQt5.QtWidgets import QGraphicsItem

from .solver import MANUAL_SWITCHES

FLOW_COLOR = QColor(220, 53, 69, 170)
LAMP_COLOR = QColor(255, 215, 0, 200)
COIL_COLOR = QColor(40, 167, 69, 170)
BRIDGE_COLOR = QColor(40, 167, 69, 220)
MOTOR_COLOR = QColor(40, 167, 69, 220)
TEXT_COLOR = QColor(20, 20, 20)


class SimulationOverlayItem(QGraphicsItem):
    is_decoration = True

    def __init__(self, engine_provider, readings_provider=None):
        super().__init__()
        self.engine_provider = engine_provider
        self.readings_provider = readings_provider or (lambda: {})
        self.setZValue(16)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        if self.scene() is None:
            return QRectF()
        return self.scene().sceneRect()

    def shape(self):
        return QPainterPath()

    def paint(self, painter, option, widget):
        engine = self.engine_provider()
        if engine is None:
            return

        # Strompfad: unter Strom stehende Leitungen nachzeichnen
        pen = QPen(FLOW_COLOR, 5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        try:
            for wire in engine.net.wire_items():
                if engine.wire_energized(wire):
                    painter.drawLine(wire.start_point, wire.end_point)
        except RuntimeError:
            return  # Szene wurde während des Zeichnens verändert

        readings = self.readings_provider()
        for component in list(engine.net.pins):
            try:
                self._paint_component(painter, engine, component, readings)
            except RuntimeError:
                continue  # gelöschtes C++-Item: übergehen

    def _paint_component(self, painter, engine, component, readings):
        sid = getattr(component, "symbol_id", "")
        rect = component.mapRectToScene(component.boundingRect())
        center = rect.center()

        if sid == "lamp" and engine.active.get(component):
            radius = min(rect.width(), rect.height()) / 2.6
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(LAMP_COLOR))
            painter.drawEllipse(center, radius, radius)

        elif sid == "motor" and engine.active.get(component):
            self._paint_motor_arrow(painter, center, rect,
                                    component.placeholder_values.get("direction", "rechts"))

        elif sid in ("relay_coil", "timer_coil") and engine.active.get(component):
            painter.setPen(QPen(COIL_COLOR, 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect.adjusted(rect.width() * 0.25,
                                           rect.height() * 0.25,
                                           -rect.width() * 0.25,
                                           -rect.height() * 0.25))

        elif sid in ("relay_contact_no", "relay_contact_nc",
                     "timer_contact_pickup", "timer_contact_dropout"):
            if engine.contact_closed.get(component):
                self._paint_bridge(painter, component)
        elif sid in MANUAL_SWITCHES:
            # Schalter/Taster: Stellung sichtbar machen — geschlossene
            # Stellung bekommt eine Brücke (wie bei Relaiskontakten).
            if engine.manual.get(component, False):
                self._paint_bridge(painter, component)

        if component in readings:
            self._paint_reading(painter, rect, readings[component])

    def _paint_bridge(self, painter, component):
        poles = component.get_pole_points()
        if len(poles) == 2:
            painter.setPen(QPen(BRIDGE_COLOR, 4))
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(QPointF(poles[0]), QPointF(poles[1]))

    def _paint_motor_arrow(self, painter, center, rect, direction):
        """Kreisbogen-Pfeil um den Motor: rechtslaufend (im Uhrzeigersinn)
        oder linkslaufend (Richtung aus dem Platzhalter 'direction')."""
        radius = min(rect.width(), rect.height()) / 2.2
        clockwise = str(direction).strip().lower() not in ("links", "linkslauf", "ccw", "l")
        pen = QPen(MOTOR_COLOR, 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        start, span = (-60, 240) if clockwise else (240, -240)
        rectf = QRectF(center.x() - radius, center.y() - radius,
                       radius * 2, radius * 2)
        painter.drawArc(rectf, int(start * 16), int(span * 16))
        # Pfeilspitze am Bogenende
        end_angle = start + span
        rad = end_angle * 3.14159265 / 180.0
        tip = QPointF(center.x() + radius * __import__("math").cos(rad),
                      center.y() - radius * __import__("math").sin(rad))
        tangent = (-__import__("math").sin(rad), -__import__("math").cos(rad))
        if not clockwise:
            tangent = (-tangent[0], -tangent[1])
        size = 7.0
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(MOTOR_COLOR))
        import math as _m
        wing1 = QPointF(tip.x() - tangent[0] * size - (_m.cos(rad)) * size * 0.5,
                        tip.y() - tangent[1] * size + (_m.sin(rad)) * size * 0.5)
        wing2 = QPointF(tip.x() - tangent[0] * size + (_m.cos(rad)) * size * 0.5,
                        tip.y() - tangent[1] * size - (_m.sin(rad)) * size * 0.5)
        from PyQt5.QtGui import QPolygonF
        painter.drawPolygon(QPolygonF([tip, wing1, wing2]))

    def _paint_reading(self, painter, rect, text):
        painter.setPen(QPen(TEXT_COLOR))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(QPointF(rect.left(), rect.bottom() + 14), str(text))

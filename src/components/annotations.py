"""
Messwert-Annotationen: Spannungsbogen (blau) und Strompfeil (rot).

Beide sind Kind-Items ihres Zielelements (Bauteil bzw. Leitung) und folgen
damit automatisch beim Verschieben und werden mitgelöscht. Der Wert ist per
Doppelklick frei editierbar (z. B. "20 V", "15 mV", "10 kA").
"""
import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPen, QBrush, QPainterPath, QPolygonF, QPainterPathStroker
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem, QInputDialog, QMenu, QAction, QStyle

VOLTAGE_COLOR = QColor(0, 102, 204)
CURRENT_COLOR = QColor(220, 53, 69)

# Lokale Geometrie (Pixel, unskaliert)
ARC_HALF_WIDTH = 44    # Bogen spannt ±44 px (Passt zum 80-px-Polabstand + Luft)
ARC_HEIGHT = 14        # "Leicht gebogen": Scheitelhöhe des Bogens
ARC_BASE_OFFSET = 34   # Abstand Bogenenden über Bauteilmitte (y negativ = oben)
TRIANGLE_SIZE = 12     # Dreieckshalbe Breite/Höhe des Strompfeils
ARROW_LENGTH = 9       # Kleiner Pfeil am rechten Bogenende
ARROW_WIDTH = 3.5


class _AnnotationText(QGraphicsTextItem):
    """Wert-Text einer Annotation (Doppelklick = bearbeiten)."""

    def __init__(self, annotation, color):
        super().__init__(annotation)
        self.annotation = annotation
        self.setDefaultTextColor(color)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        # Ohne Text-Interaktion fallen Klicks durch den Text hindurch auf die
        # Annotation darunter (auswählen/verschieben); der Doppelklick wird
        # weiter unten abgefangen.
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    def mouseDoubleClickEvent(self, event):
        self.annotation.edit_value()
        event.accept()


class BaseAnnotation(QGraphicsItem):
    """Gemeinsame Basis: Wert, Textposition, Bearbeiten, Kontextmenü."""

    is_annotation = True

    def __init__(self, parent_item):
        super().__init__(parent_item)
        self.value = ""
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(8)
        self._press_pos = None
        self.text_item = _AnnotationText(self, self.text_color())
        self._update_text()

    # -- von Unterklassen ------------------------------------------------
    def text_color(self):
        raise NotImplementedError

    def text_anchor(self):
        """Szene-lokaler Ankerpunkt (relativ zum Annotation-Item) für den Text."""
        return QPointF(0, 0)

    # -- API ---------------------------------------------------------------
    def set_value(self, value):
        self.value = value or ""
        self._update_text()

    def edit_value(self):
        title, prompt = self.edit_prompt()
        self._request_undo()
        value, ok = QInputDialog.getText(None, title, prompt, text=self.value)
        if ok:
            self.set_value(value)

    def _request_undo(self):
        """Undo-Snapshot über das Hauptfenster des Zielelements anstossen."""
        target = self.parentItem()
        getter = getattr(target, "_push_undo_from_component", None)
        if callable(getter):
            getter()
        elif isinstance(target, QGraphicsItem) and target.scene() and target.scene().views():
            top = target.scene().views()[0].window()
            push = getattr(top, "_push_undo_snapshot", None)
            if callable(push):
                push()

    def _update_text(self):
        self.text_item.setPlainText(self.value)
        anchor = self.text_anchor()
        rect = self.text_item.boundingRect()
        self.text_item.setPos(anchor.x() - rect.width() / 2.0,
                              anchor.y() - rect.height() / 2.0)
        self.prepareGeometryChange()

    def keep_text_upright(self, angle):
        """Wert-Text gegen die Drehung des Zielelements rotieren."""
        self.text_item.setRotation(angle)

    # -- Auswahl & Ziehen --------------------------------------------------
    def mousePressEvent(self, event):
        self._press_pos = QPointF(self.pos())
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # Verschieben der Annotation ist undo-fähig: Snapshot erst am Ende
        # des Zugs (wie bei den Leitungsenden-Griffpunkten — niemals während
        # des Dispatchs serialisieren).
        if self._press_pos is not None and self.pos() != self._press_pos:
            self._request_undo()
        self._press_pos = None

    def _paint_selection_hint(self, painter, option):
        """Gestrichelter Rahmen, wenn die Annotation ausgewählt ist."""
        if option.state & QStyle.State_Selected:
            hint = QPen(QColor(120, 170, 255, 180), 1, Qt.DashLine)
            painter.setPen(hint)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect().adjusted(1, 1, -1, -1))

    def _text_hit_path(self):
        path = QPainterPath()
        path.addRect(QRectF(self.text_item.pos(), self.text_item.boundingRect().size()))
        return path

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_action = QAction("Wert bearbeiten", None)
        edit_action.triggered.connect(self.edit_value)
        menu.addAction(edit_action)
        self._extend_context_menu(menu)
        menu.addSeparator()
        delete_action = QAction("Löschen", None)
        delete_action.triggered.connect(self.delete_later)
        menu.addAction(delete_action)
        menu.exec_(event.screenPos())
        event.accept()

    def _extend_context_menu(self, menu):
        pass

    def delete_later(self):
        self._request_undo()
        if self.scene():
            # Sicherheitshalber erst aus Registry des Bauteils entfernen.
            parent = self.parentItem()
            registry = getattr(parent, "annotations", None)
            if registry is not None and self in registry:
                registry.remove(self)
            self.scene().removeItem(self)


class VoltageAnnotation(BaseAnnotation):
    """Blauer, leicht gebogener Spannungsbogen über einem Bauteil.

    `flipped` spiegelt den Bogen: der Messpfeil sitzt dann am linken statt
    am rechten Ende (Messrichtung umgekehrt).
    """

    ANNOTATION_TYPE = "voltage"

    def __init__(self, parent_item, value="U", flipped=False):
        self.flipped = bool(flipped)
        super().__init__(parent_item)
        self.set_value(value)

    def text_color(self):
        return VOLTAGE_COLOR

    def edit_prompt(self):
        return ("Spannung", "Spannungswert eingeben (z. B. 20 V, 15 mV, 10 kV):")

    def set_flipped(self, flipped):
        self.flipped = bool(flipped)
        self.prepareGeometryChange()
        self.update()

    def _mirror(self):
        return -1.0 if self.flipped else 1.0

    def boundingRect(self):
        rect = QRectF(-ARC_HALF_WIDTH - 5, -ARC_BASE_OFFSET - ARC_HEIGHT - 5,
                      ARC_HALF_WIDTH * 2 + 10, ARC_HEIGHT + ARC_BASE_OFFSET + 10)
        text_rect = QRectF(self.text_item.pos(), self.text_item.boundingRect().size())
        return rect.united(text_rect)

    def shape(self):
        """Trefferfläche = Bogenkontur (mit Toleranz) + Textbereich."""
        m = self._mirror()
        base = -ARC_BASE_OFFSET
        path = QPainterPath()
        path.moveTo(m * -ARC_HALF_WIDTH, base)
        path.quadTo(0.0, base - ARC_HEIGHT * 2, m * ARC_HALF_WIDTH, base)
        stroker = QPainterPathStroker()
        stroker.setWidth(16)
        return stroker.createStroke(path).united(self._text_hit_path())

    def text_anchor(self):
        return QPointF(0, -(ARC_BASE_OFFSET + ARC_HEIGHT) - 14)

    def paint(self, painter, option, widget):
        self._paint_selection_hint(painter, option)
        pen = QPen(VOLTAGE_COLOR, 2)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        path = QPainterPath()
        base = -ARC_BASE_OFFSET
        m = self._mirror()
        path.moveTo(m * -ARC_HALF_WIDTH, base)
        path.quadTo(0.0, base - ARC_HEIGHT * 2, m * ARC_HALF_WIDTH, base)
        painter.drawPath(path)
        # Kleiner Pfeil am Bogenende (standardmäßig rechts), in Kurvenrichtung
        # nach unten aufs Bauteil weisend — Messpfeil-Konvention.
        end = QPointF(m * ARC_HALF_WIDTH, base)
        ctrl = QPointF(0.0, base - ARC_HEIGHT * 2)
        tangent = end - ctrl
        norm = math.hypot(tangent.x(), tangent.y())
        if norm > 0:
            tangent = QPointF(tangent.x() / norm, tangent.y() / norm)
            perp = QPointF(-tangent.y(), tangent.x())
            wing1 = QPointF(end.x() - tangent.x() * ARROW_LENGTH + perp.x() * ARROW_WIDTH,
                            end.y() - tangent.y() * ARROW_LENGTH + perp.y() * ARROW_WIDTH)
            wing2 = QPointF(end.x() - tangent.x() * ARROW_LENGTH - perp.x() * ARROW_WIDTH,
                            end.y() - tangent.y() * ARROW_LENGTH - perp.y() * ARROW_WIDTH)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(VOLTAGE_COLOR))
            painter.drawPolygon(QPolygonF([end, wing1, wing2]))

    def _extend_context_menu(self, menu):
        flip = QAction("Richtung drehen", None)
        flip.triggered.connect(self._flip_direction)
        menu.addAction(flip)

    def _flip_direction(self):
        self._request_undo()
        self.set_flipped(not self.flipped)

    def to_dict(self):
        data = {"type": self.ANNOTATION_TYPE,
                "x": float(self.x()), "y": float(self.y()),
                "value": self.value}
        if self.flipped:
            data["flip"] = True
        return data


class CurrentAnnotation(BaseAnnotation):
    """Roter Pfeil (gefülltes Dreieck) auf einer Leitung."""

    ANNOTATION_TYPE = "current"

    def __init__(self, parent_wire, value="I", angle=0.0):
        # Früh setzen: BaseAnnotation.__init__ ruft bereits text_anchor() auf.
        self.angle_deg = float(angle) % 360.0
        super().__init__(parent_wire)
        self.set_value(value)

    def text_color(self):
        return CURRENT_COLOR

    def edit_prompt(self):
        return ("Strom", "Stromwert eingeben (z. B. 20 A, 15 mA, 10 kA):")

    def set_angle(self, angle):
        self.angle_deg = float(angle) % 360.0
        self.prepareGeometryChange()
        self.update()

    def _triangle_points(self):
        """Dreieck symmetrisch um den Ursprung, Spitze in +x-Richtung.

        Spitze und Basis liegen gleich weit vom Anker entfernt — der Anker
        (die projizierte Klickstelle auf der Leitung) ist damit die optische
        Mitte des Pfeils und die Spitze sitzt exakt auf der Leitungsachse.
        """
        return [
            QPointF(TRIANGLE_SIZE, 0.0),
            QPointF(-TRIANGLE_SIZE, -TRIANGLE_SIZE * 0.7),
            QPointF(-TRIANGLE_SIZE, TRIANGLE_SIZE * 0.7),
        ]

    def _rotated(self, point):
        rad = math.radians(self.angle_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        return QPointF(point.x() * cos_a - point.y() * sin_a,
                       point.x() * sin_a + point.y() * cos_a)

    def boundingRect(self):
        pts = [self._rotated(p) for p in self._triangle_points()]
        xs = [p.x() for p in pts] + [0]
        ys = [p.y() for p in pts] + [0]
        rect = QRectF(min(xs) - 2, min(ys) - 2,
                      max(xs) - min(xs) + 4, max(ys) - min(ys) + 4)
        text_rect = QRectF(self.text_item.pos(), self.text_item.boundingRect().size())
        return rect.united(text_rect)

    def shape(self):
        """Trefferfläche = Pfeildreieck + Textbereich."""
        path = QPainterPath()
        path.addPolygon(QPolygonF([self._rotated(p) for p in self._triangle_points()]))
        path.closeSubpath()
        return path.united(self._text_hit_path())

    def text_anchor(self):
        # Text leicht oberhalb des Pfeils, senkrecht zur Pfeilrichtung.
        rad = math.radians(self.angle_deg)
        offset = QPointF(-math.sin(rad) * 18, -math.cos(rad) * 18)
        return offset

    def paint(self, painter, option, widget):
        self._paint_selection_hint(painter, option)
        painter.setPen(QPen(CURRENT_COLOR, 1))
        painter.setBrush(QBrush(CURRENT_COLOR))
        polygon = QPolygonF([self._rotated(p) for p in self._triangle_points()])
        painter.drawPolygon(polygon)

    def _extend_context_menu(self, menu):
        flip = QAction("Richtung drehen", None)
        flip.triggered.connect(self._flip_direction)
        menu.addAction(flip)

    def _flip_direction(self):
        self._request_undo()
        self.set_angle(self.angle_deg + 180.0)

    def to_dict(self):
        # Szenen-Koordinaten: die Leitung speichert nur absolute Endpunkte,
        # ihre Item-Position aber nicht — lokale Koordinaten wären verlustbehaftet.
        # Rechnerisch statt mapToScene: wird u. U. innerhalb des Maus-Press-
        # Dispatchs aufgerufen, wo Szenen-Abfragen zum Absturz führen können.
        # Leitungen sind nie rotiert/skaliert: Szene = Item-Position + lokale Position.
        parent = self.parentItem()
        if parent is not None:
            scene_pos = parent.pos() + QPointF(self.x(), self.y())
        else:
            scene_pos = QPointF(self.x(), self.y())
        return {"type": self.ANNOTATION_TYPE,
                "x": float(scene_pos.x()), "y": float(scene_pos.y()),
                "angle": self.angle_deg, "value": self.value}

"""
Grid Canvas - Main drawing area with grid and magnetic snapping
"""
import math

from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor


class GridCanvas(QGraphicsView):
    """Canvas with grid background and magnetic snapping"""

    # Feuert, wenn der Mauszeiger den Zeichenbereich verlässt (z. B. um die
    # halbtransparente Platzierungs-Vorschau zu entfernen).
    mouse_left_canvas = pyqtSignal()

    def __init__(self, parent=None, grid_size=20, subdivisions=1):
        super().__init__(parent)
        self.grid_size = grid_size
        self.subdivisions = max(1, subdivisions)
        self.snap_to_subgrid = False
        self.grid_visible = True  # Raster standardmäßig sichtbar

        # Pan mit mittlerer Maustaste
        self._is_panning = False
        self._pan_start_pos = None

        # Cache calculated sizes
        self._minor_grid_size = (
            self.grid_size / self.subdivisions if self.subdivisions > 1 else self.grid_size
        )

        # Grid styling
        self.major_grid_color = QColor(200, 200, 200)
        self.minor_grid_color = QColor(235, 235, 235)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Set canvas size - große Arbeitsfläche für Scrolling
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self._zoom_factor = 1.0

        # Configure view
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        # Scrollbars anzeigen wenn nötig
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Enable drag mode
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Initial bei Ursprung (0,0) zentrieren
        self.centerOn(0, 0)

    def drawBackground(self, painter, rect):
        """Draw grid background"""
        painter.fillRect(rect, QColor(255, 255, 255))

        # Nur Raster zeichnen wenn sichtbar
        if not self.grid_visible:
            return

        painter.save()

        def draw_grid(step_size, color):
            pen = QPen(color)
            pen.setWidth(1)
            painter.setPen(pen)

            left = math.floor(rect.left() / step_size) * step_size
            top = math.floor(rect.top() / step_size) * step_size

            x = left
            while x <= rect.right():
                painter.drawLine(int(round(x)), int(rect.top()), int(round(x)), int(rect.bottom()))
                x += step_size

            y = top
            while y <= rect.bottom():
                painter.drawLine(int(rect.left()), int(round(y)), int(rect.right()), int(round(y)))
                y += step_size

        # Draw finer grid first so major grid remains visible on top
        if self.subdivisions > 1:
            draw_grid(self._minor_grid_size, self.minor_grid_color)

        draw_grid(self.grid_size, self.major_grid_color)
        painter.restore()

    def set_grid_visible(self, visible):
        """Raster ein-/ausblenden"""
        self.grid_visible = visible
        self.viewport().update()

    def snap_to_grid(self, point, use_minor=None):
        """Snap a point to the nearest grid intersection"""
        if use_minor is None:
            use_minor = self.snap_to_subgrid

        step = self._minor_grid_size if use_minor and self.subdivisions > 1 else self.grid_size
        if step == 0:
            step = self.grid_size

        x = round(point.x() / step) * step
        y = round(point.y() / step) * step
        return QPointF(x, y)

    def set_subdivisions(self, subdivisions):
        """Update subdivision factor and redraw grid"""
        self.subdivisions = max(1, subdivisions)
        self._minor_grid_size = (
            self.grid_size / self.subdivisions if self.subdivisions > 1 else self.grid_size
        )
        self.viewport().update()

    def set_snap_to_subgrid(self, enabled):
        """Toggle snapping to the finer grid"""
        self.snap_to_subgrid = bool(enabled)

    @property
    def minor_grid_size(self):
        """Return the current minor grid size used for subdivisions"""
        return self._minor_grid_size

    def set_zoom_factor(self, factor):
        """Apply a zoom factor to the view"""
        factor = max(0.1, min(10.0, float(factor)))  # Limit zoom: 0.1x to 10x
        if factor == self._zoom_factor:
            return
        self.resetTransform()
        self.scale(factor, factor)
        self._zoom_factor = factor

    def wheelEvent(self, event):
        """Zoom mit Mausrad"""
        # Zoom-Faktor berechnen
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Zoom anwenden
        if event.angleDelta().y() > 0:
            # Hineinzoomen
            zoom_factor = zoom_in_factor
        else:
            # Herauszoomen
            zoom_factor = zoom_out_factor

        # Neue Zoom-Stufe berechnen
        new_zoom = self._zoom_factor * zoom_factor
        new_zoom = max(0.1, min(10.0, new_zoom))  # Limit zoom

        # Zoom anwenden mit Mausposition als Zentrum
        old_pos = self.mapToScene(event.pos())
        self.set_zoom_factor(new_zoom)
        new_pos = self.mapToScene(event.pos())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def zoom_in(self):
        """Hineinzoomen um 15%"""
        self.set_zoom_factor(self._zoom_factor * 1.15)

    def zoom_out(self):
        """Herauszoomen um 15%"""
        self.set_zoom_factor(self._zoom_factor / 1.15)

    def zoom_reset(self):
        """Zoom zurücksetzen auf 100%"""
        self.set_zoom_factor(1.0)

    def get_visible_scene_rect(self):
        """Gibt den aktuell sichtbaren Bereich der Szene zurück"""
        return self.mapToScene(self.viewport().rect()).boundingRect()

    def mousePressEvent(self, event):
        """Mouse-Press Event für Pan mit mittlerer Maustaste"""
        if event.button() == Qt.MiddleButton:
            # Pan-Modus starten
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Mouse-Move Event für Pan"""
        if self._is_panning:
            # Pan durchführen - Scene-Koordinaten verwenden
            # Aktuelle Mausposition in Scene-Koordinaten
            new_pos = self.mapToScene(event.pos())
            # Start-Position in Scene-Koordinaten
            old_pos = self.mapToScene(self._pan_start_pos)
            # Delta in Scene-Koordinaten
            delta = new_pos - old_pos

            # Aktuellen Center holen und verschieben
            current_center = self.mapToScene(self.viewport().rect().center())
            new_center = current_center - delta

            # View zum neuen Center verschieben
            self.centerOn(new_center)

            # Start-Position für nächsten Frame aktualisieren
            self._pan_start_pos = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Mouse-Release Event für Pan"""
        if event.button() == Qt.MiddleButton and self._is_panning:
            # Pan-Modus beenden
            self._is_panning = False
            self._pan_start_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        """Maus verlässt den Zeichenbereich -> Vorschau-Aufräumer informieren."""
        self.mouse_left_canvas.emit()
        super().leaveEvent(event)

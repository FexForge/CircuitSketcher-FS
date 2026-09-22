"""Messwert-Annotationen: Platzierung, Auswahl, Flip, Serialisierung."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt5.QtCore import QPointF

from src.components.annotations import CurrentAnnotation, VoltageAnnotation
from src.components.wire import Wire


def test_voltage_arc_centered_and_flip(main_window):
    mw = main_window
    comp = mw.create_component("resistor", 200, 300)
    mw.canvas.scene.addItem(comp)
    # Platzierungslogik: Bogen auf die Pol-Mitte
    poles = comp.get_pole_points()
    mid = QPointF((poles[0].x() + poles[1].x()) / 2,
                  (poles[0].y() + poles[1].y()) / 2)
    va = VoltageAnnotation(comp, "20 V")
    va.setPos(comp.mapFromScene(mid))
    comp.annotations.append(va)
    assert abs(va.x() - 40) < 0.01 and abs(va.y()) < 0.01
    assert "flip" not in va.to_dict()
    va.set_flipped(True)
    assert va.to_dict().get("flip") is True
    assert not va.shape().isEmpty()
    assert va.flags() & 0x1  # ItemIsSelectable


def test_current_triangle_on_wire_axis(main_window, monkeypatch):
    mw = main_window
    wire = Wire(QPointF(100, 200), QPointF(100, 500), grid_size=20)
    mw.canvas.scene.addItem(wire)
    click = QPointF(107, 300)  # 7 px daneben geklickt
    wire_line = __import__("PyQt5.QtCore", fromlist=["QLineF"]).QLineF(
        wire.start_point, wire.end_point)
    target = mw._project_point_on_line(click, wire_line)
    assert target == QPointF(100, 300)
    ann = CurrentAnnotation(wire, "15 mA", 90.0)
    ann.setPos(wire.mapFromScene(target))
    assert abs(ann.x() - 100) < 0.01
    tip = ann._rotated(ann._triangle_points()[0]) + ann.pos()
    assert abs(tip.x() - 100) < 0.01
    assert ann.flags() & 0x1
    # Richtung drehen (Rechtsklick-Aktion)
    ann.set_angle(ann.angle_deg + 180.0)
    assert abs(ann.angle_deg - 270.0) < 0.01


def test_snapshot_roundtrip_with_annotations(main_window):
    mw = main_window
    comp = mw.create_component("resistor", 200, 300)
    mw.canvas.scene.addItem(comp)
    wire = Wire(QPointF(200, 400), QPointF(400, 400), grid_size=20)
    mw.canvas.scene.addItem(wire)
    va = VoltageAnnotation(comp, "20 V", flipped=True)
    va.setPos(40, 0)
    comp.annotations.append(va)
    ca = CurrentAnnotation(wire, "15 mA", 0.0)
    ca.setPos(wire.mapFromScene(QPointF(300, 400)))
    wire.annotations.append(ca)
    snap = mw._capture_snapshot()
    volt = next(a for a in snap["annotations"] if a["type"] == "voltage")
    assert volt["flip"] is True
    assert any(a["type"] == "current" for a in snap["annotations"])
    mw._restore_snapshot(snap)
    volt = [a for c in mw.canvas.scene.items() if isinstance(c, type(comp))
            for a in getattr(c, "annotations", [])]
    assert volt and volt[0].flipped is True

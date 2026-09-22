"""Trenn-Logik: alle Symbole, beide Orientierungen, alle drei Richtungen
sowie die Überlappungs-Regel (Randüberhang kürzt statt zu ignorieren)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt5.QtCore import QPointF, Qt

from src.components.symbol_component import SymbolComponent
from src.components.wire import Wire


class FakeEvent:
    """QGraphicsSceneMouseEvent-Ersatz (in PyQt5 nicht instanziierbar)."""

    def __init__(self, pos, button=Qt.LeftButton):
        self._pos = QPointF(pos)
        self._btn = button

    def button(self):
        return self._btn

    def scenePos(self):
        return self._pos

    def isAccepted(self):
        return False

    def accept(self):
        pass

    def ignore(self):
        pass


def real_wires(mw):
    return [w for w in mw.canvas.scene.items()
            if isinstance(w, Wire) and w is not mw.temp_wire and w.line().length() > 0]


def real_components(mw):
    return [c for c in mw.canvas.scene.items() if isinstance(c, SymbolComponent)]


def reset(mw):
    mw.activate_select_mode()
    mw._cancel_pending_wire()
    mw.canvas.scene.clear()
    mw._ensure_decorations()
    mw.undo_stack.clear()
    mw.redo_stack.clear()


def test_all_symbols_three_directions(main_window):
    mw = main_window
    for sid in sorted(mw.symbol_definitions):
        if sid in ("Strom", "ground", "rail_plus", "rail_minus"):
            continue  # Durchführung / Erde (1-polig) trennen bewusst nicht
        for step in (0, 1):
            base = QPointF(200, 300)
            wstart, wend = ((QPointF(100, 300), QPointF(600, 300)) if step == 0
                            else (QPointF(200, 100), QPointF(200, 600)))
            # A) Platzieren auf bestehende Leitung
            reset(mw)
            mw.canvas.scene.addItem(Wire(wstart, wend, grid_size=20))
            mw.selected_component_type = sid
            mw.preview_rotation_step = step
            mw.canvas_mouse_press(FakeEvent(base))
            assert len(real_wires(mw)) == 2, f"{sid}@{step*90}° Platzieren"
            # B) Bestehendes Bauteil per Drag auf Leitung
            reset(mw)
            off = QPointF(200, 500) if step == 0 else QPointF(500, 300)
            comp = mw.create_component(sid, off.x(), off.y(),
                                       orientation="horizontal", rotation_step=step)
            mw.canvas.scene.addItem(comp)
            mw.canvas.scene.addItem(Wire(wstart, wend, grid_size=20))
            comp.setSelected(True)
            mw.selected_component_type = None
            mw.canvas_mouse_press(FakeEvent(off))
            comp.setPos(base)
            mw.canvas_mouse_release(FakeEvent(base))
            assert len(real_wires(mw)) == 2, f"{sid}@{step*90}° Drag"
            # C) Neue Leitung über bestehendes Bauteil
            reset(mw)
            comp = mw.create_component(sid, base.x(), base.y(),
                                       orientation="horizontal", rotation_step=step)
            mw.canvas.scene.addItem(comp)
            mw.selected_component_type = "wire"
            mw.canvas_mouse_press(FakeEvent(wstart))
            mw.canvas_mouse_press(FakeEvent(wend))
            mw._cancel_pending_wire()
            assert len(real_wires(mw)) == 2, f"{sid}@{step*90}° Leitung-über-Bauteil"


def test_overlap_rule_trims_overhang(main_window):
    """Ragt nur eine Bauteilhälfte über das Linienende, wird gekürzt."""
    mw = main_window
    reset(mw)
    mw.canvas.scene.addItem(Wire(QPointF(100, 300), QPointF(340, 300), grid_size=20))
    comp = mw.create_component("battery", 260, 500,
                               orientation="horizontal", rotation_step=0)
    mw.canvas.scene.addItem(comp)
    comp.setSelected(True)
    mw.selected_component_type = None
    mw.canvas_mouse_press(FakeEvent(QPointF(300, 500)))
    comp.setPos(320, 300)  # Pole 320..400 — Mitte 360 liegt hinter dem Ende 340
    mw.canvas_mouse_release(FakeEvent(QPointF(360, 300)))
    wires = sorted((round(w.start_point.x()), round(w.end_point.x())) for w in real_wires(mw))
    assert wires == [(100, 320)]


def test_attached_wire_not_resplit(main_window):
    """Eine an einem Pol angedockte Leitung wird nicht erneut getrennt."""
    mw = main_window
    reset(mw)
    comp = mw.create_component("resistor", 300, 300,
                               orientation="horizontal", rotation_step=0)
    mw.canvas.scene.addItem(comp)
    mw.canvas.scene.addItem(Wire(QPointF(380, 300), QPointF(600, 300), grid_size=20))
    comp.setSelected(True)
    mw.selected_component_type = None
    mw.canvas_mouse_press(FakeEvent(QPointF(340, 300)))
    comp.setPos(300, 300)
    mw.canvas_mouse_release(FakeEvent(QPointF(340, 300)))
    wires = sorted((round(w.start_point.x()), round(w.end_point.x())) for w in real_wires(mw))
    assert wires == [(380, 600)]

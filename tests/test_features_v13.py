"""v1.3-Features: Knotenpunkte, Clipboard, Nudge, Blattrahmen/Schriftfeld,
Drucken (PDF), Änderungsmarker, Autosave, neue Symbole, Palette."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from PyQt5.QtCore import QPointF, Qt

from src.components.symbol_component import SymbolComponent
from src.components.wire import Wire


def comps(mw):
    return [c for c in mw.canvas.scene.items() if isinstance(c, SymbolComponent)]


def wires(mw):
    return [w for w in mw.canvas.scene.items()
            if isinstance(w, Wire) and w is not mw.temp_wire and w.line().length() > 0]


def reset(mw):
    mw.canvas.scene.clear()
    mw._ensure_decorations()
    mw.undo_stack.clear()
    mw.redo_stack.clear()


# --- Knotenpunkte --------------------------------------------------------

def test_junction_dots_detection(main_window):
    mw = main_window
    reset(mw)
    mw.canvas.scene.addItem(Wire(QPointF(100, 200), QPointF(500, 200), grid_size=20))
    mw.canvas.scene.addItem(Wire(QPointF(300, 200), QPointF(300, 500), grid_size=20))
    assert mw.junction_layer.junction_points() == [QPointF(300, 200)]
    # Kreuzung OHNE Verbindungsende: kein Punkt
    reset(mw)
    mw.canvas.scene.addItem(Wire(QPointF(100, 200), QPointF(500, 200), grid_size=20))
    mw.canvas.scene.addItem(Wire(QPointF(290, 100), QPointF(310, 600), grid_size=20))
    assert mw.junction_layer.junction_points() == []
    # offenes Ende: kein Punkt
    reset(mw)
    mw.canvas.scene.addItem(Wire(QPointF(0, 0), QPointF(100, 0), grid_size=20))
    assert mw.junction_layer.junction_points() == []


# --- Neue Symbole ---------------------------------------------------------

def test_new_symbols_load_and_poles(main_window):
    mw = main_window
    expected = {"capacitor", "inductor", "diode", "led", "fuse", "motor", "ground"}
    assert expected <= set(mw.symbol_definitions)
    reset(mw)
    for sid in sorted(expected):
        c = mw.create_component(sid, 200, 300)
        mw.canvas.scene.addItem(c)
        poles = c.get_pole_points()
        if sid == "ground":
            assert len(poles) == 1
        else:
            assert len(poles) == 2, sid
            assert abs((poles[1].x() - poles[0].x()) - 80) < 0.01 or \
                   abs((poles[1].y() - poles[0].y()) - 80) < 0.01
        mw.canvas.scene.removeItem(c)


def test_palette_hides_strom_and_groups(main_window):
    mw = main_window
    tb = mw.component_toolbar
    assert "Strom" not in tb.symbol_buttons
    assert tb.select_group.title() == "Auswählen"
    tools = [tb.tools_group.layout().itemAt(i).widget().text()
             for i in range(tb.tools_group.layout().count())]
    assert tools == ["Leitung"]


# --- Clipboard ------------------------------------------------------------

def test_copy_paste_duplicate(main_window):
    mw = main_window
    reset(mw)
    c = mw.create_component("resistor", 300, 300)
    mw.canvas.scene.addItem(c)
    w = Wire(QPointF(380, 300), QPointF(500, 300), grid_size=20)
    mw.canvas.scene.addItem(w)
    c.setSelected(True)
    w.setSelected(True)
    mw.copy_selection()
    assert mw._clipboard and len(mw._clipboard["components"]) == 1
    mw.paste_clipboard()
    assert len(comps(mw)) == 2 and len(wires(mw)) == 2
    pasted = [x for x in comps(mw) if x is not c][0]
    assert pasted.x() == 340  # nahe dem Original (+2 Raster)
    mw.duplicate_selection()
    assert len(comps(mw)) == 3


# --- Nudge ------------------------------------------------------------------

class FakeKey:
    def __init__(self, key, mod=Qt.NoModifier):
        self._k, self._m = key, mod

    def key(self):
        return self._k

    def modifiers(self):
        return self._m

    def accept(self):
        pass


def test_nudge_fine_and_grid(main_window):
    mw = main_window
    reset(mw)
    c = mw.create_component("resistor", 300, 300)
    mw.canvas.scene.addItem(c)
    c.setSelected(True)
    mw.keyPressEvent(FakeKey(Qt.Key_Right))          # fein: +1 px
    assert c.x() == 301
    mw.keyPressEvent(FakeKey(Qt.Key_Right, Qt.ShiftModifier))  # Raster: +20 (snappt)
    assert c.x() == round(301 / 20) * 20 + 20


# --- Blattrahmen/Schriftfeld/Drucken ---------------------------------------

def test_sheet_roundtrip_and_print(main_window, tmp_path):
    mw = main_window
    reset(mw)
    mw.canvas.scene.addItem(Wire(QPointF(100, 100), QPointF(300, 100), grid_size=20))
    mw._set_sheet_visible(True)
    mw.sheet_meta.update({"title": "Prüfung"})
    snap = mw._capture_snapshot()
    assert snap["sheet"]["visible"] is True and snap["sheet"]["title"] == "Prüfung"
    mw._restore_snapshot(snap)
    assert mw.sheet_meta["title"] == "Prüfung" and mw.sheet_frame.isVisible()

    from PyQt5.QtPrintSupport import QPrinter
    pdf = tmp_path / "print.pdf"
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(str(pdf))
    mw._render_to_printer(printer)
    assert pdf.exists() and pdf.stat().st_size > 1000


# --- Datei-Komfort -----------------------------------------------------------

def test_dirty_title_save_load(main_window, tmp_path):
    mw = main_window
    reset(mw)
    mw.canvas.scene.addItem(Wire(QPointF(0, 0), QPointF(100, 0), grid_size=20))
    mw._mark_dirty()
    assert "*" in mw.windowTitle()
    path = tmp_path / "test.sz.json"
    path.write_text(json.dumps(mw._capture_snapshot(), ensure_ascii=False), encoding="utf-8")
    mw.current_file = None
    mw.load_circuit(str(path))
    assert "*" not in mw.windowTitle()
    assert len(wires(mw)) == 1


def test_autosave_roundtrip(main_window):
    mw = main_window
    reset(mw)
    mw.canvas.scene.addItem(Wire(QPointF(0, 0), QPointF(100, 0), grid_size=20))
    expected = len(comps(mw))
    mw._mark_dirty()
    mw._autosave()
    assert mw._autosave_path().exists()
    mw.canvas.scene.clear()
    mw._ensure_decorations()
    mw.restore_autosave()
    assert len(comps(mw)) == expected
    if mw._autosave_path().exists():
        mw._autosave_path().unlink()

"""Kontakt-Spiegel-Element: Platzierung, Zuordnung, Serialisierung,
Ruhelage-Darstellung der Schalter-/Tastertypen (Namen + Zeichnung)."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.components.contact_mirror import ContactMirrorItem


def build(mw, symbol_id, x, y, name=None, **values):
    comp = mw.create_component(symbol_id, x, y,
                               orientation="horizontal", rotation_step=0)
    mw.canvas.scene.addItem(comp)
    if name:
        comp.set_placeholder_value("name", name)
    for key, value in values.items():
        comp.set_placeholder_value(key, value)
    return comp


def fresh(mw):
    mw.canvas.scene.clear()
    mw._ensure_decorations()
    return mw


# ----------------------------------------------------------------------
# Symbol-Namen: normally_open = Schliesser (ruht offen),
# normally_closed = Öffner (ruht geschlossen)
# ----------------------------------------------------------------------
def test_switch_names_match_rest_state():
    base = Path(__file__).resolve().parent.parent / "symbols"
    cases = {
        "switch_normally_open": "Schliesser",
        "switch_normally_closed": "Öffner",
        "pushbutton_normally_open": "Schliesser",
        "pushbutton_normally_closed": "Öffner",
        "relay_contact_no": "Schliesser",
        "relay_contact_nc": "Öffner",
    }
    for sid, expected in cases.items():
        data = json.loads((base / f"{sid}.symbol.json").read_text(encoding="utf-8"))
        assert expected in data["name"], f"{sid}: '{data['name']}' ohne '{expected}'"


def _lever_tip(sid):
    """Spitze des Kontaktarms: Linie, die auf der Achse links vom Mittelpunkt
    startet und weit nach rechts reicht (funktioniert für jede Steigung)."""
    data = json.loads(
        (Path(__file__).resolve().parent.parent / "symbols" / f"{sid}.symbol.json"
         ).read_text(encoding="utf-8"))
    for item in data["orientations"]["horizontal"]["items"]:
        if item["type"] != "line":
            continue
        (sx, sy), (ex, ey) = item["start"], item["end"]
        if sy == 0 and -12 <= sx <= -4 and ex >= 8:
            return item["end"]
    raise AssertionError(f"{sid}: kein Kontaktarm definiert")


def test_switch_rest_geometry_matches_id():
    """Schliesser (…_normally_open) ruht OFFEN: Hebel klar angehoben (Spitze
    deutlich über der Kontaktlinie). Öffner (…_normally_closed) ruht ZU:
    Hebel liegt fast flach auf dem festen Kontakt."""
    for sid in ("switch_normally_open", "pushbutton_normally_open",
                "relay_contact_no", "timer_contact_pickup",
                "timer_contact_dropout"):
        tip = _lever_tip(sid)
        assert tip[1] <= -10, f"{sid}: Schliesser sollte offen ruhen, Spitze {tip}"
    for sid in ("switch_normally_closed", "pushbutton_normally_closed",
                "relay_contact_nc"):
        tip = _lever_tip(sid)
        assert -6 < tip[1] < 0, f"{sid}: Öffner sollte zu ruhen, Spitze {tip}"


# ----------------------------------------------------------------------
# Kontakt-Spiegel-Element
# ----------------------------------------------------------------------
def test_mirror_lists_contacts_with_rest_state(main_window):
    mw = fresh(main_window)
    build(mw, "relay_coil", 400, 100, name="K1")
    no_c = build(mw, "relay_contact_no", 200, 200, name="K1")
    nc_c = build(mw, "relay_contact_nc", 200, 300, name="K1")
    mirror = ContactMirrorItem("K1", grid_size=20)
    mw.canvas.scene.addItem(mirror)

    coil, rows = mirror._relay_data()
    assert coil is not None
    kinds = [r[0] for r in rows]
    assert "Schliesser" in kinds and "Öffner" in kinds
    states = {r[0]: r[3] for r in rows}
    assert states["Schliesser"] is False, "Schliesser ruht offen"
    assert states["Öffner"] is True, "Öffner ruht geschlossen"

    # Mit laufendem Motor der Simulation: Spule zieht an -> beide umgekehrt
    from src.simulation.solver import SimEngine
    engine = SimEngine(mw.canvas.scene)
    engine.coil_latched["K1"] = True
    engine._update_contact_states()
    mirror.engine_provider = lambda: engine
    coil, rows = mirror._relay_data()
    states = {r[0]: r[3] for r in rows}
    assert states["Schliesser"] is True and states["Öffner"] is False


def test_mirror_serialization_roundtrip(main_window):
    mw = fresh(main_window)
    build(mw, "relay_coil", 400, 100, name="K2")
    mirror = ContactMirrorItem("K2", grid_size=20)
    mirror.setPos(300, 500)
    mw.canvas.scene.addItem(mirror)

    snapshot = mw._capture_snapshot()
    entry = [a for a in snapshot["annotations"] if a.get("type") == "contact_mirror"]
    assert entry and entry[0]["value"] == "K2"
    assert entry[0]["x"] == 300 and entry[0]["y"] == 500

    mw._restore_snapshot(snapshot)
    mirrors = [i for i in mw.canvas.scene.items()
               if isinstance(i, ContactMirrorItem)]
    assert len(mirrors) == 1
    assert mirrors[0].relay_name == "K2"
    assert mirrors[0].pos().x() == 300


def test_mirror_placement_tool(main_window):
    mw = fresh(main_window)
    build(mw, "relay_coil", 400, 100, name="K1")
    mw.on_component_selected("contact_mirror")
    assert mw.selected_component_type in (None, "contact_mirror")
    mw._place_contact_mirror(mw.canvas.snap_to_grid(
        __import__("PyQt5.QtCore", fromlist=["QPointF"]).QPointF(240, 260)))
    mirrors = [i for i in mw.canvas.scene.items()
               if isinstance(i, ContactMirrorItem)]
    assert len(mirrors) == 1
    assert mirrors[0].relay_name == "K1", "Auto-Zuweisung an niedrigstes Relais"

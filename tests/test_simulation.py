"""Funktionsschema-Simulation: Netzliste, Löser (Selbsthaltung), Zeitrelais,
DC-Messung, Motor-Richtung.

Geometrie-Konvention: Bauteile mit Ursprung links oben platzieren, Pole liegen
bei (x, y) und (x+80, y); Schienen spannen 400 px (x .. x+400)."""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt5.QtCore import QPointF

from src.components.symbol_component import SymbolComponent
from src.components.wire import Wire
from src.simulation.solver import SimEngine
from src.simulation.dc import meter_readings, parse_ohm, parse_voltage


def build(mw, symbol_id, x, y, name=None, step=0, **values):
    comp = mw.create_component(symbol_id, x, y,
                               orientation="horizontal", rotation_step=step)
    mw.canvas.scene.addItem(comp)
    if name:
        comp.set_placeholder_value("name", name)
    for key, value in values.items():
        comp.set_placeholder_value(key, value)
    return comp


def wire(mw, a, b):
    w = Wire(QPointF(*a), QPointF(*b), grid_size=20)
    mw.canvas.scene.addItem(w)
    return w


def fresh(main_window):
    mw = main_window
    mw.canvas.scene.clear()
    mw._ensure_decorations()
    return mw


def test_parse_units():
    assert parse_ohm("4,7 kΩ") == 4700.0
    assert parse_ohm("220 Ω") == 220.0
    assert parse_voltage("12 V") == 12.0
    assert parse_voltage("1,5 V") == 1.5


def test_lamp_lights_via_switch(main_window):
    mw = fresh(main_window)
    build(mw, "rail_plus", 100, 100)                    # Segment x=100..500, y=100
    sw = build(mw, "switch_normally_open", 300, 200)    # Pole (300/380, 200)
    lamp = build(mw, "lamp", 500, 200)                  # Pole (500/580, 200)
    build(mw, "rail_minus", 100, 500)                   # Segment x=100..500, y=500
    wire(mw, (300, 100), (300, 200))   # L+ -> Schalter Pin0 (T auf Schiene)
    wire(mw, (380, 200), (500, 200))   # Schalter -> Lampe
    wire(mw, (580, 200), (580, 500))   # Lampe -> runter
    wire(mw, (300, 500), (580, 500))   # quer (T auf M-Schiene)
    engine = SimEngine(mw.canvas.scene)
    engine.evaluate()
    assert not engine.active.get(lamp, False), "Lampe aus (Schalter offen)"
    engine.toggle_manual(sw)
    engine.evaluate()
    assert engine.active.get(lamp, False), "Lampe leuchtet (Schalter zu)"


def test_relay_latching(main_window):
    """Klassische Selbsthaltung: Taster parallel zum eigenen Kontakt K1."""
    mw = fresh(main_window)
    build(mw, "rail_plus", 100, 100)
    build(mw, "rail_minus", 100, 700)
    btn = build(mw, "pushbutton_normally_open", 300, 200)   # Pole 300/380
    hold = build(mw, "relay_contact_no", 300, 360, name="K1")  # Pole 300/380
    coil = build(mw, "relay_coil", 600, 200, name="K1")     # Pole 600/680
    wire(mw, (200, 100), (200, 200))   # L+ Abzweig (T auf Schiene)
    wire(mw, (200, 200), (300, 200))   # an Taster Pin0
    wire(mw, (300, 200), (300, 360))   # linke Seite parallel
    wire(mw, (380, 200), (380, 360))   # rechte Seite parallel (Knoten A)
    wire(mw, (380, 200), (600, 200))   # A -> Spule (T auf (380,200))
    wire(mw, (680, 200), (680, 700))   # Spule -> M
    wire(mw, (200, 700), (680, 700))   # quer (T auf M)
    engine = SimEngine(mw.canvas.scene)
    engine.evaluate()
    assert not engine.active.get(coil, False), "Spule aus (alles offen)"
    engine.press_manual(btn, pressed=True)
    engine.evaluate()
    assert engine.active.get(coil, False), "Spule zieht an (Taster)"
    engine.press_manual(btn, pressed=False)
    engine.evaluate()
    assert engine.active.get(coil, False), "SELBSTHALTUNG hält die Spule"


def test_timer_relay_delay(main_window):
    mw = fresh(main_window)
    build(mw, "rail_plus", 100, 100)
    build(mw, "rail_minus", 100, 700)
    sw = build(mw, "switch_normally_open", 300, 200)
    coil = build(mw, "timer_coil", 600, 200, name="KT1", delay="0.3 s")
    tc = build(mw, "timer_contact_pickup", 300, 360, name="KT1")
    lamp = build(mw, "lamp", 500, 360)
    wire(mw, (200, 100), (200, 200)); wire(mw, (200, 200), (300, 200))
    wire(mw, (380, 200), (600, 200))
    wire(mw, (680, 200), (680, 700)); wire(mw, (200, 700), (680, 700))
    # Lampenzweig: L+ -> verzögerter Kontakt -> Lampe -> M
    wire(mw, (240, 100), (240, 300)); wire(mw, (240, 300), (300, 360))
    wire(mw, (380, 360), (500, 360))
    wire(mw, (580, 360), (580, 700))
    engine = SimEngine(mw.canvas.scene)
    engine.evaluate()
    assert not engine.active.get(coil, False)
    engine.toggle_manual(sw)
    engine.evaluate()
    assert engine.active.get(coil, False), "Zeitrelais-Spule an"
    assert not engine.active.get(lamp, False), "Kontakt NICHT sofort schließen"
    engine.tick(0.1)          # erster Takt startet den Verzögerungstimer
    time.sleep(0.35)
    engine.tick(0.1)          # nach Ablauf: Kontakt schließt
    assert engine.active.get(lamp, False), "Verzögert geschlossen nach Ablauf"


def test_dc_meter_readings(main_window):
    mw = fresh(main_window)
    build(mw, "battery", 200, 200, voltage="12 V")     # Pole 200/280
    build(mw, "resistor", 400, 200, resistance="1 kΩ")  # Pole 400/480
    amm = build(mw, "ammeter", 600, 200)               # Pole 600/680
    wire(mw, (280, 200), (400, 200))
    wire(mw, (480, 200), (600, 200))
    wire(mw, (680, 200), (680, 400)); wire(mw, (680, 400), (200, 400))
    wire(mw, (200, 200), (200, 400))
    result, readings = meter_readings(mw.canvas.scene)
    text = readings.get(amm, "—")
    assert "mA" in text, f"reale Werte erwartet: {text!r} ({result.reason})"
    assert "12" in text, "12 V / 1 kOhm = 12 mA"


def test_motor_direction_placeholder(main_window):
    mw = fresh(main_window)
    motor = build(mw, "motor", 300, 300, name="M1")
    assert motor.placeholder_values.get("direction") == "rechts"
    motor.set_placeholder_value("direction", "links")
    assert motor.placeholder_values.get("direction") == "links"

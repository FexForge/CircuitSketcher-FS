"""DC-Messwerte: Ohm'sche Netzwerke numerisch lösen (Knotenpotenzialanalyse).

Gilt für klassische Schaltungen (Batterie + Widerstände/Leitungen), NICHT für
Funktionsschemata mit Schienen. Ist ein Element nicht numerisch (Wert fehlt
oder unbekannt), meldet der Löser 'nicht berechenbar' — die Messgeräte
bleiben dann bei Ihrer manuellen Beschriftung.

Wertformate deutsch-tolerant: '4,7 kΩ'/'4.7 kOhm'/'10 V'/'15 mA'/'2 A'.
"""
import math

from .netlist import Netlist, UnionFind

OHM_UNITS = {"": 1.0, "ohm": 1.0, "Ω".lower(): 1.0, "r": 1.0,
             "k": 1e3, "kohm": 1e3, "kΩ".lower(): 1e3, "kiloohm": 1e3,
             "m": 1e6, "mohm": 1e6, "megaohm": 1e6}
VOLT_UNITS = {"": 1.0, "v": 1.0, "volt": 1.0, "mv": 1e-3, "millivolt": 1e3 and 1e-3,
              "kv": 1e3, "kilovolt": 1e3}
AMP_UNITS = {"": 1.0, "a": 1.0, "ampere": 1.0, "ma": 1e-3, "milliampere": 1e-3,
             "µa": 1e-6, "ua": 1e-6, "ka": 1e3}


def _parse_number(text):
    return float(str(text).strip().replace(",", ".").split()[0])


def parse_ohm(text):
    s = str(text).strip().lower().replace(" ", "").replace("ohm", "Ω")
    try:
        for suffix in sorted(OHM_UNITS, key=len, reverse=True):
            if s.endswith(suffix.lower()) or (suffix == "" and s[-1:].isdigit()):
                value = float(s[: len(s) - len(suffix)].replace(",", ".")
                              if suffix else s.replace(",", "."))
                return value * OHM_UNITS[suffix]
    except (ValueError, IndexError):
        pass
    return None


def parse_voltage(text):
    s = str(text).strip().lower().replace(" ", "")
    try:
        for suffix in ("millivolt", "mv", "kilovolt", "kv", "volt", "v", ""):
            if s.endswith(suffix):
                head = s[: len(s) - len(suffix)]
                if head:
                    value = float(head.replace(",", "."))
                    factor = {"millivolt": 1e-3, "mv": 1e-3,
                              "kilovolt": 1e3, "kv": 1e3, "volt": 1.0,
                              "v": 1.0, "": 1.0}[suffix]
                    return value * factor
    except ValueError:
        pass
    return None


def _gauss(matrix, vector):
    """Kleine Gauß-Elimination mit Pivot; None bei singulärem System."""
    n = len(vector)
    a = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-12:
            return None
        a[col], a[pivot] = a[pivot], a[col]
        for row in range(col + 1, n):
            factor = a[row][col] / a[col][col]
            for c in range(col, n + 1):
                a[row][c] -= factor * a[col][c]
    x = [0.0] * n
    for row in range(n - 1, -1, -1):
        value = a[row][n] - sum(a[row][c] * x[c] for c in range(row + 1, n))
        x[row] = value / a[row][row]
    return x


R_METER_SHUNT = 1e-3     # Amperemeter: Strom über Spannungsabfall am Shunt
R_VOLTMETER = 1e9        # Voltmeter: sehr hoher Innenwiderstand
R_SOURCE_INTERNAL = 1e-3 # Batterie: winziger Innenwiderstand zur Stabilität


class DCSolution:
    def __init__(self, ok, node_voltages=None, currents=None, reason=""):
        self.ok = ok
        self.node_voltages = node_voltages or {}
        self.currents = currents or {}
        self.reason = reason


def solve_dc(scene):
    """Netzwerk lösen; liefert (DCSolution, Netlist) — ok=False mit Grund,
    wenn nicht berechenbar (Funktionsschema-Schienen, fehlende Werte …)."""
    from ..components.symbol_component import SymbolComponent
    net = Netlist.from_scene(scene)
    components = net.components()

    batteries = [c for c in components if c.symbol_id == "battery"]
    resistors = [c for c in components if c.symbol_id in ("resistor", "lamp", "motor", "fuse", "inductor", "switch_normally_open", "switch")]
    voltmeters = [c for c in components if c.symbol_id == "voltmeter"]
    ammeters = [c for c in components if c.symbol_id == "ammeter"]
    rails = [c for c in components if getattr(c, "symbol_id", "").startswith("rail_")]

    if not voltmeters and not ammeters:
        return DCSolution(False, reason="keine Messgeräte"), net
    if not batteries:
        return DCSolution(False, reason="keine Spannungsquelle"), net
    if rails:
        return DCSolution(False, reason="Funktionsschema-Schienen sind nicht numerisch"), net

    # Knoten aufbauen (Masse = Referenz), Bauteile als Zweipole.
    # Amperemeter-NICHT vereinigen: sein Shunt ist die einzige Verbindung —
    # nur so fliesst ein messbarer Strom durch den Zweig.
    node_ids = {}
    def node_key(component, pin):
        raw = net.pins.get(component, [])[pin]
        return net.uf.find(raw)

    def node_index(key):
        if key not in node_ids:
            node_ids[key] = len(node_ids)
        return node_ids[key]

    branches = []  # (node_a, node_b, resistance, voltage_source, tag)
    for battery in batteries:
        if len(net.pins.get(battery, [])) < 2:
            continue
        value = parse_voltage(battery.placeholder_values.get("voltage", ""))
        if value is None:
            return DCSolution(False, reason="Batteriespannung fehlt"), net
        # Polung: Pin 0 = Minus, Pin 1 = Plus (Batterie-Symbolkonvention)
        branches.append((node_index(node_key(battery, 0)),
                         node_index(node_key(battery, 1)),
                         R_SOURCE_INTERNAL, value, ("battery", id(battery))))
    ohm_missing = None
    for resistor in resistors:
        if len(net.pins.get(resistor, [])) < 2:
            continue
        value = parse_ohm(resistor.placeholder_values.get("resistance", ""))
        if value is None:
            value = parse_ohm(resistor.placeholder_values.get("voltage", ""))
        if value is None or value <= 0:
            ohm_missing = resistor.placeholder_values.get("name", resistor.symbol_id)
            continue
        branches.append((node_index(node_key(resistor, 0)),
                         node_index(node_key(resistor, 1)),
                         value, 0.0, ("resistor", id(resistor))))
    for voltmeter in voltmeters:
        if len(net.pins.get(voltmeter, [])) < 2:
            continue
        branches.append((node_index(node_key(voltmeter, 0)),
                         node_index(node_key(voltmeter, 1)),
                         R_VOLTMETER, 0.0, ("voltmeter", id(voltmeter))))
    for ammeter in ammeters:
        if len(net.pins.get(ammeter, [])) < 2:
            continue
        branches.append((node_index(node_key(ammeter, 0)),
                         node_index(node_key(ammeter, 1)),
                         R_METER_SHUNT, 0.0, ("ammeter", id(ammeter))))
    if ohm_missing:
        return DCSolution(False, reason=f"Widerstandswert fehlt ({ohm_missing})"), net

    n = len(node_ids)
    if n < 2:
        return DCSolution(False, reason="zu wenig Knoten"), net
    # MNA: G-Matrix + Stromquellen; Quelle als Norton äquivalent (U/R intern)
    g = [[0.0] * n for _ in range(n)]
    i_vec = [0.0] * n
    for a, b, resistance, source, _tag in branches:
        conductance = 1.0 / resistance
        g[a][a] += conductance
        g[b][b] += conductance
        g[a][b] -= conductance
        g[b][a] -= conductance
        if source:
            # Strom von b nach a treiben (Plus-Pol b)
            i_vec[a] -= source / resistance
            i_vec[b] += source / resistance
    # Referenzknoten (Index 0) auf 0 V pinnen: Zeile/Spalte entfernen
    reduced = [[g[r][c] for c in range(1, n)] for r in range(1, n)]
    rhs = [-i_vec[r] for r in range(1, n)]
    solution = _gauss(reduced, rhs)
    if solution is None:
        return DCSolution(False, reason="Netzwerk singulär (Kurzschluss?)"), net
    voltages = {0: 0.0}
    for idx in range(1, n):
        voltages[idx] = solution[idx - 1]
    currents = {}
    for a, b, resistance, source, (kind, comp_id) in branches:
        current = (voltages[a] - voltages[b] + source) / resistance
        currents[comp_id] = current
    return DCSolution(True, node_voltages=voltages, currents=currents), net


def meter_readings(scene):
    """{component: anzeigbarer Text} für Volt-/Amperemeter ('—' wenn nicht
    berechenbar)."""
    result, net = solve_dc(scene)
    readings = {}
    for component in net.components():
        sid = getattr(component, "symbol_id", "")
        if sid not in ("voltmeter", "ammeter"):
            continue
        if not result.ok:
            readings[component] = "—"
            continue
        current = result.currents.get(id(component), 0.0)
        if sid == "ammeter":
            value = abs(current)
            unit, factor = ("A", 1.0)
            if value < 0.1:
                unit, factor = ("mA", 1e3)
            elif value >= 1000:
                unit, factor = ("kA", 1e-3)
            readings[component] = _format(value * factor, unit)
        else:
            keys = net.pins.get(component, [])
            if len(keys) < 2:
                readings[component] = "—"
                continue
            from .netlist import UnionFind as UF
            # Spannung über dem Voltmeter = Strom * R (hochohmig)
            value = abs(current) * R_VOLTMETER
            unit, factor = ("V", 1.0)
            if value < 0.1:
                unit, factor = ("mV", 1e3)
            elif value >= 1000:
                unit, factor = ("kV", 1e-3)
            readings[component] = _format(value * factor, unit)
    return result, readings


def _format(value, unit):
    if value >= 100:
        text = f"{value:.0f}"
    elif value >= 10:
        text = f"{value:.1f}"
    else:
        text = f"{value:.2f}"
    return f"{text} {unit}"

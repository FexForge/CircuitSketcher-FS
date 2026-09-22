"""Schaltlogik-Löser für Funktionsschemata.

Modell: Diskrete Logik (keine Spannungen/Ströme). Eine Schiene L+ speist,
eine Schiene M ist Rückleiter. Verbraucher (Lampe, Motor, Spule) sind aktiv,
wenn Pin 1 über GESCHLOSSENE Kontakte an L+ und Pin 2 an M liegt (oder
umgekehrt). Verbraucher überbrücken KEINE Netze — sonst würden parallele
Pfade falsch verbinden. Amperemeter leiten (0 Ω), Voltmeter nicht (∞).

Selbsthaltung: Spulenzustände werden rundenweise aktualisiert, bis ein
Fixpunkt erreicht ist (max. RUNDEN, danach Hinweis).

Zeitrelais: Spulenzustandswechsel starten/stoppen Verzögerungstimer; der
Kontakt schaltet erst nach Ablauf (anzugs- bzw. abfallverzögert). Timer
laufen im Takt (tick), nicht im Fixpunkt.
"""
import time

from .netlist import Netlist

# symbol_id -> (gruende Stellung geschlossen?, momentan?)
MANUAL_SWITCHES = {
    "switch": (False, False),
    "switch_normally_open": (False, False),
    "switch_normally_closed": (True, False),
    "pushbutton_normally_open": (False, True),
    "pushbutton_normally_closed": (True, True),
}
# symbol_id -> (Schliesser?, Verzögerung: None|"pickup"|"dropout")
CONTACTS = {
    "relay_contact_no": (True, None),
    "relay_contact_nc": (False, None),
    "timer_contact_pickup": (True, "pickup"),
    "timer_contact_dropout": (True, "dropout"),
}
COIL_SYMBOLS = {"relay_coil": "sofort", "timer_coil": "zeit"}
LOAD_SYMBOLS = {"lamp", "motor"}
METER_SYMBOLS = {"voltmeter", "ammeter"}
RAIL_PLUS = "rail_plus"
RAIL_MINUS = "rail_minus"
MAX_ROUNDS = 40


def parse_delay_seconds(text, default=2.0):
    """'2 s', '1,5 s', '500 ms' → Sekunden (Fehlertolerant)."""
    try:
        value = str(text).replace(",", ".").strip().lower()
        if value.endswith("ms"):
            return float(value[:-2].strip()) / 1000.0
        for suffix in ("s", "sec", "sek"):
            if value.endswith(suffix):
                value = value[: -len(suffix)].strip()
                break
        return float(value)
    except (ValueError, TypeError):
        return default


class SimEngine:
    """Zustand + Auswertung einer laufenden Simulation."""

    def __init__(self, scene, exclude_wire=None):
        self.scene = scene
        self.manual = {}        # component -> bool (Schalter/Taster-Stellung)
        self.coil_latched = {}  # Spulename -> bool (Spule zieht an)
        self.timer_contact = {} # Spulename -> bool (Zeitkontakt-Stellung)
        self.timers = {}        # Spulename -> (deadline|None, Ziel)
        self.energized_nets = set()
        self.active = {}        # component -> bool (Lampe leuchtet, Motor läuft, Spule an)
        self.contact_closed = {}  # component -> bool
        self.unstable = False
        self.message = ""
        self._rebuild()

    # -- Aufbau ------------------------------------------------------------
    def _rebuild(self):
        self.net = Netlist.from_scene(self.scene, exclude_wire=None)
        self.switches = [c for c in self.net.components()
                         if getattr(c, "symbol_id", "") in MANUAL_SWITCHES]
        self.contacts = [c for c in self.net.components()
                         if getattr(c, "symbol_id", "") in CONTACTS]
        self.coils = [c for c in self.net.components()
                      if getattr(c, "symbol_id", "") in COIL_SYMBOLS]
        self.loads = [c for c in self.net.components()
                      if getattr(c, "symbol_id", "") in LOAD_SYMBOLS]
        self.meters = [c for c in self.net.components()
                       if getattr(c, "symbol_id", "") in METER_SYMBOLS]
        self.rails_plus = [c for c in self.net.components()
                           if getattr(c, "symbol_id", "") == RAIL_PLUS]
        self.rails_minus = [c for c in self.net.components()
                            if getattr(c, "symbol_id", "") == RAIL_MINUS]
        for switch in self.switches:
            if switch not in self.manual:
                initial, _ = MANUAL_SWITCHES[switch.symbol_id]
                self.manual[switch] = initial
        for coil in self.coils:
            name = self._name_of(coil)
            self.coil_latched.setdefault(name, False)
            self.timer_contact.setdefault(name, False)
            self.timers.setdefault(name, (None, None))

    @staticmethod
    def _name_of(component):
        return str(component.placeholder_values.get("name", "") or "").strip()

    def relay_delay(self, coil_name):
        for coil in self.coils:
            if self._name_of(coil) == coil_name and coil.symbol_id == "timer_coil":
                return parse_delay_seconds(coil.placeholder_values.get("delay", "2 s"))
        return None

    # -- Betätigung ----------------------------------------------------------
    def toggle_manual(self, component):
        """Schalter umschalten (Klick)."""
        if component in self.manual:
            self.manual[component] = not self.manual[component]
            return True
        return False

    def press_manual(self, component, pressed):
        """Taster drücken/loslassen (momentan)."""
        if component in self.manual and MANUAL_SWITCHES.get(component.symbol_id, (0, 0))[1]:
            initial, _ = MANUAL_SWITCHES[component.symbol_id]
            # Taster: gedrückt = Umkehrung der Ruhestellung
            self.manual[component] = (not initial) if pressed else initial
            return True
        return False

    # -- Leitfähigkeit eines Bauteils --------------------------------------
    def _conducts(self, component):
        """Bauteil verbindet seine Pole (als Schalter/Kontakt/Amperemeter)."""
        sid = getattr(component, "symbol_id", "")
        if sid in MANUAL_SWITCHES:
            return bool(self.manual.get(component, False))
        if sid in CONTACTS:
            return bool(self.contact_closed.get(component, False))
        if sid == "ammeter":
            return True
        return False

    def _update_contact_states(self):
        """Kontaktstellungen aus Spulenzuständen ableiten."""
        for contact in self.contacts:
            is_no, timing = CONTACTS[contact.symbol_id]
            coil_name = self._name_of(contact)
            if timing is None:
                coil_on = self.coil_latched.get(coil_name, False)
            else:
                coil_on = self.timer_contact.get(coil_name, False)
            self.contact_closed[contact] = coil_on if is_no else not coil_on

    # -- Fixpunkt ------------------------------------------------------------
    def evaluate(self):
        """Logik auswerten bis stabil; setzt energized_nets/active/contact_closed."""
        self._rebuild()
        for _ in range(MAX_ROUNDS):
            self._update_contact_states()
            # Basis-Konnektivität (Leitungen/Schienen) übernehmen, dann
            # leitende Bauteile (Schalter/Kontakte/Amperemeter) obendrauf.
            union = self.net.clone_union()
            for component in self.net.components():
                if self._conducts(component):
                    keys = self.net.pins.get(component, [])
                    if len(keys) >= 2:
                        union.union(keys[0], keys[1])
            source = set()
            for rail in self.rails_plus:
                node = self.net.node_of_pin(rail, 0)
                if node:
                    source.add(union.find(node))
            sink = set()
            for rail in self.rails_minus:
                node = self.net.node_of_pin(rail, 0)
                if node:
                    sink.add(union.find(node))
            # aktive Verbraucher/Spulen
            changed = False
            for component in self.loads + self.coils:
                keys = self.net.pins.get(component, [])
                is_active = False
                if len(keys) >= 2:
                    a, b = union.find(keys[0]), union.find(keys[1])
                    is_active = ((a in source and b in sink) or (a in sink and b in source)) \
                        and a != b
                if self.active.get(component, False) != is_active:
                    changed = True
                self.active[component] = is_active
            # Spulenzustände aus Aktivität
            for coil in self.coils:
                name = self._name_of(coil)
                latched = bool(self.active.get(coil, False))
                if self.coil_latched.get(name, False) != latched:
                    self.coil_latched[name] = latched
                    changed = True
            self.energized_nets = {union.find(n) for n in source}
            if not changed:
                self.unstable = False
                return
        self.unstable = True
        self.message = "Schaltung oszilliert – Auswertung nach Rundenlimit gestoppt."

    # -- Zeitrelais ------------------------------------------------------------
    def tick(self, dt):
        """Takt (Sekunden): Zeitrelais-Verzögerungen fortsetzen."""
        changed = False
        for coil in self.coils:
            if coil.symbol_id != "timer_coil":
                continue
            name = self._name_of(coil)
            delay = self.relay_delay(name)
            coil_on = self.coil_latched.get(name, False)
            contact_on = self.timer_contact.get(name, False)
            if coil_on != contact_on:
                deadline, _target = self.timers.get(name, (None, None))
                if deadline is None:
                    # Timer starten: Kontakt wechselt nach Verzögerung
                    self.timers[name] = (time.monotonic() + (delay or 0.0), coil_on)
                elif time.monotonic() >= deadline:
                    self.timer_contact[name] = coil_on
                    self.timers[name] = (None, None)
                    changed = True
            else:
                self.timers[name] = (None, None)
        self.evaluate()
        return changed

    # -- Anfragen für die Darstellung -----------------------------------------
    def wire_energized(self, wire):
        node = self.net.wire_node(wire)
        return node in self.energized_nets

    def reset(self):
        self.manual.clear()
        self.coil_latched.clear()
        self.timer_contact.clear()
        self.timers.clear()
        self.active.clear()
        self.evaluate()

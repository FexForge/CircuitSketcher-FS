"""Netzliste: verbindet Bauteil-Pole und Leitungen zu elektrischen Knoten.

Konnektivität wie in der Zeichnung sichtbar: Punkte (Leitungsenden, T-Punkte,
Pole) mit identischer Position gehören zusammen; eine Leitung, die einen
fremden Punkt nur durchläuft, verbindet ihn (T-Verzweigung) — gleiche
Konvention wie die automatischen Knotenpunkte.
"""


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, key):
        self.parent.setdefault(key, key)
        if self.parent[key] != key:
            self.parent[key] = self.find(self.parent[key])
        return self.parent[key]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def groups(self):
        out = {}
        for key in self.parent:
            out.setdefault(self.find(key), set()).add(key)
        return out


def _key(point):
    return (round(point.x()), round(point.y()))


def _point_on_segment(point, start, end, eps=1.0):
    dx, dy = end.x() - start.x(), end.y() - start.y()
    seg_sq = dx * dx + dy * dy
    if seg_sq == 0:
        return False
    t = ((point.x() - start.x()) * dx + (point.y() - start.y()) * dy) / seg_sq
    if t <= 0.001 or t >= 0.999:
        return False
    foot_x, foot_y = start.x() + t * dx, start.y() + t * dy
    return abs(point.x() - foot_x) + abs(point.y() - foot_y) <= eps


class Netlist:
    """Ergebnis des Netzlisten-Aufbaus.

    - uf: UnionFind über Punktschlüssel
    - pins: {component: [knoten_key, ...]} je Pol (Index == Pol-Index)
    - wires: {wire: leitender Knoten (beide Enden vereinigt)}
    - wires_by_node, pins_by_node: umgekehrte Sicht
    """

    def __init__(self):
        self.uf = UnionFind()
        self.pins = {}
        self.wires = {}
        self._components = []
        self._wire_items = []

    @classmethod
    def from_scene(cls, scene, exclude_wire=None):
        from ..components.symbol_component import SymbolComponent
        from ..components.wire import Wire
        net = cls()
        wires = [w for w in scene.items()
                 if isinstance(w, Wire) and w is not exclude_wire and w.line().length() > 0]
        net._wire_items = wires

        # Schienen (L+/M) leiten wie Leitungen: ihr Pol-zu-Pol-Segment ist ein
        # durchgehender Leiter, auf den andere Leitungen T-förmig andocken.
        rail_segments = []
        for item in scene.items():
            if not isinstance(item, SymbolComponent):
                continue
            if getattr(item, "symbol_id", "") in ("rail_plus", "rail_minus"):
                poles = item.get_pole_points()
                if len(poles) == 2:
                    rail_segments.append((poles[0], poles[1]))

        segments = [(w.start_point, w.end_point) for w in wires] + rail_segments
        for start, end in segments:
            net.uf.union(_key(start), _key(end))
        # T-Verzweigungen: Endpunkt auf fremdem Segment verbindet beide
        for start, end in segments:
            for point in (start, end):
                for other_start, other_end in segments:
                    if other_start is point or other_end is point:
                        continue
                    if _point_on_segment(point, other_start, other_end):
                        net.uf.union(_key(point), _key(other_start))
        for wire in wires:
            net.wires[wire] = net.uf.find(_key(wire.start_point))
        for item in scene.items():
            if not isinstance(item, SymbolComponent):
                continue
            getter = getattr(item, "get_pole_points", None)
            if not callable(getter):
                continue
            poles = getter()
            if poles:
                net.pins[item] = [_key(p) for p in poles]
                net._components.append(item)
        return net

    def clone_union(self):
        """Kopie der Knoten-Vereinigung (z. B. um leitende Bauteile obendrauf
        zu vereinigen, ohne die Basis-Netzliste zu verändern)."""
        clone = UnionFind()
        for members in self.uf.groups().values():
            keys = list(members)
            for key in keys[1:]:
                clone.union(keys[0], key)
        return clone

    def node_of_pin(self, component, index):
        keys = self.pins.get(component)
        if keys and 0 <= index < len(keys):
            return self.uf.find(keys[index])
        return None

    def wire_node(self, wire):
        node = self.wires.get(wire)
        return self.uf.find(node) if node is not None else None

    def components(self):
        return list(self._components)

    def wire_items(self):
        return list(self._wire_items)

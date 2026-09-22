"""
Symbol library loader for circuit components.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def _app_base_dir() -> Path:
    """Basisverzeichnis für die Symbol-Bibliothek.

    Im Normalfall (python main.py) liegt es zwei Ebenen über dieser Datei.
    Bei einer mit PyInstaller eingefrorenen EXE liegen eingebettete Daten
    im Entpack-Verzeichnis sys._MEIPASS (onedir: <App>/_internal).
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[2]


def _symbols_dir() -> Path:
    """Verzeichnis der Symbol-Bibliothek.

    Eingefrorene EXE: bevorzugt ein 'symbols'-Ordner NEBEN der EXE
    (vom Installer dorthin gelegt bzw. vom Nutzer gepflegt) — Änderungen
    darin bleiben dauerhaft erhalten. Fallback: eingebettete Kopie unter
    sys._MEIPASS/symbols.
    """
    base = _app_base_dir()
    if getattr(sys, "frozen", False):
        beside_exe = Path(sys.executable).parent / "symbols"
        if beside_exe.is_dir():
            return beside_exe
    return base / "symbols"


SYMBOLS_DIR = _symbols_dir()


@dataclass
class OrientationData:
    """Holds drawing data for one orientation of a symbol."""

    name: str
    items: List[Dict]
    placeholders: List[Dict]
    connection_points: List[List[float]]
    bounds: Dict[str, List[float]]
    origin: List[float]

    @property
    def width(self) -> float:
        return float(self.bounds["max"][0] - self.bounds["min"][0])

    @property
    def height(self) -> float:
        return float(self.bounds["max"][1] - self.bounds["min"][1])


@dataclass
class SymbolDefinition:
    """Represents a drawable circuit symbol."""

    symbol_id: str
    name: str
    category: str
    default_values: Dict[str, str]
    orientations: Dict[str, OrientationData]
    file_path: Path
    description: Optional[str] = None
    # Versteckte Symbole erscheinen nicht in der Palette (bleiben aber für
    # gespeicherte Dateien ladbar und im Symbol-Editor bearbeitbar).
    hidden: bool = False

    def orientation_names(self) -> Iterable[str]:
        return self.orientations.keys()

    def get_orientation(self, name: str) -> OrientationData:
        return self.orientations[name]


def load_symbol_definitions(
    symbol_dir: Optional[Path] = None,
) -> Tuple[List[SymbolDefinition], List[Tuple[Path, str]]]:
    """
    Load all symbol definitions from the given directory.

    Returns a tuple of (definitions, errors). Errors contain pairs of
    the file path and the error message describing the issue.
    """
    directory = symbol_dir or SYMBOLS_DIR
    definitions: List[SymbolDefinition] = []
    errors: List[Tuple[Path, str]] = []

    if not directory.exists():
        return definitions, errors

    for path in sorted(directory.glob("*.symbol.json")):
        try:
            definition = _load_symbol_file(path)
        except Exception as exc:  # pylint: disable=broad-except
            errors.append((path, str(exc)))
        else:
            definitions.append(definition)

    definitions.sort(key=lambda d: (d.category.lower(), d.name.lower()))
    return definitions, errors


def _load_symbol_file(path: Path) -> SymbolDefinition:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    symbol_id = raw.get("id") or path.stem
    name = raw.get("name") or symbol_id
    category = raw.get("category") or "Unkategorisiert"
    description = raw.get("description")
    default_values = raw.get("default_values", {})

    orientations_raw = raw.get("orientations", {})
    if not orientations_raw:
        raise ValueError("Symboldefinition enthält keine Orientierungen.")

    orientations: Dict[str, OrientationData] = {}
    for orientation_name, orientation_data in orientations_raw.items():
        orientations[orientation_name] = _build_orientation(
            orientation_name, orientation_data
        )

    required_orientations = {"horizontal", "vertical"}
    if not required_orientations.issubset(orientations):
        missing = required_orientations - set(orientations)
        raise ValueError(
            f"Fehlende Orientierung(en): {', '.join(sorted(missing))}."
        )

    return SymbolDefinition(
        symbol_id=symbol_id,
        name=name,
        category=category,
        default_values=default_values,
        orientations=orientations,
        file_path=path,
        description=description,
        hidden=bool(raw.get("hidden", False)),
    )


def _build_orientation(name: str, data: Dict) -> OrientationData:
    items = list(data.get("items", []))
    placeholders = list(data.get("placeholders", []))
    connection_points = list(data.get("connection_points", []))
    bounds = data.get("bounds")

    if not items:
        raise ValueError(f"Orientierung '{name}' enthält keine Zeichenobjekte.")

    bounds = bounds or _derive_bounds(items, placeholders, connection_points)
    origin = data.get("origin")
    if origin is None:
        origin = _derive_origin(bounds)

    return OrientationData(
        name=name,
        items=items,
        placeholders=placeholders,
        connection_points=connection_points,
        bounds=bounds,
        origin=[float(origin[0]), float(origin[1])],
    )


def _derive_bounds(
    items: List[Dict],
    placeholders: List[Dict],
    connection_points: List[List[float]],
) -> Dict[str, List[float]]:
    xs: List[float] = []
    ys: List[float] = []

    for item in items:
        item_type = item.get("type")
        if item_type == "line":
            start = item.get("start", [0, 0])
            end = item.get("end", [0, 0])
            xs.extend([float(start[0]), float(end[0])])
            ys.extend([float(start[1]), float(end[1])])
        elif item_type == "circle":
            center = item.get("center", [0, 0])
            radius = float(item.get("radius", 0))
            xs.extend([float(center[0] - radius), float(center[0] + radius)])
            ys.extend([float(center[1] - radius), float(center[1] + radius)])

    for point in connection_points:
        xs.append(float(point[0]))
        ys.append(float(point[1]))

    for placeholder in placeholders:
        position = placeholder.get("position")
        if position:
            xs.append(float(position[0]))
            ys.append(float(position[1]))

    if not xs:
        xs = [0.0]
    if not ys:
        ys = [0.0]

    return {
        "min": [min(xs), min(ys)],
        "max": [max(xs), max(ys)],
    }


def _derive_origin(bounds: Dict[str, List[float]]) -> List[float]:
    return [
        (float(bounds["min"][0]) + float(bounds["max"][0])) / 2.0,
        (float(bounds["min"][1]) + float(bounds["max"][1])) / 2.0,
    ]

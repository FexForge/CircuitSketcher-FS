"""
CircuitSketcher - Main Entry Point
A visual drag-and-drop tool for drawing electrical circuits
"""
import sys
from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def _app_base_dir() -> Path:
    """Basisverzeichnis der Anwendung (PyInstaller-frozen-safe)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("CircuitSketcherFS")
    app.setOrganizationName("CircuitSketcherFS")
    app.setWindowIcon(QIcon(str(_app_base_dir() / "assets" / "favicon.ico")))

    # Create and show main window
    window = MainWindow()
    window.show()

    # Datei-Argument (Doppelklick auf eine .sz-Datei) direkt öffnen
    for arg in sys.argv[1:]:
        if arg.lower().endswith((".sz", ".json")) and Path(arg).is_file():
            window.load_circuit(arg)
            break

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

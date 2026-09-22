"""Gemeinsame Fixtures für die SchaltungsZeichner-Testsuite.

Läuft komplett offscreen (QT_QPA_PLATFORM=offscreen), damit die Tests auch ohne
Display/CI laufen. Dialog-Blocker (QMessageBox) werden neutralisiert.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_API", "pyqt5")

import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture()
def main_window(qapp, tmp_path, monkeypatch):
    """MainWindow mit neutralisierten Modal-Dialogen und isolierten QSettings.

    QSettings werden auf ein Temp-Verzeichnis umgeleitet, damit Tests die
    gespeicherte Paletten-/Dateihistorie des Nutzers nicht anfassen.
    """
    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "critical", staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(QMessageBox, "question",
                        staticmethod(lambda *a, **k: QMessageBox.Yes))
    monkeypatch.setenv("QT_QSETTINGS_HOME", str(tmp_path))
    # QSettings liegt outside HOME unter Windows in der Registry; die Recent-
    # Liste der Tests isolieren wir per eindeutigem Applikationsnamen.
    from PyQt5.QtCore import QSettings
    QSettings("SchaltungsZeichnerTest", "tests").clear()

    from src.ui.main_window import MainWindow
    window = MainWindow()
    yield window
    window.close()

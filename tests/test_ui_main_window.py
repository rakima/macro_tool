from app.models import RuleSet
from app.ui.main_window import UiDependencyError

import pytest


def test_create_main_window_raises_clear_error_without_pyside6(monkeypatch):
    import app.ui.main_window as main_window

    def fail_import():
        raise UiDependencyError("PySide6 is not installed")

    monkeypatch.setattr(main_window, "import_qt_widgets", fail_import)

    with pytest.raises(UiDependencyError, match="PySide6"):
        main_window.create_main_window(RuleSet(rules=[]))


def test_import_qt_widgets_returns_required_widget_names_when_pyside6_is_available():
    pytest.importorskip("PySide6", reason="PySide6 is not installed")

    from app.ui.main_window import import_qt_widgets

    qt = import_qt_widgets()

    assert "QDialog" in qt
    assert "QMainWindow" in qt
    assert "QListWidget" in qt
    assert "QPlainTextEdit" in qt
    assert "QTimer" in qt

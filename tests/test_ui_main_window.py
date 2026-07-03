from app.models import RuleSet
from app.ui.main_window import UiDependencyError, rectangles_overlap

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


def test_rectangles_overlap_returns_true_when_areas_intersect():
    assert rectangles_overlap((10, 10, 100, 100), (50, 50, 20, 20)) is True


def test_rectangles_overlap_returns_false_when_areas_do_not_intersect():
    assert rectangles_overlap((10, 10, 100, 100), (110, 10, 20, 20)) is False

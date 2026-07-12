from app.models import RuleSet
from app.detector import MatchResult
from app.runner import RuleRunResult
from app.ui.main_window import (
    UiDependencyError,
    format_rule_test_result,
    format_score_percent,
    is_check_area_position,
    rectangles_overlap,
)

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


def test_is_check_area_position_detects_left_edge():
    assert is_check_area_position(12) is True
    assert is_check_area_position(40) is False


def test_format_score_percent():
    assert format_score_percent(0.842) == "84.2%"


def test_format_rule_test_result_returns_not_run_without_result():
    assert format_rule_test_result(None, confidence=0.85) == ["Last Test: not run"]


def test_format_rule_test_result_returns_matched_summary():
    result = RuleRunResult(
        rule_name="Rule",
        matched=True,
        score=0.95,
        match=MatchResult(
            rule_name="Rule",
            score=0.95,
            x=10,
            y=20,
            width=10,
            height=10,
        ),
    )

    assert format_rule_test_result(result, confidence=0.85) == [
        "Last Test: matched (95.0% >= 85.0%)",
        "Match: x=10, y=20, center=(15, 25)",
    ]


def test_format_rule_test_result_returns_below_threshold_summary():
    result = RuleRunResult(rule_name="Rule", score=0.842)

    assert format_rule_test_result(result, confidence=0.85) == [
        "Last Test: below threshold (84.2% < 85.0%)"
    ]


def test_format_rule_test_result_returns_error_summary():
    result = RuleRunResult(rule_name="Rule", error="template missing")

    assert format_rule_test_result(result, confidence=0.85) == [
        "Last Test: error",
        "Error: template missing",
    ]

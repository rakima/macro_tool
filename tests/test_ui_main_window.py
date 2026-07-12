from pathlib import Path

from app.models import RuleSet
from app.detector import MatchResult
from app.runner import RuleRunResult
from app.ui.main_window import (
    UiDependencyError,
    format_rule_list_text,
    format_rule_test_result,
    format_score_percent,
    is_check_area_position,
    is_escape_key,
    is_valid_rule_row,
    rectangles_overlap,
    rule_profile_base_dir,
    resolve_rule_image_path,
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

    assert "QComboBox" in qt
    assert "QDialog" in qt
    assert "QInputDialog" in qt
    assert "QMainWindow" in qt
    assert "QListWidget" in qt
    assert "QPlainTextEdit" in qt
    assert "QImage" in qt
    assert "QPixmap" in qt
    assert "QTimer" in qt


def test_rectangles_overlap_returns_true_when_areas_intersect():
    assert rectangles_overlap((10, 10, 100, 100), (50, 50, 20, 20)) is True


def test_rectangles_overlap_returns_false_when_areas_do_not_intersect():
    assert rectangles_overlap((10, 10, 100, 100), (110, 10, 20, 20)) is False


def test_is_check_area_position_detects_left_edge():
    assert is_check_area_position(12) is True
    assert is_check_area_position(40) is False


def test_is_escape_key_matches_escape_only():
    assert is_escape_key(27, 27) is True
    assert is_escape_key(65, 27) is False


def test_is_valid_rule_row_rejects_out_of_range_rows():
    assert is_valid_rule_row(0, 1) is True
    assert is_valid_rule_row(-1, 1) is False
    assert is_valid_rule_row(1, 1) is False
    assert is_valid_rule_row(0, 0) is False


def test_resolve_rule_image_path_uses_base_dir_for_relative_path(tmp_path):
    assert resolve_rule_image_path("image/button.png", tmp_path) == tmp_path / "image" / "button.png"


def test_resolve_rule_image_path_leaves_absolute_path(tmp_path):
    image_path = tmp_path / "button.png"

    assert resolve_rule_image_path(str(image_path), tmp_path) == image_path


def test_rule_profile_base_dir_uses_rules_parent_for_profile_path():
    assert rule_profile_base_dir("rules/tower.json") == Path(".")


def test_rule_profile_base_dir_uses_rules_file_parent_for_legacy_path():
    assert rule_profile_base_dir("rules.json") == Path(".")


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


def test_format_rule_list_text_returns_name_without_result():
    assert format_rule_list_text("Rule") == "Rule"


def test_format_rule_list_text_returns_clicked_score():
    result = RuleRunResult(rule_name="Rule", triggered=True, score=0.95)

    assert format_rule_list_text("Rule", result) == "Rule  [clicked 95.0%]"


def test_format_rule_list_text_returns_matched_score():
    result = RuleRunResult(rule_name="Rule", matched=True, score=0.91)

    assert format_rule_list_text("Rule", result) == "Rule  [matched 91.0%]"


def test_format_rule_list_text_returns_below_score():
    result = RuleRunResult(rule_name="Rule", score=0.842)

    assert format_rule_list_text("Rule", result) == "Rule  [below 84.2%]"


def test_format_rule_list_text_returns_cooldown():
    result = RuleRunResult(rule_name="Rule", skipped_cooldown=True)

    assert format_rule_list_text("Rule", result) == "Rule  [cooldown]"


def test_format_rule_list_text_returns_error():
    result = RuleRunResult(rule_name="Rule", error="failed")

    assert format_rule_list_text("Rule", result) == "Rule  [error]"

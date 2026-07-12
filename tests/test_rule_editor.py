import cv2
import numpy as np
import pytest

from app.models import Action, Offset, Region, Rule
from app.ui.main_window import UiDependencyError
from app.ui.rule_editor import (
    RuleFormData,
    RuleFormValidationError,
    default_captured_template_path,
    safe_template_file_stem,
    save_captured_template,
    validate_detection_image,
)


def write_image(path, image: np.ndarray) -> None:
    success, encoded_image = cv2.imencode(".png", image)
    assert success
    encoded_image.tofile(str(path))


def make_rule() -> Rule:
    return Rule(
        enabled=True,
        name="Click start button",
        image="images/start_button.png",
        region=Region(x=10, y=20, width=30, height=40),
        confidence=0.9,
        action=Action(type="click", button="right", offset=Offset(x=1, y=-2)),
        cooldown=1.5,
    )


def test_rule_form_data_from_rule():
    data = RuleFormData.from_rule(make_rule())

    assert data.name == "Click start button"
    assert data.image == "images/start_button.png"
    assert data.region_x == 10
    assert data.region_y == 20
    assert data.region_width == 30
    assert data.region_height == 40
    assert data.confidence == 0.9
    assert data.button == "right"
    assert data.offset_x == 1
    assert data.offset_y == -2
    assert data.cooldown == 1.5


def test_rule_form_data_to_rule():
    data = RuleFormData(
        enabled=False,
        name="New rule",
        image="images/new.png",
        region_x=1,
        region_y=2,
        region_width=3,
        region_height=4,
        confidence=0.8,
        button="middle",
        offset_x=5,
        offset_y=6,
        cooldown=2.0,
    )

    rule = data.to_rule()

    assert rule.enabled is False
    assert rule.name == "New rule"
    assert rule.image == "images/new.png"
    assert rule.region == Region(x=1, y=2, width=3, height=4)
    assert rule.confidence == 0.8
    assert rule.action == Action(type="click", button="middle", offset=Offset(x=5, y=6))
    assert rule.cooldown == 2.0


def test_rule_form_data_rejects_blank_name():
    data = RuleFormData(image="images/new.png")

    with pytest.raises(RuleFormValidationError, match="Rule name"):
        data.validate()


def test_rule_form_data_rejects_blank_image():
    data = RuleFormData(name="New rule")

    with pytest.raises(RuleFormValidationError, match="Detection image"):
        data.validate()


def test_rule_form_data_to_rule_validates_before_model_creation():
    data = RuleFormData(name="New rule")

    with pytest.raises(RuleFormValidationError, match="Detection image"):
        data.to_rule()


def test_validate_detection_image_accepts_existing_image(tmp_path):
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    write_image(tmp_path / "button.png", image)

    validate_detection_image("button.png", base_dir=tmp_path)


def test_validate_detection_image_rejects_missing_image(tmp_path):
    with pytest.raises(RuleFormValidationError, match="does not exist"):
        validate_detection_image("missing.png", base_dir=tmp_path)


def test_validate_detection_image_rejects_invalid_image(tmp_path):
    path = tmp_path / "broken.png"
    path.write_text("not an image", encoding="utf-8")

    with pytest.raises(RuleFormValidationError, match="decoded"):
        validate_detection_image("broken.png", base_dir=tmp_path)


def test_validate_detection_image_rejects_fully_transparent_png(tmp_path):
    image = np.zeros((10, 10, 4), dtype=np.uint8)
    write_image(tmp_path / "transparent.png", image)

    with pytest.raises(RuleFormValidationError, match="fully transparent"):
        validate_detection_image("transparent.png", base_dir=tmp_path)


def test_safe_template_file_stem_removes_unsafe_characters():
    assert safe_template_file_stem("Start Button!?") == "Start_Button"


def test_safe_template_file_stem_uses_fallback_for_blank_name():
    assert safe_template_file_stem("   ") == "template"


def test_default_captured_template_path_uses_image_directory(tmp_path):
    assert default_captured_template_path(tmp_path, "Start Button") == tmp_path / "image" / "Start_Button.png"


def test_save_captured_template_writes_png(tmp_path):
    image = np.zeros((4, 5, 3), dtype=np.uint8)
    image[:, :] = (0, 0, 255)
    output_path = tmp_path / "画像" / "button.png"

    save_captured_template(output_path, image)

    decoded = cv2.imdecode(np.fromfile(str(output_path), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    assert decoded is not None
    assert decoded.shape == (4, 5, 3)


def test_create_rule_editor_raises_clear_error_without_pyside6(monkeypatch):
    import app.ui.rule_editor as rule_editor

    def fail_import():
        raise UiDependencyError("PySide6 is not installed")

    monkeypatch.setattr(rule_editor, "import_qt_widgets", fail_import)

    with pytest.raises(UiDependencyError, match="PySide6"):
        rule_editor.create_rule_editor()


def test_import_qt_widgets_returns_required_widget_names_when_pyside6_is_available():
    pytest.importorskip("PySide6", reason="PySide6 is not installed")

    from app.ui.rule_editor import import_qt_widgets

    qt = import_qt_widgets()

    assert "QDialog" in qt
    assert "QLineEdit" in qt
    assert "QMessageBox" in qt
    assert "QDoubleSpinBox" in qt

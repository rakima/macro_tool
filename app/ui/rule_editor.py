"""Rule editor dialog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.models import Action, Offset, Region, Rule
from app.ui.main_window import UiDependencyError


class RuleFormValidationError(ValueError):
    """Raised when rule editor form data is invalid."""


def resolve_image_path(image: str, base_dir: str | Path | None = None) -> Path:
    image_path = Path(image)
    if base_dir is not None and not image_path.is_absolute():
        return Path(base_dir) / image_path
    return image_path


def validate_detection_image(image: str, base_dir: str | Path | None = None) -> None:
    image_path = resolve_image_path(image, base_dir)
    if not image_path.exists():
        raise RuleFormValidationError(f"Detection image does not exist: {image_path}")
    if not image_path.is_file():
        raise RuleFormValidationError(f"Detection image is not a file: {image_path}")

    try:
        image_data = np.fromfile(str(image_path), dtype=np.uint8)
    except OSError as error:
        raise RuleFormValidationError(f"Could not read detection image: {image_path}") from error

    decoded_image = cv2.imdecode(image_data, cv2.IMREAD_UNCHANGED)
    if decoded_image is None:
        raise RuleFormValidationError(f"Detection image could not be decoded: {image_path}")
    if len(decoded_image.shape) == 3 and decoded_image.shape[2] == 4 and not np.any(decoded_image[:, :, 3]):
        raise RuleFormValidationError(f"Detection image mask is fully transparent: {image_path}")


@dataclass(frozen=True)
class RuleFormData:
    enabled: bool = True
    name: str = ""
    image: str = ""
    region_x: int = 0
    region_y: int = 0
    region_width: int = 1
    region_height: int = 1
    confidence: float = 0.85
    action_type: str = "click"
    button: str = "left"
    offset_x: int = 0
    offset_y: int = 0
    cooldown: float = 1.0

    def validate(self) -> None:
        if not self.name.strip():
            raise RuleFormValidationError("Rule name is required.")
        if not self.image.strip():
            raise RuleFormValidationError("Detection image is required.")
        if self.region_width <= 0:
            raise RuleFormValidationError("Region width must be greater than 0.")
        if self.region_height <= 0:
            raise RuleFormValidationError("Region height must be greater than 0.")
        if not 0.0 <= self.confidence <= 1.0:
            raise RuleFormValidationError("Confidence must be between 0.0 and 1.0.")
        if self.cooldown < 0:
            raise RuleFormValidationError("Cooldown must be 0 or greater.")

    @classmethod
    def from_rule(cls, rule: Rule) -> "RuleFormData":
        return cls(
            enabled=rule.enabled,
            name=rule.name,
            image=rule.image,
            region_x=rule.region.x,
            region_y=rule.region.y,
            region_width=rule.region.width,
            region_height=rule.region.height,
            confidence=rule.confidence,
            action_type=rule.action.type,
            button=rule.action.button,
            offset_x=rule.action.offset.x,
            offset_y=rule.action.offset.y,
            cooldown=rule.cooldown,
        )

    def to_rule(self) -> Rule:
        self.validate()
        return Rule(
            enabled=self.enabled,
            name=self.name,
            image=self.image,
            region=Region(
                x=self.region_x,
                y=self.region_y,
                width=self.region_width,
                height=self.region_height,
            ),
            confidence=self.confidence,
            action=Action(
                type=self.action_type,
                button=self.button,
                offset=Offset(x=self.offset_x, y=self.offset_y),
            ),
            cooldown=self.cooldown,
        )


def import_qt_widgets():
    try:
        from PySide6.QtWidgets import (  # type: ignore[import-not-found]
            QCheckBox,
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QDoubleSpinBox,
            QFileDialog,
            QFormLayout,
            QHBoxLayout,
            QLineEdit,
            QMessageBox,
            QPushButton,
            QSpinBox,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as error:
        raise UiDependencyError("PySide6 is not installed") from error

    return {
        "QCheckBox": QCheckBox,
        "QComboBox": QComboBox,
        "QDialog": QDialog,
        "QDialogButtonBox": QDialogButtonBox,
        "QDoubleSpinBox": QDoubleSpinBox,
        "QFileDialog": QFileDialog,
        "QFormLayout": QFormLayout,
        "QHBoxLayout": QHBoxLayout,
        "QLineEdit": QLineEdit,
        "QMessageBox": QMessageBox,
        "QPushButton": QPushButton,
        "QSpinBox": QSpinBox,
        "QVBoxLayout": QVBoxLayout,
        "QWidget": QWidget,
    }


def create_rule_editor(rule: Rule | None = None, parent=None, base_dir: str | Path | None = None):
    """Create a rule editor dialog."""
    qt = import_qt_widgets()
    QCheckBox = qt["QCheckBox"]
    QComboBox = qt["QComboBox"]
    QDialog = qt["QDialog"]
    QDialogButtonBox = qt["QDialogButtonBox"]
    QDoubleSpinBox = qt["QDoubleSpinBox"]
    QFileDialog = qt["QFileDialog"]
    QFormLayout = qt["QFormLayout"]
    QHBoxLayout = qt["QHBoxLayout"]
    QLineEdit = qt["QLineEdit"]
    QMessageBox = qt["QMessageBox"]
    QPushButton = qt["QPushButton"]
    QSpinBox = qt["QSpinBox"]
    QVBoxLayout = qt["QVBoxLayout"]
    QWidget = qt["QWidget"]

    class RuleEditorDialog(QDialog):
        def __init__(self, initial_rule: Rule | None = None, parent_widget=None) -> None:
            super().__init__(parent_widget)
            self.setWindowTitle("Rule Editor")
            self.setMinimumWidth(520)
            self._build_ui()
            self.set_form_data(RuleFormData.from_rule(initial_rule) if initial_rule else RuleFormData())

        def _build_ui(self) -> None:
            layout = QVBoxLayout(self)
            form = QFormLayout()
            form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

            self.enabled_input = QCheckBox("Enabled")
            form.addRow("State", self.enabled_input)

            self.name_input = QLineEdit()
            form.addRow("Rule name", self.name_input)

            image_row = QWidget()
            image_layout = QHBoxLayout(image_row)
            image_layout.setContentsMargins(0, 0, 0, 0)
            self.image_input = QLineEdit()
            self.image_button = QPushButton("Browse")
            self.mask_button = QPushButton("Edit Mask")
            self.image_button.clicked.connect(self._browse_image)
            self.mask_button.clicked.connect(self._edit_mask)
            image_layout.addWidget(self.image_input, 1)
            image_layout.addWidget(self.image_button)
            image_layout.addWidget(self.mask_button)
            form.addRow("Detection image", image_row)

            region_row = QWidget()
            region_layout = QHBoxLayout(region_row)
            region_layout.setContentsMargins(0, 0, 0, 0)
            self.region_x_input = self._make_int_input(-99999, 99999)
            self.region_y_input = self._make_int_input(-99999, 99999)
            self.region_width_input = self._make_int_input(1, 99999)
            self.region_height_input = self._make_int_input(1, 99999)
            self.region_button = QPushButton("Select")
            self.region_button.clicked.connect(self._select_region)
            for widget in (
                self.region_x_input,
                self.region_y_input,
                self.region_width_input,
                self.region_height_input,
                self.region_button,
            ):
                region_layout.addWidget(widget)
            form.addRow("Region x/y/w/h", region_row)

            self.confidence_input = QDoubleSpinBox()
            self.confidence_input.setRange(0.0, 1.0)
            self.confidence_input.setSingleStep(0.01)
            self.confidence_input.setDecimals(2)
            form.addRow("Confidence", self.confidence_input)

            self.action_type_input = QComboBox()
            self.action_type_input.addItem("click")
            form.addRow("Action", self.action_type_input)

            self.button_input = QComboBox()
            self.button_input.addItems(["left", "right", "middle"])
            form.addRow("Button", self.button_input)

            offset_row = QWidget()
            offset_layout = QHBoxLayout(offset_row)
            offset_layout.setContentsMargins(0, 0, 0, 0)
            self.offset_x_input = self._make_int_input(-99999, 99999)
            self.offset_y_input = self._make_int_input(-99999, 99999)
            self.offset_button = QPushButton("Select")
            self.offset_button.clicked.connect(self._select_click_position)
            offset_layout.addWidget(self.offset_x_input)
            offset_layout.addWidget(self.offset_y_input)
            offset_layout.addWidget(self.offset_button)
            form.addRow("Click offset x/y", offset_row)

            self.cooldown_input = QDoubleSpinBox()
            self.cooldown_input.setRange(0.0, 9999.0)
            self.cooldown_input.setSingleStep(0.1)
            self.cooldown_input.setDecimals(2)
            form.addRow("Cooldown", self.cooldown_input)

            layout.addLayout(form)
            self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            layout.addWidget(self.buttons)

        def _make_int_input(self, minimum: int, maximum: int):
            input_widget = QSpinBox()
            input_widget.setRange(minimum, maximum)
            return input_widget

        def _browse_image(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select detection image",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp);;All files (*.*)",
            )
            if path:
                self.image_input.setText(self._display_image_path(path))

        def _display_image_path(self, path: str) -> str:
            image_path = Path(path)
            if base_dir is None or not image_path.is_absolute():
                return path

            try:
                return image_path.resolve().relative_to(Path(base_dir).resolve()).as_posix()
            except ValueError:
                return path

        def _resolve_image_path(self, image_text: str) -> Path:
            return resolve_image_path(image_text, base_dir)

        def _edit_mask(self) -> None:
            from app.ui.mask_editor import create_mask_editor, default_masked_image_path

            image_text = self.image_input.text().strip()
            if not image_text:
                QMessageBox.warning(self, "Image required", "Select a detection image first.")
                return

            image_path = self._resolve_image_path(image_text)
            output_path = default_masked_image_path(image_path)

            try:
                dialog = create_mask_editor(image_path, output_path=output_path, parent=self)
            except ValueError as error:
                QMessageBox.warning(self, "Could not open image", str(error))
                return

            if dialog.exec() != QDialog.Accepted:
                return

            self.image_input.setText(self._display_image_path(str(dialog.masked_image_path())))

        def _select_region(self) -> None:
            from app.ui.region_selector import create_region_selector

            dialog = create_region_selector(parent=self)
            if dialog is None:
                return
            if dialog.exec() != QDialog.Accepted:
                return

            region = dialog.selected_region()
            self.region_x_input.setValue(region.x)
            self.region_y_input.setValue(region.y)
            self.region_width_input.setValue(region.width)
            self.region_height_input.setValue(region.height)

        def _select_click_position(self) -> None:
            from app.ui.click_position_selector import create_click_position_selector

            image_text = self.image_input.text().strip()
            if not image_text:
                QMessageBox.warning(self, "Image required", "Select a detection image first.")
                return

            image_path = self._resolve_image_path(image_text)

            try:
                dialog = create_click_position_selector(
                    image_path,
                    Offset(x=self.offset_x_input.value(), y=self.offset_y_input.value()),
                    parent=self,
                )
            except ValueError as error:
                QMessageBox.warning(self, "Could not open image", str(error))
                return

            if dialog.exec() != QDialog.Accepted:
                return

            offset = dialog.selected_offset()
            self.offset_x_input.setValue(offset.x)
            self.offset_y_input.setValue(offset.y)

        def form_data(self) -> RuleFormData:
            return RuleFormData(
                enabled=self.enabled_input.isChecked(),
                name=self.name_input.text(),
                image=self.image_input.text(),
                region_x=self.region_x_input.value(),
                region_y=self.region_y_input.value(),
                region_width=self.region_width_input.value(),
                region_height=self.region_height_input.value(),
                confidence=self.confidence_input.value(),
                action_type=self.action_type_input.currentText(),
                button=self.button_input.currentText(),
                offset_x=self.offset_x_input.value(),
                offset_y=self.offset_y_input.value(),
                cooldown=self.cooldown_input.value(),
            )

        def set_form_data(self, data: RuleFormData) -> None:
            self.enabled_input.setChecked(data.enabled)
            self.name_input.setText(data.name)
            self.image_input.setText(data.image)
            self.region_x_input.setValue(data.region_x)
            self.region_y_input.setValue(data.region_y)
            self.region_width_input.setValue(data.region_width)
            self.region_height_input.setValue(data.region_height)
            self.confidence_input.setValue(data.confidence)
            self.action_type_input.setCurrentText(data.action_type)
            self.button_input.setCurrentText(data.button)
            self.offset_x_input.setValue(data.offset_x)
            self.offset_y_input.setValue(data.offset_y)
            self.cooldown_input.setValue(data.cooldown)

        def rule(self) -> Rule:
            return self.form_data().to_rule()

        def accept(self) -> None:
            try:
                self.rule()
                validate_detection_image(self.image_input.text(), base_dir)
            except RuleFormValidationError as error:
                QMessageBox.warning(self, "Invalid rule", str(error))
                return

            if self._looks_like_default_region():
                answer = QMessageBox.question(
                    self,
                    "Confirm region",
                    "The search region is still 1x1 at x=0, y=0. Save this rule anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if answer != QMessageBox.Yes:
                    return

            super().accept()

        def _looks_like_default_region(self) -> bool:
            return (
                self.region_x_input.value() == 0
                and self.region_y_input.value() == 0
                and self.region_width_input.value() == 1
                and self.region_height_input.value() == 1
            )

    return RuleEditorDialog(rule, parent)

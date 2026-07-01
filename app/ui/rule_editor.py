"""Rule editor dialog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models import Action, Offset, Region, Rule
from app.ui.main_window import UiDependencyError


class RuleFormValidationError(ValueError):
    """Raised when rule editor form data is invalid."""


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
            self.image_button.clicked.connect(self._browse_image)
            image_layout.addWidget(self.image_input, 1)
            image_layout.addWidget(self.image_button)
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
            offset_layout.addWidget(self.offset_x_input)
            offset_layout.addWidget(self.offset_y_input)
            form.addRow("Offset x/y", offset_row)

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
            except RuleFormValidationError as error:
                QMessageBox.warning(self, "Invalid rule", str(error))
                return

            super().accept()

    return RuleEditorDialog(rule, parent)

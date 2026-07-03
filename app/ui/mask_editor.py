"""Mask editor for creating transparent PNG templates."""

from __future__ import annotations

from pathlib import Path

from app.ui.main_window import UiDependencyError


def default_masked_image_path(image_path: str | Path) -> Path:
    """Return the default output path for a masked copy of an image."""
    path = Path(image_path)
    if path.name.lower().endswith(".masked.png") and not path.name.lower().endswith(".png.masked.png"):
        return path

    stem_path = path.with_suffix("")
    if stem_path.name.lower().endswith(".masked"):
        stem_path = stem_path.with_suffix("")

    for suffix in (".png", ".jpg", ".jpeg", ".bmp"):
        if stem_path.name.lower().endswith(suffix):
            stem_path = stem_path.with_suffix("")
            break

    return stem_path.with_name(f"{stem_path.name}.masked.png")


def import_qt():
    try:
        from PySide6.QtCore import QPoint, Qt  # type: ignore[import-not-found]
        from PySide6.QtGui import (  # type: ignore[import-not-found]
            QColor,
            QImage,
            QKeySequence,
            QPainter,
            QPen,
            QPixmap,
            QShortcut,
        )
        from PySide6.QtWidgets import (  # type: ignore[import-not-found]
            QButtonGroup,
            QDialog,
            QDialogButtonBox,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QScrollArea,
            QSpinBox,
            QVBoxLayout,
            QWidget,
        )
    except ImportError as error:
        raise UiDependencyError("PySide6 is not installed") from error

    return {
        "QButtonGroup": QButtonGroup,
        "QColor": QColor,
        "QDialog": QDialog,
        "QDialogButtonBox": QDialogButtonBox,
        "QHBoxLayout": QHBoxLayout,
        "QImage": QImage,
        "QKeySequence": QKeySequence,
        "QLabel": QLabel,
        "QPainter": QPainter,
        "QPen": QPen,
        "QPixmap": QPixmap,
        "QPoint": QPoint,
        "QShortcut": QShortcut,
        "QPushButton": QPushButton,
        "QScrollArea": QScrollArea,
        "QSpinBox": QSpinBox,
        "QVBoxLayout": QVBoxLayout,
        "QWidget": QWidget,
        "Qt": Qt,
    }


def create_mask_editor(image_path: str | Path, output_path: str | Path | None = None, parent=None):
    """Create a dialog that saves a masked PNG copy."""
    qt = import_qt()
    QButtonGroup = qt["QButtonGroup"]
    QColor = qt["QColor"]
    QDialog = qt["QDialog"]
    QDialogButtonBox = qt["QDialogButtonBox"]
    QHBoxLayout = qt["QHBoxLayout"]
    QImage = qt["QImage"]
    QKeySequence = qt["QKeySequence"]
    QLabel = qt["QLabel"]
    QPainter = qt["QPainter"]
    QPen = qt["QPen"]
    QPixmap = qt["QPixmap"]
    QPoint = qt["QPoint"]
    QShortcut = qt["QShortcut"]
    QPushButton = qt["QPushButton"]
    QScrollArea = qt["QScrollArea"]
    QSpinBox = qt["QSpinBox"]
    QVBoxLayout = qt["QVBoxLayout"]
    QWidget = qt["QWidget"]
    Qt = qt["Qt"]

    source_path = Path(image_path)
    save_path = Path(output_path) if output_path is not None else default_masked_image_path(source_path)
    source_image = QImage(str(source_path))
    if source_image.isNull():
        raise ValueError(f"Could not open image: {source_path}")
    source_image = source_image.convertToFormat(QImage.Format_RGBA8888)

    class MaskCanvas(QLabel):
        def __init__(self, image) -> None:
            super().__init__()
            self.image = image.copy()
            self.base_rgb = image.copy()
            self.brush_size = 20
            self.mode = "mask"
            self.undo_stack = []
            self._stroke_started = False
            self.setFixedSize(self.image.size())
            self.setCursor(Qt.CrossCursor)
            self._last_point = None
            self._refresh_pixmap()

        def set_mode(self, mode: str) -> None:
            self.mode = mode

        def set_brush_size(self, size: int) -> None:
            self.brush_size = size

        def mousePressEvent(self, event) -> None:
            point = event.position().toPoint()
            self._begin_stroke()
            self._last_point = point
            self._paint_at(point)

        def mouseMoveEvent(self, event) -> None:
            point = event.position().toPoint()
            self._paint_line(self._last_point or point, point)
            self._last_point = point

        def mouseReleaseEvent(self, event) -> None:
            self._last_point = None
            self._stroke_started = False

        def undo(self) -> None:
            if not self.undo_stack:
                return

            self.image = self.undo_stack.pop()
            self._refresh_pixmap()

        def _begin_stroke(self) -> None:
            if self._stroke_started:
                return

            self.undo_stack.append(self.image.copy())
            if len(self.undo_stack) > 30:
                self.undo_stack.pop(0)
            self._stroke_started = True

        def _paint_at(self, point) -> None:
            self._paint_line(point, point)

        def _paint_line(self, start, end) -> None:
            if self.mode == "restore":
                self._restore_line(start, end)
                self._refresh_pixmap()
                return

            painter = QPainter(self.image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            color = QColor(0, 0, 0, 0)

            pen = QPen(color, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(start, end)
            painter.end()

            self._refresh_pixmap()

        def _restore_line(self, start, end) -> None:
            dx = end.x() - start.x()
            dy = end.y() - start.y()
            steps = max(abs(dx), abs(dy), 1)

            for index in range(steps + 1):
                x = round(start.x() + dx * index / steps)
                y = round(start.y() + dy * index / steps)
                self._restore_rgb_around(QPoint(x, y))

        def _restore_rgb_around(self, point) -> None:
            radius = max(1, self.brush_size // 2)
            left = max(point.x() - radius, 0)
            right = min(point.x() + radius, self.base_rgb.width() - 1)
            top = max(point.y() - radius, 0)
            bottom = min(point.y() + radius, self.base_rgb.height() - 1)
            radius_squared = radius * radius

            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    dx = x - point.x()
                    dy = y - point.y()
                    if dx * dx + dy * dy <= radius_squared:
                        self.image.setPixelColor(x, y, self.base_rgb.pixelColor(x, y))

        def _refresh_pixmap(self) -> None:
            preview = self.image.copy()
            painter = QPainter(preview)
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
            painter.fillRect(preview.rect(), QColor(230, 230, 230))
            painter.end()
            self.setPixmap(QPixmap.fromImage(preview))

    class MaskEditorDialog(QDialog):
        def __init__(self, parent_widget=None) -> None:
            super().__init__(parent_widget)
            self.setWindowTitle("Edit Mask")
            viewport_width = min(source_image.width(), 960)
            viewport_height = min(source_image.height(), 620)
            self.resize(viewport_width + 46, viewport_height + 126)
            self.canvas = MaskCanvas(source_image)
            self.undo_shortcut = QShortcut(QKeySequence.Undo, self)
            self.undo_shortcut.activated.connect(self.canvas.undo)

            layout = QVBoxLayout(self)
            toolbar = QHBoxLayout()
            toolbar.addWidget(QLabel("Mode"))
            self.mask_button = QPushButton("Mask")
            self.restore_button = QPushButton("Restore")
            self.mask_button.setCheckable(True)
            self.restore_button.setCheckable(True)
            self.mask_button.setChecked(True)
            for button in (self.mask_button, self.restore_button):
                button.setMinimumWidth(82)
                button.setStyleSheet(
                    "QPushButton:checked {"
                    "background: #d8eaff;"
                    "border: 1px solid #4c8fd6;"
                    "}"
                )
            self.mode_group = QButtonGroup(self)
            self.mode_group.setExclusive(True)
            self.mode_group.addButton(self.mask_button)
            self.mode_group.addButton(self.restore_button)
            self.mask_button.toggled.connect(lambda checked: checked and self.canvas.set_mode("mask"))
            self.restore_button.toggled.connect(lambda checked: checked and self.canvas.set_mode("restore"))
            toolbar.addWidget(self.mask_button)
            toolbar.addWidget(self.restore_button)

            toolbar.addWidget(QLabel("Brush size"))
            self.brush_size_input = QSpinBox()
            self.brush_size_input.setRange(3, 80)
            self.brush_size_input.setValue(20)
            self.brush_size_input.setSuffix(" px")
            self.brush_size_input.valueChanged.connect(self.canvas.set_brush_size)
            toolbar.addWidget(self.brush_size_input)
            toolbar.addStretch(1)
            toolbar_container = QWidget()
            toolbar_container.setLayout(toolbar)
            layout.addWidget(toolbar_container)

            scroll_area = QScrollArea()
            scroll_area.setWidget(self.canvas)
            scroll_area.setWidgetResizable(False)
            scroll_area.setFixedSize(viewport_width + 4, viewport_height + 4)
            scroll_area.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            layout.addWidget(scroll_area, 1)

            self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            layout.addWidget(self.buttons)

        def masked_image_path(self) -> Path:
            return save_path

        def accept(self) -> None:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.canvas.image.save(str(save_path), "PNG"):
                raise ValueError(f"Could not save image: {save_path}")
            super().accept()

    return MaskEditorDialog(parent)

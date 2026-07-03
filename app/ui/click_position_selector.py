"""Click position selector for template images."""

from __future__ import annotations

from pathlib import Path

from app.models import Offset
from app.ui.main_window import UiDependencyError


def offset_from_image_point(image_width: int, image_height: int, point_x: int, point_y: int) -> Offset:
    """Convert an image-local click point to an offset from the image center."""
    return Offset(
        x=point_x - image_width // 2,
        y=point_y - image_height // 2,
    )


def image_point_from_offset(image_width: int, image_height: int, offset: Offset) -> tuple[int, int]:
    """Convert an offset from the image center to an image-local click point."""
    return (
        image_width // 2 + offset.x,
        image_height // 2 + offset.y,
    )


def clamp_image_point(image_width: int, image_height: int, point_x: int, point_y: int) -> tuple[int, int]:
    """Clamp an image-local point into the image bounds."""
    return (
        min(max(point_x, 0), image_width - 1),
        min(max(point_y, 0), image_height - 1),
    )


def import_qt():
    try:
        from PySide6.QtCore import QPoint, Qt  # type: ignore[import-not-found]
        from PySide6.QtGui import QColor, QPainter, QPen, QPixmap  # type: ignore[import-not-found]
        from PySide6.QtWidgets import (  # type: ignore[import-not-found]
            QDialog,
            QDialogButtonBox,
            QLabel,
            QScrollArea,
            QVBoxLayout,
        )
    except ImportError as error:
        raise UiDependencyError("PySide6 is not installed") from error

    return {
        "QColor": QColor,
        "QDialog": QDialog,
        "QDialogButtonBox": QDialogButtonBox,
        "QLabel": QLabel,
        "QPainter": QPainter,
        "QPen": QPen,
        "QPoint": QPoint,
        "QPixmap": QPixmap,
        "QScrollArea": QScrollArea,
        "QVBoxLayout": QVBoxLayout,
        "Qt": Qt,
    }


def create_click_position_selector(image_path: str | Path, initial_offset: Offset, parent=None):
    """Create a dialog that selects a click point on the template image."""
    qt = import_qt()
    QColor = qt["QColor"]
    QDialog = qt["QDialog"]
    QDialogButtonBox = qt["QDialogButtonBox"]
    QLabel = qt["QLabel"]
    QPainter = qt["QPainter"]
    QPen = qt["QPen"]
    QPoint = qt["QPoint"]
    QPixmap = qt["QPixmap"]
    QScrollArea = qt["QScrollArea"]
    QVBoxLayout = qt["QVBoxLayout"]
    Qt = qt["Qt"]

    pixmap = QPixmap(str(image_path))
    if pixmap.isNull():
        raise ValueError(f"Could not open image: {image_path}")

    class ClickImageLabel(QLabel):
        def __init__(self, source_pixmap, initial_point) -> None:
            super().__init__()
            self.source_pixmap = source_pixmap
            self.selected_point = initial_point
            self.setPixmap(source_pixmap)
            self.setFixedSize(source_pixmap.size())
            self.setCursor(Qt.CrossCursor)

        def mousePressEvent(self, event) -> None:
            position = event.position().toPoint()
            point_x, point_y = clamp_image_point(
                self.source_pixmap.width(),
                self.source_pixmap.height(),
                position.x(),
                position.y(),
            )
            self.selected_point = QPoint(point_x, point_y)
            self.update()

        def paintEvent(self, event) -> None:
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 80, 80), 2)
            painter.setPen(pen)
            x = self.selected_point.x()
            y = self.selected_point.y()
            painter.drawLine(x - 8, y, x + 8, y)
            painter.drawLine(x, y - 8, x, y + 8)
            painter.drawEllipse(self.selected_point, 5, 5)

    class ClickPositionSelectorDialog(QDialog):
        def __init__(self, parent_widget=None) -> None:
            super().__init__(parent_widget)
            self.setWindowTitle("Select Click Position")
            viewport_width = min(pixmap.width(), 860)
            viewport_height = min(pixmap.height(), 600)
            self.resize(viewport_width + 46, viewport_height + 116)

            point_x, point_y = image_point_from_offset(pixmap.width(), pixmap.height(), initial_offset)
            point_x, point_y = clamp_image_point(pixmap.width(), pixmap.height(), point_x, point_y)
            self.image_label = ClickImageLabel(pixmap, QPoint(point_x, point_y))

            layout = QVBoxLayout(self)
            hint_label = QLabel("Click the template image to set the action position.")
            layout.addWidget(hint_label)

            scroll_area = QScrollArea()
            scroll_area.setWidget(self.image_label)
            scroll_area.setWidgetResizable(False)
            scroll_area.setFixedSize(viewport_width + 4, viewport_height + 4)
            scroll_area.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            layout.addWidget(scroll_area, 1)

            self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            layout.addWidget(self.buttons)

        def selected_offset(self) -> Offset:
            point = self.image_label.selected_point
            return offset_from_image_point(pixmap.width(), pixmap.height(), point.x(), point.y())

    return ClickPositionSelectorDialog(parent)

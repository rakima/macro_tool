"""Screen region selector dialog."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.models import Region
from app.screenshot import CapturedScreenshot, PyAutoGuiScreenshotProvider, ScreenshotError
from app.ui.main_window import UiDependencyError


class RegionSelectionError(ValueError):
    """Raised when a selected region is invalid."""


@dataclass(frozen=True)
class Point:
    x: int
    y: int


def region_from_points(start: Point, end: Point, origin: Point | None = None) -> Region:
    """Build a positive Region from two drag points."""
    origin = origin or Point(0, 0)
    x = min(start.x, end.x)
    y = min(start.y, end.y)
    width = abs(end.x - start.x)
    height = abs(end.y - start.y)

    if width <= 0 or height <= 0:
        raise RegionSelectionError("Selected region must have width and height.")

    return Region(x=x + origin.x, y=y + origin.y, width=width, height=height)


def crop_image_by_region(image: np.ndarray, region: Region, origin: Point | None = None) -> np.ndarray:
    """Crop an image using a screen-coordinate region and screenshot origin."""
    origin = origin or Point(0, 0)
    left = region.x - origin.x
    top = region.y - origin.y
    right = left + region.width
    bottom = top + region.height

    image_height, image_width = image.shape[:2]
    if left < 0 or top < 0 or right > image_width or bottom > image_height:
        raise RegionSelectionError("Selected region is outside the screenshot.")

    return image[top:bottom, left:right].copy()


def import_qt_modules():
    try:
        from PySide6.QtCore import QPoint, QRect, Qt  # type: ignore[import-not-found]
        from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap  # type: ignore[import-not-found]
        from PySide6.QtWidgets import (  # type: ignore[import-not-found]
            QDialog,
            QDialogButtonBox,
            QLabel,
            QMessageBox,
            QScrollArea,
            QVBoxLayout,
        )
    except ImportError as error:
        raise UiDependencyError("PySide6 is not installed") from error

    return {
        "QColor": QColor,
        "QDialog": QDialog,
        "QDialogButtonBox": QDialogButtonBox,
        "QImage": QImage,
        "QLabel": QLabel,
        "QMessageBox": QMessageBox,
        "QPainter": QPainter,
        "QPen": QPen,
        "QPixmap": QPixmap,
        "QPoint": QPoint,
        "QRect": QRect,
        "QScrollArea": QScrollArea,
        "Qt": Qt,
        "QVBoxLayout": QVBoxLayout,
    }


def bgr_array_to_qimage(image: np.ndarray):
    """Convert an OpenCV BGR image to a QImage."""
    qt = import_qt_modules()
    QImage = qt["QImage"]

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rgb = np.ascontiguousarray(rgb)
    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    return QImage(rgb.data, width, height, bytes_per_line, QImage.Format_RGB888).copy()


def create_region_selector(screenshot: np.ndarray | CapturedScreenshot | None = None, parent=None):
    """Create a region selector dialog."""
    qt = import_qt_modules()
    QColor = qt["QColor"]
    QDialog = qt["QDialog"]
    QDialogButtonBox = qt["QDialogButtonBox"]
    QLabel = qt["QLabel"]
    QMessageBox = qt["QMessageBox"]
    QPainter = qt["QPainter"]
    QPen = qt["QPen"]
    QPixmap = qt["QPixmap"]
    QPoint = qt["QPoint"]
    QRect = qt["QRect"]
    QScrollArea = qt["QScrollArea"]
    Qt = qt["Qt"]
    QVBoxLayout = qt["QVBoxLayout"]

    class ScreenshotLabel(QLabel):
        def __init__(self, pixmap, origin: Point) -> None:
            super().__init__()
            self.setPixmap(pixmap)
            self.setFixedSize(pixmap.size())
            self.origin = origin
            self.start_point = None
            self.end_point = None

        def selected_region(self) -> Region:
            if self.start_point is None or self.end_point is None:
                raise RegionSelectionError("Select a region by dragging on the screenshot.")

            return region_from_points(
                Point(self.start_point.x(), self.start_point.y()),
                Point(self.end_point.x(), self.end_point.y()),
                origin=self.origin,
            )

        def mousePressEvent(self, event) -> None:
            if event.button() == Qt.LeftButton:
                self.start_point = event.position().toPoint()
                self.end_point = self.start_point
                self.update()

        def mouseMoveEvent(self, event) -> None:
            if self.start_point is not None:
                self.end_point = self._bounded_point(event.position().toPoint())
                self.update()

        def mouseReleaseEvent(self, event) -> None:
            if event.button() == Qt.LeftButton and self.start_point is not None:
                self.end_point = self._bounded_point(event.position().toPoint())
                self.update()

        def paintEvent(self, event) -> None:
            super().paintEvent(event)
            if self.start_point is None or self.end_point is None:
                return

            rect = QRect(self.start_point, self.end_point).normalized()
            painter = QPainter(self)
            painter.setPen(QPen(QColor(0, 122, 204), 2))
            painter.fillRect(rect, QColor(0, 122, 204, 40))
            painter.drawRect(rect)

        def _bounded_point(self, point):
            x = min(max(point.x(), 0), self.width())
            y = min(max(point.y(), 0), self.height())
            return QPoint(x, y)

    class RegionSelectorDialog(QDialog):
        def __init__(self, image: np.ndarray, origin: Point, parent_widget=None) -> None:
            super().__init__(parent_widget)
            self.setWindowTitle("Select Region")
            self.resize(960, 640)
            self.image = image
            self.origin = origin
            self._build_ui(image, origin)

        def _build_ui(self, image: np.ndarray, origin: Point) -> None:
            layout = QVBoxLayout(self)
            layout.addWidget(
                QLabel(
                    "Drag on the screenshot to select a search region. "
                    f"Virtual origin: x={origin.x}, y={origin.y}"
                )
            )

            pixmap = QPixmap.fromImage(bgr_array_to_qimage(image))
            self.screenshot_label = ScreenshotLabel(pixmap, origin)

            scroll_area = QScrollArea()
            scroll_area.setWidget(self.screenshot_label)
            scroll_area.setWidgetResizable(False)
            layout.addWidget(scroll_area, 1)

            self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.buttons.accepted.connect(self.accept)
            self.buttons.rejected.connect(self.reject)
            layout.addWidget(self.buttons)

        def selected_region(self) -> Region:
            return self.screenshot_label.selected_region()

        def selected_image(self) -> np.ndarray:
            return crop_image_by_region(self.image, self.selected_region(), self.origin)

        def accept(self) -> None:
            try:
                self.selected_region()
            except RegionSelectionError as error:
                QMessageBox.warning(self, "Invalid region", str(error))
                return

            super().accept()

    if screenshot is None:
        try:
            screenshot = PyAutoGuiScreenshotProvider().capture_frame()
        except ScreenshotError as error:
            QMessageBox.warning(parent, "Could not capture screenshot", str(error))
            return None

    if isinstance(screenshot, CapturedScreenshot):
        image = screenshot.image
        origin = Point(screenshot.origin_x, screenshot.origin_y)
    else:
        image = screenshot
        origin = Point(0, 0)

    return RegionSelectorDialog(image, origin, parent)

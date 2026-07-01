"""Screenshot capture boundary."""

from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass
from typing import Any, Callable

import cv2
import numpy as np

from app.models import Region


class ScreenshotError(RuntimeError):
    """Raised when a screenshot cannot be captured or converted."""


@dataclass(frozen=True)
class ScreenshotRequest:
    region: Region | None = None

    @property
    def pyautogui_region(self) -> tuple[int, int, int, int] | None:
        if self.region is None:
            return None
        return (
            self.region.x,
            self.region.y,
            self.region.width,
            self.region.height,
        )


@dataclass(frozen=True)
class CapturedScreenshot:
    image: np.ndarray
    origin_x: int = 0
    origin_y: int = 0


class PyAutoGuiScreenshotProvider:
    """Screenshot provider backed by PyAutoGUI."""

    def __init__(self, screenshot_func: Callable[..., Any] | None = None) -> None:
        self.screenshot_func = screenshot_func

    def capture(self, request: ScreenshotRequest | None = None) -> np.ndarray:
        return self.capture_frame(request).image

    def capture_frame(self, request: ScreenshotRequest | None = None) -> CapturedScreenshot:
        request = request or ScreenshotRequest()

        if self.screenshot_func is None:
            return self._capture_with_image_grab(request)

        try:
            if request.pyautogui_region is None:
                image = self.screenshot_func()
            else:
                image = self.screenshot_func(region=request.pyautogui_region)
        except Exception as error:
            raise ScreenshotError("Failed to capture screenshot") from error

        return CapturedScreenshot(image=image_to_bgr_array(image))

    def _capture_with_image_grab(self, request: ScreenshotRequest) -> CapturedScreenshot:
        try:
            from PIL import ImageGrab
        except ImportError as error:
            raise ScreenshotError("Pillow ImageGrab is not installed") from error

        origin_x, origin_y = virtual_screen_origin()
        try:
            if request.region is None:
                image = ImageGrab.grab(all_screens=True)
            else:
                region = request.region
                bbox = (
                    region.x,
                    region.y,
                    region.x + region.width,
                    region.y + region.height,
                )
                image = ImageGrab.grab(bbox=bbox, all_screens=True)
                origin_x = region.x
                origin_y = region.y
        except Exception as error:
            raise ScreenshotError("Failed to capture screenshot") from error

        return CapturedScreenshot(
            image=image_to_bgr_array(image),
            origin_x=origin_x,
            origin_y=origin_y,
        )


def virtual_screen_origin() -> tuple[int, int]:
    """Return the top-left coordinate of the virtual desktop."""
    if sys.platform != "win32":
        return 0, 0

    user32 = ctypes.windll.user32
    return (
        int(user32.GetSystemMetrics(76)),
        int(user32.GetSystemMetrics(77)),
    )


def image_to_bgr_array(image: Any) -> np.ndarray:
    """Convert a PyAutoGUI/Pillow style image to an OpenCV BGR array."""
    array = np.asarray(image)
    if array.size == 0:
        raise ScreenshotError("Captured screenshot is empty")

    if array.ndim == 2:
        return cv2.cvtColor(array, cv2.COLOR_GRAY2BGR)

    if array.ndim != 3:
        raise ScreenshotError("Captured screenshot has an unsupported shape")

    channels = array.shape[2]
    if channels == 3:
        return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
    if channels == 4:
        return cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)

    raise ScreenshotError("Captured screenshot has an unsupported channel count")

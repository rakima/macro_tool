import numpy as np
import pytest

from app.models import Region
from app.screenshot import (
    CapturedScreenshot,
    PyAutoGuiScreenshotProvider,
    ScreenshotError,
    ScreenshotRequest,
    image_to_bgr_array,
    virtual_screen_origin,
)


class FakeScreenshotFunction:
    def __init__(self, image):
        self.image = image
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return self.image


def test_screenshot_request_converts_region_for_pyautogui():
    request = ScreenshotRequest(region=Region(x=10, y=20, width=30, height=40))

    assert request.pyautogui_region == (10, 20, 30, 40)


def test_screenshot_request_allows_negative_region_for_virtual_screen():
    request = ScreenshotRequest(region=Region(x=-100, y=-20, width=30, height=40))

    assert request.pyautogui_region == (-100, -20, 30, 40)


def test_screenshot_request_without_region_uses_full_screen():
    request = ScreenshotRequest()

    assert request.pyautogui_region is None


def test_image_to_bgr_array_converts_rgb_to_bgr():
    rgb = np.array([[[10, 20, 30]]], dtype=np.uint8)

    bgr = image_to_bgr_array(rgb)

    assert bgr.tolist() == [[[30, 20, 10]]]


def test_image_to_bgr_array_converts_rgba_to_bgr():
    rgba = np.array([[[10, 20, 30, 255]]], dtype=np.uint8)

    bgr = image_to_bgr_array(rgba)

    assert bgr.tolist() == [[[30, 20, 10]]]


def test_image_to_bgr_array_converts_grayscale_to_bgr():
    gray = np.array([[42]], dtype=np.uint8)

    bgr = image_to_bgr_array(gray)

    assert bgr.tolist() == [[[42, 42, 42]]]


def test_image_to_bgr_array_rejects_empty_image():
    with pytest.raises(ScreenshotError, match="empty"):
        image_to_bgr_array(np.array([]))


def test_capture_uses_full_screen_when_region_is_missing():
    rgb = np.array([[[10, 20, 30]]], dtype=np.uint8)
    screenshot_func = FakeScreenshotFunction(rgb)
    provider = PyAutoGuiScreenshotProvider(screenshot_func=screenshot_func)

    bgr = provider.capture()

    assert screenshot_func.calls == [{}]
    assert bgr.tolist() == [[[30, 20, 10]]]


def test_capture_frame_returns_image_with_default_origin_for_custom_function():
    rgb = np.array([[[10, 20, 30]]], dtype=np.uint8)
    screenshot_func = FakeScreenshotFunction(rgb)
    provider = PyAutoGuiScreenshotProvider(screenshot_func=screenshot_func)

    frame = provider.capture_frame()

    assert frame == CapturedScreenshot(image=frame.image, origin_x=0, origin_y=0)
    assert frame.image.tolist() == [[[30, 20, 10]]]


def test_capture_passes_region_to_screenshot_function():
    rgb = np.array([[[10, 20, 30]]], dtype=np.uint8)
    screenshot_func = FakeScreenshotFunction(rgb)
    provider = PyAutoGuiScreenshotProvider(screenshot_func=screenshot_func)

    provider.capture(ScreenshotRequest(region=Region(x=1, y=2, width=3, height=4)))

    assert screenshot_func.calls == [{"region": (1, 2, 3, 4)}]


def test_capture_wraps_screenshot_errors():
    def fail(**kwargs):
        raise RuntimeError("boom")

    provider = PyAutoGuiScreenshotProvider(screenshot_func=fail)

    with pytest.raises(ScreenshotError, match="capture"):
        provider.capture()


def test_virtual_screen_origin_returns_tuple():
    origin = virtual_screen_origin()

    assert isinstance(origin[0], int)
    assert isinstance(origin[1], int)

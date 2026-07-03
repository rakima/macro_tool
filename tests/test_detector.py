import cv2
import numpy as np
import pytest

from app.detector import DetectionError, MatchResult, TemplateDetector
from app.models import Action, Region, Rule
from app.screenshot import CapturedScreenshot


def make_rule(image: str, confidence: float = 0.95) -> Rule:
    return Rule(
        enabled=True,
        name="Find marker",
        image=image,
        region=Region(x=10, y=10, width=40, height=40),
        confidence=confidence,
        action=Action(type="click", button="left"),
        cooldown=1.0,
    )


def write_image(path, image: np.ndarray) -> None:
    success, encoded_image = cv2.imencode(".png", image)
    assert success
    encoded_image.tofile(str(path))


def make_marker(color: tuple[int, int, int]) -> np.ndarray:
    marker = np.zeros((10, 10, 3), dtype=np.uint8)
    marker[1:9, 1:9] = color
    marker[3:7, 3:7] = (255, 255, 255)
    return marker


def make_masked_marker() -> np.ndarray:
    marker = np.zeros((10, 10, 4), dtype=np.uint8)
    marker[:, :, :3] = (0, 0, 255)
    marker[:, :, 3] = 255
    marker[3:7, 3:7, :3] = (255, 255, 255)
    marker[3:7, 3:7, 3] = 0
    return marker


def test_detect_returns_match_when_template_is_found(tmp_path):
    screenshot = np.zeros((80, 80, 3), dtype=np.uint8)
    template = make_marker((0, 0, 255))
    screenshot[25:35, 30:40] = template
    write_image(tmp_path / "marker.png", template)

    detector = TemplateDetector(base_dir=tmp_path)
    result = detector.detect(screenshot, make_rule("marker.png"))

    assert result == MatchResult(
        rule_name="Find marker",
        score=1.0,
        x=30,
        y=25,
        width=10,
        height=10,
    )


def test_detect_reads_template_with_japanese_filename(tmp_path):
    screenshot = np.zeros((80, 80, 3), dtype=np.uint8)
    template = make_marker((255, 0, 0))
    screenshot[25:35, 30:40] = template
    write_image(tmp_path / "ミサイル.png", template)

    detector = TemplateDetector(base_dir=tmp_path)
    result = detector.detect(screenshot, make_rule("ミサイル.png"))

    assert result is not None
    assert result.x == 30
    assert result.y == 25


def test_detect_ignores_transparent_template_pixels(tmp_path):
    screenshot = np.zeros((80, 80, 3), dtype=np.uint8)
    template = make_masked_marker()
    target = template[:, :, :3].copy()
    target[3:7, 3:7] = (0, 255, 0)
    screenshot[25:35, 30:40] = target
    write_image(tmp_path / "masked.png", template)

    detector = TemplateDetector(base_dir=tmp_path)
    result = detector.detect(screenshot, make_rule("masked.png", confidence=0.99))

    assert result is not None
    assert result.x == 30
    assert result.y == 25


def test_detect_rejects_fully_transparent_template(tmp_path):
    screenshot = np.zeros((80, 80, 3), dtype=np.uint8)
    template = np.zeros((10, 10, 4), dtype=np.uint8)
    write_image(tmp_path / "transparent.png", template)

    detector = TemplateDetector(base_dir=tmp_path)
    with pytest.raises(DetectionError, match="mask is empty"):
        detector.detect(screenshot, make_rule("transparent.png"))


def test_detect_handles_captured_screenshot_with_virtual_origin(tmp_path):
    screenshot = np.zeros((80, 80, 3), dtype=np.uint8)
    template = make_marker((0, 0, 255))
    screenshot[25:35, 30:40] = template
    write_image(tmp_path / "marker.png", template)
    rule = Rule(
        enabled=True,
        name="Find marker",
        image="marker.png",
        region=Region(x=-1890, y=25, width=40, height=40),
        confidence=0.95,
        action=Action(type="click", button="left"),
        cooldown=1.0,
    )

    detector = TemplateDetector(base_dir=tmp_path)
    result = detector.detect(
        CapturedScreenshot(image=screenshot, origin_x=-1920, origin_y=0),
        rule,
    )

    assert result is not None
    assert result.x == -1890
    assert result.y == 25


def test_match_result_exposes_center():
    result = MatchResult(rule_name="Rule", score=0.9, x=10, y=20, width=9, height=11)

    assert result.center_x == 14
    assert result.center_y == 25


def test_detect_returns_none_when_score_is_below_confidence(tmp_path):
    screenshot = np.zeros((80, 80, 3), dtype=np.uint8)
    screenshot[25:35, 30:40] = make_marker((0, 255, 0))
    template = make_marker((0, 0, 255))
    write_image(tmp_path / "marker.png", template)

    detector = TemplateDetector(base_dir=tmp_path)
    result = detector.detect(screenshot, make_rule("marker.png", confidence=0.99))

    assert result is None


def test_detect_returns_none_when_template_is_larger_than_region(tmp_path):
    screenshot = np.zeros((80, 80, 3), dtype=np.uint8)
    template = np.zeros((50, 50, 3), dtype=np.uint8)
    write_image(tmp_path / "large.png", template)

    detector = TemplateDetector(base_dir=tmp_path)
    result = detector.detect(screenshot, make_rule("large.png"))

    assert result is None


def test_detect_rejects_missing_template(tmp_path):
    screenshot = np.zeros((80, 80, 3), dtype=np.uint8)

    detector = TemplateDetector(base_dir=tmp_path)
    with pytest.raises(DetectionError, match="template image"):
        detector.detect(screenshot, make_rule("missing.png"))


def test_detect_rejects_region_outside_screenshot(tmp_path):
    screenshot = np.zeros((20, 20, 3), dtype=np.uint8)
    template = np.zeros((5, 5, 3), dtype=np.uint8)
    write_image(tmp_path / "marker.png", template)

    detector = TemplateDetector(base_dir=tmp_path)
    with pytest.raises(DetectionError, match="outside"):
        detector.detect(screenshot, make_rule("marker.png"))


def test_detect_rejects_empty_screenshot(tmp_path):
    template = np.zeros((5, 5, 3), dtype=np.uint8)
    write_image(tmp_path / "marker.png", template)

    detector = TemplateDetector(base_dir=tmp_path)
    with pytest.raises(DetectionError, match="screenshot"):
        detector.detect(np.array([]), make_rule("marker.png"))

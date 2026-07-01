"""Image detection boundary for OpenCV-based template matching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.models import Rule
from app.screenshot import CapturedScreenshot


class DetectionError(RuntimeError):
    """Raised when image detection cannot be performed."""


@dataclass(frozen=True)
class MatchResult:
    rule_name: str
    score: float
    x: int
    y: int
    width: int
    height: int

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2


class TemplateDetector:
    """OpenCV template matching detector."""

    def __init__(self, base_dir: str | Path = ".") -> None:
        self.base_dir = Path(base_dir)

    def detect(self, screenshot: np.ndarray, rule: Rule) -> MatchResult | None:
        """Return the best match when it meets the rule confidence."""
        origin_x = 0
        origin_y = 0
        if isinstance(screenshot, CapturedScreenshot):
            origin_x = screenshot.origin_x
            origin_y = screenshot.origin_y
            screenshot = screenshot.image

        if screenshot is None or screenshot.size == 0:
            raise DetectionError("screenshot must not be empty")

        template = self._load_template(rule.image)
        region_image = self._crop_region(screenshot, rule, origin_x=origin_x, origin_y=origin_y)

        if template.shape[0] > region_image.shape[0] or template.shape[1] > region_image.shape[1]:
            return None

        result = cv2.matchTemplate(region_image, template, cv2.TM_CCOEFF_NORMED)
        _, max_score, _, max_location = cv2.minMaxLoc(result)

        if max_score < rule.confidence:
            return None

        match_x = rule.region.x + max_location[0]
        match_y = rule.region.y + max_location[1]
        return MatchResult(
            rule_name=rule.name,
            score=float(max_score),
            x=match_x,
            y=match_y,
            width=int(template.shape[1]),
            height=int(template.shape[0]),
        )

    def _load_template(self, image_path: str) -> np.ndarray:
        path = Path(image_path)
        if not path.is_absolute():
            path = self.base_dir / path

        try:
            image_data = np.fromfile(str(path), dtype=np.uint8)
        except OSError as error:
            raise DetectionError(f"Could not read template image: {path}") from error

        template = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        if template is None:
            raise DetectionError(f"Could not read template image: {path}")
        return template

    def _crop_region(
        self,
        screenshot: np.ndarray,
        rule: Rule,
        origin_x: int = 0,
        origin_y: int = 0,
    ) -> np.ndarray:
        region = rule.region
        screenshot_height, screenshot_width = screenshot.shape[:2]
        left = region.x - origin_x
        top = region.y - origin_y
        right = left + region.width
        bottom = top + region.height

        if left < 0 or top < 0 or left >= screenshot_width or top >= screenshot_height:
            raise DetectionError("rule region starts outside the screenshot")
        if right > screenshot_width or bottom > screenshot_height:
            raise DetectionError("rule region extends outside the screenshot")

        return screenshot[top:bottom, left:right]

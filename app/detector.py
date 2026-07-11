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


@dataclass(frozen=True)
class TemplateImage:
    image: np.ndarray
    mask: np.ndarray | None = None


class TemplateDetector:
    """OpenCV template matching detector."""

    def __init__(self, base_dir: str | Path = ".") -> None:
        self.base_dir = Path(base_dir)

    def detect(self, screenshot: np.ndarray, rule: Rule) -> MatchResult | None:
        """Return the best match when it meets the rule confidence."""
        match = self.find_best_match(screenshot, rule)
        if match is None or match.score < rule.confidence:
            return None

        return match

    def find_best_match(self, screenshot: np.ndarray, rule: Rule) -> MatchResult | None:
        """Return the best match even when it is below the rule confidence."""
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

        if template.image.shape[0] > region_image.shape[0] or template.image.shape[1] > region_image.shape[1]:
            return None

        result = self._match_template(region_image, template)
        _, max_score, _, max_location = cv2.minMaxLoc(result)

        match_x = rule.region.x + max_location[0]
        match_y = rule.region.y + max_location[1]
        return MatchResult(
            rule_name=rule.name,
            score=float(max_score),
            x=match_x,
            y=match_y,
            width=int(template.image.shape[1]),
            height=int(template.image.shape[0]),
        )

    def _load_template(self, image_path: str) -> TemplateImage:
        path = Path(image_path)
        if not path.is_absolute():
            path = self.base_dir / path

        try:
            image_data = np.fromfile(str(path), dtype=np.uint8)
        except OSError as error:
            raise DetectionError(f"Could not read template image: {path}") from error

        template = cv2.imdecode(image_data, cv2.IMREAD_UNCHANGED)
        if template is None:
            raise DetectionError(f"Could not read template image: {path}")

        if len(template.shape) == 2:
            return TemplateImage(image=cv2.cvtColor(template, cv2.COLOR_GRAY2BGR))

        if template.shape[2] == 4:
            mask = template[:, :, 3]
            if not np.any(mask):
                raise DetectionError(f"Template image mask is empty: {path}")
            return TemplateImage(image=template[:, :, :3], mask=mask)

        return TemplateImage(image=template)

    def _match_template(self, region_image: np.ndarray, template: TemplateImage) -> np.ndarray:
        if template.mask is None:
            return cv2.matchTemplate(region_image, template.image, cv2.TM_CCOEFF_NORMED)

        result = cv2.matchTemplate(region_image, template.image, cv2.TM_CCORR_NORMED, mask=template.mask)
        return np.nan_to_num(result, nan=-1.0, posinf=-1.0, neginf=-1.0)

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

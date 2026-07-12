"""Macro runner and cooldown handling."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from app.actions import (
    ActionExecutionError,
    ClickTarget,
    MouseController,
    execute_action,
)
from app.detector import DetectionError, MatchResult
from app.models import Rule
from app.screenshot import ScreenshotError


class Detector(Protocol):
    def detect(self, screenshot: Any, rule: Rule) -> MatchResult | None:
        """Detect a rule target in a screenshot."""


class ScreenshotProvider(Protocol):
    def capture(self) -> Any:
        """Capture a screenshot."""


@dataclass(frozen=True)
class RuleRunResult:
    rule_name: str
    matched: bool = False
    triggered: bool = False
    skipped_cooldown: bool = False
    score: float | None = None
    match: MatchResult | None = None
    click_target: ClickTarget | None = None
    error: str | None = None


@dataclass(frozen=True)
class RunnerCycleResult:
    results: list[RuleRunResult]

    @property
    def triggered_count(self) -> int:
        return sum(1 for result in self.results if result.triggered)

    @property
    def error_count(self) -> int:
        return sum(1 for result in self.results if result.error is not None)


class MacroRunner:
    """Runs one macro detection/action cycle at a time."""

    def __init__(
        self,
        rules: list[Rule],
        detector: Detector,
        mouse: MouseController | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.rules = rules
        self.detector = detector
        self.mouse = mouse
        self.clock = clock
        self.last_triggered_at: dict[str, float] = {}

    def capture_and_run_once(self, screenshot_provider: ScreenshotProvider) -> RunnerCycleResult:
        """Capture a screenshot and evaluate enabled rules once."""
        try:
            screenshot = self._capture_screenshot(screenshot_provider)
        except ScreenshotError as error:
            return RunnerCycleResult(
                results=[
                    RuleRunResult(
                        rule_name="__screenshot__",
                        error=str(error),
                    )
                ]
            )

        return self.run_once(screenshot)

    def capture_and_test_once(self, screenshot_provider: ScreenshotProvider) -> RunnerCycleResult:
        """Capture a screenshot and test detection without executing actions."""
        try:
            screenshot = self._capture_screenshot(screenshot_provider)
        except ScreenshotError as error:
            return RunnerCycleResult(
                results=[
                    RuleRunResult(
                        rule_name="__screenshot__",
                        error=str(error),
                    )
                ]
            )

        return self.test_once(screenshot)

    def test_once(self, screenshot: Any) -> RunnerCycleResult:
        """Evaluate enabled rules once without executing actions or cooldown."""
        results: list[RuleRunResult] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            try:
                match = self._find_best_match_for_test(screenshot, rule)
            except DetectionError as error:
                results.append(
                    RuleRunResult(
                        rule_name=rule.name,
                        error=str(error),
                    )
                )
                continue

            if match is None:
                results.append(RuleRunResult(rule_name=rule.name))
            elif match.score < rule.confidence:
                results.append(
                    RuleRunResult(
                        rule_name=rule.name,
                        score=match.score,
                    )
                )
            else:
                results.append(
                    RuleRunResult(
                        rule_name=rule.name,
                        matched=True,
                        score=match.score,
                        match=match,
                    )
                )

        return RunnerCycleResult(results=results)

    def run_once(self, screenshot: Any) -> RunnerCycleResult:
        """Evaluate enabled rules once against a screenshot."""
        now = self.clock()
        results: list[RuleRunResult] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            if self.is_cooling_down(rule, now):
                results.append(
                    RuleRunResult(
                        rule_name=rule.name,
                        skipped_cooldown=True,
                    )
                )
                continue

            try:
                match = self.detector.detect(screenshot, rule)
                if match is None:
                    results.append(RuleRunResult(rule_name=rule.name))
                    continue

                click_target = execute_action(rule.action, match, mouse=self.mouse)
                self.last_triggered_at[rule.name] = now
                results.append(
                    RuleRunResult(
                        rule_name=rule.name,
                        matched=True,
                        triggered=True,
                        score=match.score,
                        match=match,
                        click_target=click_target,
                    )
                )
            except (DetectionError, ActionExecutionError) as error:
                results.append(
                    RuleRunResult(
                        rule_name=rule.name,
                        error=str(error),
                    )
                )

        return RunnerCycleResult(results=results)

    def is_cooling_down(self, rule: Rule, now: float | None = None) -> bool:
        current_time = self.clock() if now is None else now
        last_triggered = self.last_triggered_at.get(rule.name)
        if last_triggered is None:
            return False

        return current_time - last_triggered < rule.cooldown

    def _capture_screenshot(self, screenshot_provider: ScreenshotProvider) -> Any:
        capture_frame = getattr(screenshot_provider, "capture_frame", None)
        if callable(capture_frame):
            return capture_frame()

        return screenshot_provider.capture()

    def _find_best_match_for_test(self, screenshot: Any, rule: Rule) -> MatchResult | None:
        find_best_match = getattr(self.detector, "find_best_match", None)
        if callable(find_best_match):
            return find_best_match(screenshot, rule)

        return self.detector.detect(screenshot, rule)

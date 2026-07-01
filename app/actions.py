"""Action execution boundary for PyAutoGUI operations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from app.detector import MatchResult
from app.models import Action


class ActionExecutionError(RuntimeError):
    """Raised when an action cannot be executed."""


class MouseController(Protocol):
    def click(self, x: int, y: int, button: str) -> None:
        """Click at the given screen position."""


@dataclass(frozen=True)
class ClickTarget:
    x: int
    y: int
    button: str


class PyAutoGuiMouseController:
    """Mouse controller backed by PyAutoGUI."""

    def __init__(
        self,
        pyautogui_module: Any | None = None,
        sleep_func: Callable[[float], None] = time.sleep,
        move_duration: float = 0.02,
        press_duration: float = 0.05,
    ) -> None:
        self.pyautogui_module = pyautogui_module
        self.sleep_func = sleep_func
        self.move_duration = move_duration
        self.press_duration = press_duration

    def click(self, x: int, y: int, button: str) -> None:
        pyautogui = self.pyautogui_module or self._load_pyautogui()

        try:
            original_position = pyautogui.position()
            pyautogui.moveTo(x, y, duration=self.move_duration)
            pyautogui.mouseDown(button=button)
            self.sleep_func(self.press_duration)
            pyautogui.mouseUp(button=button)
            pyautogui.moveTo(original_position.x, original_position.y, duration=self.move_duration)
        except Exception as error:
            raise ActionExecutionError("Failed to execute mouse click") from error

    def _load_pyautogui(self) -> Any:
        try:
            import pyautogui
        except ImportError as error:
            raise ActionExecutionError("PyAutoGUI is not installed") from error

        return pyautogui


def build_click_target(action: Action, match: MatchResult) -> ClickTarget:
    """Build the click position from a match center and action offset."""
    if action.type != "click":
        raise ActionExecutionError("Only click actions are supported")

    return ClickTarget(
        x=match.center_x + action.offset.x,
        y=match.center_y + action.offset.y,
        button=action.button,
    )


def execute_action(
    action: Action,
    match: MatchResult,
    mouse: MouseController | None = None,
) -> ClickTarget:
    """Execute an action and return the concrete click target."""
    target = build_click_target(action, match)
    controller = mouse if mouse is not None else PyAutoGuiMouseController()
    controller.click(x=target.x, y=target.y, button=target.button)
    return target

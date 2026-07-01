import pytest
from types import SimpleNamespace

from app.actions import (
    ActionExecutionError,
    ClickTarget,
    PyAutoGuiMouseController,
    build_click_target,
    execute_action,
)
from app.detector import MatchResult
from app.models import Action, Offset


class FakeMouse:
    def __init__(self) -> None:
        self.clicks = []

    def click(self, x: int, y: int, button: str) -> None:
        self.clicks.append((x, y, button))


class FailingMouse:
    def click(self, x: int, y: int, button: str) -> None:
        raise ActionExecutionError("failed")


class FakePyAutoGui:
    def __init__(self) -> None:
        self.calls = []

    def position(self):
        self.calls.append(("position",))
        return SimpleNamespace(x=400, y=300)

    def moveTo(self, x: int, y: int, duration: float = 0.0) -> None:
        self.calls.append(("moveTo", x, y, duration))

    def mouseDown(self, button: str) -> None:
        self.calls.append(("mouseDown", button))

    def mouseUp(self, button: str) -> None:
        self.calls.append(("mouseUp", button))


def make_match() -> MatchResult:
    return MatchResult(
        rule_name="Find marker",
        score=0.98,
        x=100,
        y=200,
        width=20,
        height=10,
    )


def test_build_click_target_uses_match_center():
    action = Action(type="click", button="left")

    assert build_click_target(action, make_match()) == ClickTarget(
        x=110,
        y=205,
        button="left",
    )


def test_build_click_target_applies_offset():
    action = Action(
        type="click",
        button="right",
        offset=Offset(x=5, y=-3),
    )

    assert build_click_target(action, make_match()) == ClickTarget(
        x=115,
        y=202,
        button="right",
    )


def test_execute_action_clicks_mouse_controller():
    mouse = FakeMouse()
    action = Action(type="click", button="middle")

    target = execute_action(action, make_match(), mouse=mouse)

    assert target == ClickTarget(x=110, y=205, button="middle")
    assert mouse.clicks == [(110, 205, "middle")]


def test_execute_action_propagates_action_errors():
    action = Action(type="click", button="left")

    with pytest.raises(ActionExecutionError, match="failed"):
        execute_action(action, make_match(), mouse=FailingMouse())


def test_pyautogui_mouse_controller_restores_original_position():
    pyautogui = FakePyAutoGui()
    sleeps = []
    controller = PyAutoGuiMouseController(
        pyautogui_module=pyautogui,
        sleep_func=sleeps.append,
        move_duration=0.02,
        press_duration=0.05,
    )

    controller.click(x=110, y=205, button="left")

    assert pyautogui.calls == [
        ("position",),
        ("moveTo", 110, 205, 0.02),
        ("mouseDown", "left"),
        ("mouseUp", "left"),
        ("moveTo", 400, 300, 0.02),
    ]
    assert sleeps == [0.05]

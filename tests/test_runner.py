from app.actions import ActionExecutionError
from app.detector import DetectionError, MatchResult
from app.models import Action, Region, Rule
from app.runner import MacroRunner
from app.screenshot import ScreenshotError


class FakeClock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class FakeDetector:
    def __init__(self, matches: dict[str, MatchResult | None]) -> None:
        self.matches = matches
        self.calls = []

    def detect(self, screenshot, rule: Rule) -> MatchResult | None:
        self.calls.append(rule.name)
        return self.matches.get(rule.name)


class FakeBestMatchDetector:
    def __init__(self, matches: dict[str, MatchResult | None]) -> None:
        self.matches = matches
        self.calls = []

    def find_best_match(self, screenshot, rule: Rule) -> MatchResult | None:
        self.calls.append(rule.name)
        return self.matches.get(rule.name)

    def detect(self, screenshot, rule: Rule) -> MatchResult | None:
        raise AssertionError("test_once should use find_best_match when available")


class FailingDetector:
    def detect(self, screenshot, rule: Rule) -> MatchResult | None:
        raise DetectionError("detection failed")


class FakeMouse:
    def __init__(self) -> None:
        self.clicks = []

    def click(self, x: int, y: int, button: str) -> None:
        self.clicks.append((x, y, button))


class FailingMouse:
    def click(self, x: int, y: int, button: str) -> None:
        raise ActionExecutionError("click failed")


class FakeScreenshotProvider:
    def __init__(self, screenshot) -> None:
        self.screenshot = screenshot

    def capture(self):
        return self.screenshot


class FailingScreenshotProvider:
    def capture(self):
        raise ScreenshotError("screenshot failed")


def make_rule(name: str = "Rule", enabled: bool = True, cooldown: float = 1.5) -> Rule:
    return Rule(
        enabled=enabled,
        name=name,
        image="images/button.png",
        region=Region(x=0, y=0, width=50, height=50),
        confidence=0.85,
        action=Action(type="click", button="left"),
        cooldown=cooldown,
    )


def make_match(rule_name: str = "Rule") -> MatchResult:
    return MatchResult(
        rule_name=rule_name,
        score=0.95,
        x=10,
        y=20,
        width=10,
        height=10,
    )


def test_run_once_triggers_click_when_rule_matches():
    rule = make_rule()
    clock = FakeClock()
    mouse = FakeMouse()
    runner = MacroRunner(
        rules=[rule],
        detector=FakeDetector({"Rule": make_match()}),
        mouse=mouse,
        clock=clock,
    )

    result = runner.run_once(screenshot=object())

    assert result.triggered_count == 1
    assert result.results[0].matched is True
    assert result.results[0].click_target is not None
    assert mouse.clicks == [(15, 25, "left")]
    assert runner.last_triggered_at == {"Rule": 100.0}


def test_run_once_skips_disabled_rules():
    rule = make_rule(enabled=False)
    detector = FakeDetector({"Rule": make_match()})
    runner = MacroRunner(rules=[rule], detector=detector)

    result = runner.run_once(screenshot=object())

    assert result.results == []
    assert detector.calls == []


def test_run_once_records_no_match_without_clicking():
    rule = make_rule()
    mouse = FakeMouse()
    runner = MacroRunner(
        rules=[rule],
        detector=FakeDetector({"Rule": None}),
        mouse=mouse,
    )

    result = runner.run_once(screenshot=object())

    assert result.triggered_count == 0
    assert result.results[0].matched is False
    assert mouse.clicks == []


def test_run_once_skips_rule_during_cooldown():
    rule = make_rule(cooldown=2.0)
    clock = FakeClock(now=101.0)
    detector = FakeDetector({"Rule": make_match()})
    runner = MacroRunner(rules=[rule], detector=detector, clock=clock)
    runner.last_triggered_at["Rule"] = 100.0

    result = runner.run_once(screenshot=object())

    assert result.results[0].skipped_cooldown is True
    assert detector.calls == []


def test_run_once_allows_rule_after_cooldown():
    rule = make_rule(cooldown=2.0)
    clock = FakeClock(now=102.0)
    mouse = FakeMouse()
    runner = MacroRunner(
        rules=[rule],
        detector=FakeDetector({"Rule": make_match()}),
        mouse=mouse,
        clock=clock,
    )
    runner.last_triggered_at["Rule"] = 100.0

    result = runner.run_once(screenshot=object())

    assert result.triggered_count == 1
    assert mouse.clicks == [(15, 25, "left")]


def test_run_once_records_detection_errors_and_continues():
    rules = [make_rule("Broken"), make_rule("Healthy")]
    runner = MacroRunner(
        rules=rules,
        detector=FailingDetector(),
        mouse=FakeMouse(),
    )

    result = runner.run_once(screenshot=object())

    assert result.error_count == 2
    assert result.results[0].error == "detection failed"


def test_run_once_records_action_error():
    rule = make_rule()
    runner = MacroRunner(
        rules=[rule],
        detector=FakeDetector({"Rule": make_match()}),
        mouse=FailingMouse(),
    )

    result = runner.run_once(screenshot=object())

    assert result.error_count == 1
    assert result.results[0].error == "click failed"


def test_capture_and_run_once_uses_screenshot_provider():
    rule = make_rule()
    screenshot = object()
    detector = FakeDetector({"Rule": make_match()})
    runner = MacroRunner(
        rules=[rule],
        detector=detector,
        mouse=FakeMouse(),
    )

    result = runner.capture_and_run_once(FakeScreenshotProvider(screenshot))

    assert result.triggered_count == 1
    assert detector.calls == ["Rule"]


def test_capture_and_run_once_records_screenshot_error():
    rule = make_rule()
    runner = MacroRunner(
        rules=[rule],
        detector=FakeDetector({"Rule": make_match()}),
        mouse=FakeMouse(),
    )

    result = runner.capture_and_run_once(FailingScreenshotProvider())

    assert result.error_count == 1
    assert result.results[0].rule_name == "__screenshot__"
    assert result.results[0].error == "screenshot failed"


def test_test_once_detects_without_clicking_or_cooldown():
    rule = make_rule()
    mouse = FakeMouse()
    runner = MacroRunner(
        rules=[rule],
        detector=FakeDetector({"Rule": make_match()}),
        mouse=mouse,
    )

    result = runner.test_once(screenshot=object())

    assert result.results[0].matched is True
    assert result.results[0].triggered is False
    assert result.results[0].click_target is None
    assert mouse.clicks == []
    assert runner.last_triggered_at == {}


def test_test_once_records_below_confidence_score_without_clicking():
    rule = make_rule()
    match = MatchResult(
        rule_name="Rule",
        score=0.84,
        x=10,
        y=20,
        width=10,
        height=10,
    )
    mouse = FakeMouse()
    detector = FakeBestMatchDetector({"Rule": match})
    runner = MacroRunner(
        rules=[rule],
        detector=detector,
        mouse=mouse,
    )

    result = runner.test_once(screenshot=object())

    assert result.results[0].matched is False
    assert result.results[0].score == 0.84
    assert result.results[0].match is None
    assert mouse.clicks == []
    assert detector.calls == ["Rule"]


def test_test_once_skips_disabled_rules():
    rule = make_rule(enabled=False)
    detector = FakeDetector({"Rule": make_match()})
    runner = MacroRunner(rules=[rule], detector=detector)

    result = runner.test_once(screenshot=object())

    assert result.results == []
    assert detector.calls == []


def test_capture_and_test_once_records_screenshot_error():
    rule = make_rule()
    runner = MacroRunner(
        rules=[rule],
        detector=FakeDetector({"Rule": make_match()}),
        mouse=FakeMouse(),
    )

    result = runner.capture_and_test_once(FailingScreenshotProvider())

    assert result.error_count == 1
    assert result.results[0].rule_name == "__screenshot__"
    assert result.results[0].error == "screenshot failed"

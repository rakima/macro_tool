import pytest

from app.models import Action, Offset, Region, Rule, RuleSet, RuleValidationError


def make_rule() -> Rule:
    return Rule(
        enabled=True,
        name="Click start button",
        image="images/start_button.png",
        region=Region(x=100, y=200, width=300, height=120),
        confidence=0.85,
        action=Action(type="click", button="left"),
        cooldown=1.5,
    )


def test_region_allows_negative_position_for_multi_monitor():
    assert Region(x=-100, y=-50, width=10, height=10).to_dict() == {
        "x": -100,
        "y": -50,
        "width": 10,
        "height": 10,
    }


def test_region_rejects_empty_size():
    with pytest.raises(RuleValidationError, match="region.width"):
        Region(x=0, y=0, width=0, height=10)


def test_action_defaults_offset():
    action = Action.from_dict({"type": "click", "button": "left"})

    assert action.offset == Offset(x=0, y=0)
    assert action.to_dict()["offset"] == {"x": 0, "y": 0}


def test_action_rejects_unsupported_type():
    with pytest.raises(RuleValidationError, match="action.type"):
        Action(type="keyboard", button="left")


def test_rule_rejects_blank_name():
    with pytest.raises(RuleValidationError, match="name"):
        Rule(
            enabled=True,
            name=" ",
            image="images/start_button.png",
            region=Region(x=0, y=0, width=10, height=10),
            confidence=0.85,
            action=Action(type="click", button="left"),
            cooldown=1.0,
        )


def test_rule_rejects_invalid_confidence():
    with pytest.raises(RuleValidationError, match="confidence"):
        Rule(
            enabled=True,
            name="Bad confidence",
            image="images/start_button.png",
            region=Region(x=0, y=0, width=10, height=10),
            confidence=1.1,
            action=Action(type="click", button="left"),
            cooldown=1.0,
        )


def test_rule_round_trips_dict():
    rule = make_rule()

    assert Rule.from_dict(rule.to_dict()) == rule


def test_rule_set_round_trips_dict():
    rule_set = RuleSet(rules=[make_rule()])

    assert RuleSet.from_dict(rule_set.to_dict()) == rule_set


def test_rule_set_rejects_unsupported_version():
    with pytest.raises(RuleValidationError, match="version"):
        RuleSet.from_dict({"version": 2, "rules": []})

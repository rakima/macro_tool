import pytest

from app.models import Action, Region, Rule, RuleSet
from app.rule_operations import (
    RuleOperationError,
    add_rule,
    make_image_path_relative,
    make_rule_set_image_paths_relative,
    remove_rule,
    replace_rule,
)


def make_rule(name: str) -> Rule:
    return Rule(
        enabled=True,
        name=name,
        image=f"images/{name}.png",
        region=Region(x=0, y=0, width=10, height=10),
        confidence=0.85,
        action=Action(type="click", button="left"),
        cooldown=1.0,
    )


def test_add_rule_returns_new_rule_set():
    original = RuleSet(rules=[make_rule("a")])

    updated = add_rule(original, make_rule("b"))

    assert [rule.name for rule in original.rules] == ["a"]
    assert [rule.name for rule in updated.rules] == ["a", "b"]


def test_replace_rule_returns_new_rule_set():
    original = RuleSet(rules=[make_rule("a"), make_rule("b")])

    updated = replace_rule(original, 1, make_rule("c"))

    assert [rule.name for rule in original.rules] == ["a", "b"]
    assert [rule.name for rule in updated.rules] == ["a", "c"]


def test_replace_rule_rejects_out_of_range_index():
    with pytest.raises(RuleOperationError, match="out of range"):
        replace_rule(RuleSet(rules=[]), 0, make_rule("a"))


def test_remove_rule_returns_new_rule_set():
    original = RuleSet(rules=[make_rule("a"), make_rule("b"), make_rule("c")])

    updated = remove_rule(original, 1)

    assert [rule.name for rule in original.rules] == ["a", "b", "c"]
    assert [rule.name for rule in updated.rules] == ["a", "c"]


def test_remove_rule_rejects_out_of_range_index():
    with pytest.raises(RuleOperationError, match="out of range"):
        remove_rule(RuleSet(rules=[]), 0)


def test_make_image_path_relative_converts_path_inside_base_dir(tmp_path):
    base_dir = tmp_path / "project"
    image_path = base_dir / "image" / "button.png"
    rule = make_rule("button")
    rule = Rule(
        enabled=rule.enabled,
        name=rule.name,
        image=str(image_path),
        region=rule.region,
        confidence=rule.confidence,
        action=rule.action,
        cooldown=rule.cooldown,
    )

    updated = make_image_path_relative(rule, base_dir)

    assert updated.image == "image/button.png"


def test_make_image_path_relative_leaves_path_outside_base_dir(tmp_path):
    base_dir = tmp_path / "project"
    image_path = tmp_path / "other" / "button.png"
    rule = make_rule("button")
    rule = Rule(
        enabled=rule.enabled,
        name=rule.name,
        image=str(image_path),
        region=rule.region,
        confidence=rule.confidence,
        action=rule.action,
        cooldown=rule.cooldown,
    )

    updated = make_image_path_relative(rule, base_dir)

    assert updated.image == str(image_path)


def test_make_rule_set_image_paths_relative(tmp_path):
    base_dir = tmp_path / "project"
    image_path = base_dir / "image" / "button.png"
    rule = make_rule("button")
    rule = Rule(
        enabled=rule.enabled,
        name=rule.name,
        image=str(image_path),
        region=rule.region,
        confidence=rule.confidence,
        action=rule.action,
        cooldown=rule.cooldown,
    )

    updated = make_rule_set_image_paths_relative(RuleSet(rules=[rule]), base_dir)

    assert updated.rules[0].image == "image/button.png"

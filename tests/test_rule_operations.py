import pytest

from app.models import Action, Region, Rule, RuleSet
from app.rule_operations import (
    RuleOperationError,
    add_rule,
    duplicate_rule,
    make_image_path_relative,
    make_rule_set_image_paths_relative,
    move_rule,
    reorder_rules,
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


def test_duplicate_rule_inserts_copy_after_selected_rule():
    original = RuleSet(rules=[make_rule("a"), make_rule("b")])

    updated = duplicate_rule(original, 0)

    assert [rule.name for rule in original.rules] == ["a", "b"]
    assert [rule.name for rule in updated.rules] == ["a", "a copy", "b"]
    assert updated.rules[1].image == "images/a.png"


def test_duplicate_rule_uses_unique_copy_name():
    original = RuleSet(
        rules=[
            make_rule("a"),
            make_rule("a copy"),
            make_rule("a copy 2"),
        ]
    )

    updated = duplicate_rule(original, 0)

    assert [rule.name for rule in updated.rules] == ["a", "a copy 3", "a copy", "a copy 2"]


def test_duplicate_rule_rejects_out_of_range_index():
    with pytest.raises(RuleOperationError, match="out of range"):
        duplicate_rule(RuleSet(rules=[]), 0)


def test_move_rule_reorders_rules():
    original = RuleSet(rules=[make_rule("a"), make_rule("b"), make_rule("c")])

    updated = move_rule(original, 2, 0)

    assert [rule.name for rule in original.rules] == ["a", "b", "c"]
    assert [rule.name for rule in updated.rules] == ["c", "a", "b"]


def test_move_rule_rejects_out_of_range_index():
    with pytest.raises(RuleOperationError, match="out of range"):
        move_rule(RuleSet(rules=[make_rule("a")]), 1, 0)


def test_move_rule_rejects_out_of_range_target_index():
    with pytest.raises(RuleOperationError, match="target rule index is out of range"):
        move_rule(RuleSet(rules=[make_rule("a")]), 0, 1)


def test_reorder_rules_reorders_by_original_indices():
    original = RuleSet(rules=[make_rule("a"), make_rule("b"), make_rule("c")])

    updated = reorder_rules(original, [2, 0, 1])

    assert [rule.name for rule in original.rules] == ["a", "b", "c"]
    assert [rule.name for rule in updated.rules] == ["c", "a", "b"]


def test_reorder_rules_rejects_length_mismatch():
    with pytest.raises(RuleOperationError, match="length"):
        reorder_rules(RuleSet(rules=[make_rule("a"), make_rule("b")]), [1])


def test_reorder_rules_rejects_duplicate_indices():
    with pytest.raises(RuleOperationError, match="exactly once"):
        reorder_rules(RuleSet(rules=[make_rule("a"), make_rule("b")]), [0, 0])


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

"""RuleSet update helpers."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.models import Rule, RuleSet


class RuleOperationError(ValueError):
    """Raised when a rule update cannot be applied."""


def add_rule(rule_set: RuleSet, rule: Rule) -> RuleSet:
    """Return a new RuleSet with a rule appended."""
    return RuleSet(version=rule_set.version, rules=[*rule_set.rules, rule])


def replace_rule(rule_set: RuleSet, index: int, rule: Rule) -> RuleSet:
    """Return a new RuleSet with the rule at index replaced."""
    if index < 0 or index >= len(rule_set.rules):
        raise RuleOperationError("rule index is out of range")

    rules = list(rule_set.rules)
    rules[index] = rule
    return RuleSet(version=rule_set.version, rules=rules)


def remove_rule(rule_set: RuleSet, index: int) -> RuleSet:
    """Return a new RuleSet with the rule at index removed."""
    if index < 0 or index >= len(rule_set.rules):
        raise RuleOperationError("rule index is out of range")

    rules = list(rule_set.rules)
    del rules[index]
    return RuleSet(version=rule_set.version, rules=rules)


def duplicate_rule(rule_set: RuleSet, index: int) -> RuleSet:
    """Return a new RuleSet with the selected rule copied after itself."""
    if index < 0 or index >= len(rule_set.rules):
        raise RuleOperationError("rule index is out of range")

    rules = list(rule_set.rules)
    original = rules[index]
    duplicated = replace(
        original,
        name=_copy_rule_name(original.name, {rule.name for rule in rules}),
    )
    rules.insert(index + 1, duplicated)
    return RuleSet(version=rule_set.version, rules=rules)


def move_rule(rule_set: RuleSet, index: int, target_index: int) -> RuleSet:
    """Return a new RuleSet with one rule moved to target_index."""
    if index < 0 or index >= len(rule_set.rules):
        raise RuleOperationError("rule index is out of range")
    if target_index < 0 or target_index >= len(rule_set.rules):
        raise RuleOperationError("target rule index is out of range")

    rules = list(rule_set.rules)
    rule = rules.pop(index)
    rules.insert(target_index, rule)
    return RuleSet(version=rule_set.version, rules=rules)


def reorder_rules(rule_set: RuleSet, order: list[int]) -> RuleSet:
    """Return a new RuleSet reordered by a list of original indices."""
    if len(order) != len(rule_set.rules):
        raise RuleOperationError("rule order length does not match rule count")
    if sorted(order) != list(range(len(rule_set.rules))):
        raise RuleOperationError("rule order must contain each rule index exactly once")

    return RuleSet(
        version=rule_set.version,
        rules=[rule_set.rules[index] for index in order],
    )


def _copy_rule_name(name: str, existing_names: set[str]) -> str:
    base_name = f"{name} copy"
    if base_name not in existing_names:
        return base_name

    suffix = 2
    while f"{base_name} {suffix}" in existing_names:
        suffix += 1

    return f"{base_name} {suffix}"


def make_image_path_relative(rule: Rule, base_dir: str | Path) -> Rule:
    """Return a copy of rule with image path relative to base_dir when possible."""
    image_path = Path(rule.image)
    if not image_path.is_absolute():
        return rule

    try:
        relative_image = image_path.resolve().relative_to(Path(base_dir).resolve())
    except ValueError:
        return rule

    return Rule(
        enabled=rule.enabled,
        name=rule.name,
        image=relative_image.as_posix(),
        region=rule.region,
        confidence=rule.confidence,
        action=rule.action,
        cooldown=rule.cooldown,
    )


def make_rule_set_image_paths_relative(rule_set: RuleSet, base_dir: str | Path) -> RuleSet:
    """Return a RuleSet with absolute image paths converted relative to base_dir."""
    return RuleSet(
        version=rule_set.version,
        rules=[make_image_path_relative(rule, base_dir) for rule in rule_set.rules],
    )

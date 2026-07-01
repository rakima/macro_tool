"""Rule JSON loading and saving."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models import RuleSet, RuleValidationError


class RuleStorageError(RuntimeError):
    """Raised when a rule file cannot be loaded or saved."""


def load_rules(path: str | Path) -> RuleSet:
    """Load a rule set from JSON.

    Missing files are treated as an empty rule set so the first application
    launch can start without a pre-existing configuration file.
    """
    rule_path = Path(path)
    if not rule_path.exists():
        return RuleSet(rules=[])

    try:
        with rule_path.open("r", encoding="utf-8") as file:
            data: Any = json.load(file)
    except json.JSONDecodeError as error:
        raise RuleStorageError(f"Invalid JSON in rule file: {rule_path}") from error
    except OSError as error:
        raise RuleStorageError(f"Could not read rule file: {rule_path}") from error

    try:
        return RuleSet.from_dict(data)
    except (KeyError, RuleValidationError, TypeError) as error:
        raise RuleStorageError(f"Invalid rule data in file: {rule_path}") from error


def save_rules(path: str | Path, rule_set: RuleSet) -> None:
    """Save a rule set as pretty-printed JSON."""
    if not isinstance(rule_set, RuleSet):
        raise RuleStorageError("rule_set must be a RuleSet")

    rule_path = Path(path)

    try:
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        with rule_path.open("w", encoding="utf-8") as file:
            json.dump(rule_set.to_dict(), file, ensure_ascii=False, indent=2)
            file.write("\n")
    except OSError as error:
        raise RuleStorageError(f"Could not write rule file: {rule_path}") from error

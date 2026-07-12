"""Rule JSON loading and saving."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models import RuleSet, RuleValidationError


class RuleStorageError(RuntimeError):
    """Raised when a rule file cannot be loaded or saved."""


@dataclass(frozen=True)
class RuleProfile:
    title: str
    path: Path


def list_rule_profiles(base_dir: str | Path = ".") -> list[RuleProfile]:
    """List the root rules.json and rule JSON files from the rules directory."""
    root_dir = Path(base_dir)
    profile_paths = []

    legacy_rules_path = root_dir / "rules.json"
    if legacy_rules_path.is_file():
        profile_paths.append(legacy_rules_path)

    profiles_dir = root_dir / "rules"
    if profiles_dir.exists() and profiles_dir.is_dir():
        profile_paths.extend(
            path
            for path in sorted(profiles_dir.glob("*.json"), key=lambda item: item.stem.lower())
            if path.is_file()
        )

    return _title_rule_profiles(profile_paths)


def _title_rule_profiles(paths: list[Path]) -> list[RuleProfile]:
    title_counts: dict[str, int] = {}
    profiles = []
    for path in paths:
        base_title = path.stem
        count = title_counts.get(base_title, 0)
        title_counts[base_title] = count + 1
        title = base_title if count == 0 else f"{base_title} ({count})"
        profiles.append(RuleProfile(title=title, path=path))

    return profiles


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

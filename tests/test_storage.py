import json

import pytest

from app.models import Action, Region, Rule, RuleSet
from app.storage import RuleStorageError, list_rule_profiles, load_rules, save_rules


def make_rule_set() -> RuleSet:
    return RuleSet(
        rules=[
            Rule(
                enabled=True,
                name="Click start button",
                image="images/start_button.png",
                region=Region(x=100, y=200, width=300, height=120),
                confidence=0.85,
                action=Action(type="click", button="left"),
                cooldown=1.5,
            )
        ]
    )


def test_load_rules_returns_empty_rule_set_when_file_is_missing(tmp_path):
    rule_set = load_rules(tmp_path / "missing.json")

    assert rule_set == RuleSet(rules=[])


def test_save_and_load_rules_round_trip(tmp_path):
    path = tmp_path / "rules.json"
    rule_set = make_rule_set()

    save_rules(path, rule_set)

    assert load_rules(path) == rule_set


def test_save_rules_creates_parent_directories(tmp_path):
    path = tmp_path / "configs" / "rules.json"

    save_rules(path, make_rule_set())

    assert path.exists()


def test_save_rules_writes_pretty_json(tmp_path):
    path = tmp_path / "rules.json"

    save_rules(path, make_rule_set())

    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert json.loads(text)["version"] == 1
    assert '  "rules": [' in text


def test_load_rules_rejects_invalid_json(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(RuleStorageError, match="Invalid JSON"):
        load_rules(path)


def test_load_rules_rejects_invalid_rule_data(tmp_path):
    path = tmp_path / "rules.json"
    path.write_text(
        json.dumps({"version": 1, "rules": [{"enabled": True}]}),
        encoding="utf-8",
    )

    with pytest.raises(RuleStorageError, match="Invalid rule data"):
        load_rules(path)


def test_save_rules_rejects_non_rule_set(tmp_path):
    with pytest.raises(RuleStorageError, match="RuleSet"):
        save_rules(tmp_path / "rules.json", object())  # type: ignore[arg-type]


def test_list_rule_profiles_returns_json_files_from_rules_directory(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "beta.json").write_text("{}", encoding="utf-8")
    (rules_dir / "alpha.json").write_text("{}", encoding="utf-8")
    (rules_dir / "memo.txt").write_text("ignore", encoding="utf-8")

    profiles = list_rule_profiles(tmp_path)

    assert [profile.title for profile in profiles] == ["alpha", "beta"]
    assert [profile.path for profile in profiles] == [
        rules_dir / "alpha.json",
        rules_dir / "beta.json",
    ]


def test_list_rule_profiles_includes_root_rules_json(tmp_path):
    rules_path = tmp_path / "rules.json"
    rules_path.write_text("{}", encoding="utf-8")

    profiles = list_rule_profiles(tmp_path)

    assert [profile.title for profile in profiles] == ["rules"]
    assert [profile.path for profile in profiles] == [rules_path]


def test_list_rule_profiles_disambiguates_duplicate_rules_title(tmp_path):
    root_rules_path = tmp_path / "rules.json"
    rules_dir = tmp_path / "rules"
    nested_rules_path = rules_dir / "rules.json"
    rules_dir.mkdir()
    root_rules_path.write_text("{}", encoding="utf-8")
    nested_rules_path.write_text("{}", encoding="utf-8")

    profiles = list_rule_profiles(tmp_path)

    assert [profile.title for profile in profiles] == ["rules", "rules (1)"]
    assert [profile.path for profile in profiles] == [root_rules_path, nested_rules_path]


def test_list_rule_profiles_returns_empty_list_without_rules_directory(tmp_path):
    assert list_rule_profiles(tmp_path) == []

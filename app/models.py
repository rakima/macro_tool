"""Rule data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar


class RuleValidationError(ValueError):
    """Raised when a rule model receives invalid data."""


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuleValidationError(f"{field_name} must be an object")
    return value


@dataclass(frozen=True)
class Offset:
    x: int = 0
    y: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.x, int):
            raise RuleValidationError("offset.x must be an integer")
        if not isinstance(self.y, int):
            raise RuleValidationError("offset.y must be an integer")

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Offset:
        if data is None:
            return cls()

        mapping = _require_mapping(data, "offset")
        return cls(
            x=mapping.get("x", 0),
            y=mapping.get("y", 0),
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
        }


@dataclass(frozen=True)
class Region:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        for field_name in ("x", "y", "width", "height"):
            if not isinstance(getattr(self, field_name), int):
                raise RuleValidationError(f"region.{field_name} must be an integer")

        if self.width <= 0:
            raise RuleValidationError("region.width must be greater than 0")
        if self.height <= 0:
            raise RuleValidationError("region.height must be greater than 0")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Region:
        mapping = _require_mapping(data, "region")
        return cls(
            x=mapping["x"],
            y=mapping["y"],
            width=mapping["width"],
            height=mapping["height"],
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class Action:
    type: str
    button: str
    offset: Offset = field(default_factory=Offset)

    SUPPORTED_TYPES: ClassVar[set[str]] = {"click"}
    SUPPORTED_BUTTONS: ClassVar[set[str]] = {"left", "right", "middle"}

    def __post_init__(self) -> None:
        if self.type not in self.SUPPORTED_TYPES:
            raise RuleValidationError("action.type must be click")
        if self.button not in self.SUPPORTED_BUTTONS:
            raise RuleValidationError("action.button must be left, right, or middle")
        if not isinstance(self.offset, Offset):
            raise RuleValidationError("action.offset must be an Offset")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Action:
        mapping = _require_mapping(data, "action")
        return cls(
            type=mapping["type"],
            button=mapping["button"],
            offset=Offset.from_dict(mapping.get("offset")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "button": self.button,
            "offset": self.offset.to_dict(),
        }


@dataclass(frozen=True)
class Rule:
    enabled: bool
    name: str
    image: str
    region: Region
    confidence: float
    action: Action
    cooldown: float

    def __post_init__(self) -> None:
        if not isinstance(self.enabled, bool):
            raise RuleValidationError("enabled must be a boolean")
        if not isinstance(self.name, str) or not self.name.strip():
            raise RuleValidationError("name must be a non-empty string")
        if not isinstance(self.image, str) or not self.image.strip():
            raise RuleValidationError("image must be a non-empty string")
        if not isinstance(self.region, Region):
            raise RuleValidationError("region must be a Region")
        if not isinstance(self.action, Action):
            raise RuleValidationError("action must be an Action")
        if not isinstance(self.confidence, (int, float)):
            raise RuleValidationError("confidence must be a number")
        if not 0.0 <= self.confidence <= 1.0:
            raise RuleValidationError("confidence must be between 0.0 and 1.0")
        if not isinstance(self.cooldown, (int, float)):
            raise RuleValidationError("cooldown must be a number")
        if self.cooldown < 0:
            raise RuleValidationError("cooldown must be greater than or equal to 0")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        mapping = _require_mapping(data, "rule")
        return cls(
            enabled=mapping["enabled"],
            name=mapping["name"],
            image=mapping["image"],
            region=Region.from_dict(mapping["region"]),
            confidence=mapping["confidence"],
            action=Action.from_dict(mapping["action"]),
            cooldown=mapping["cooldown"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "name": self.name,
            "image": self.image,
            "region": self.region.to_dict(),
            "confidence": self.confidence,
            "action": self.action.to_dict(),
            "cooldown": self.cooldown,
        }


@dataclass(frozen=True)
class RuleSet:
    rules: list[Rule]
    version: int = 1

    SUPPORTED_VERSION: ClassVar[int] = 1

    def __post_init__(self) -> None:
        if self.version != self.SUPPORTED_VERSION:
            raise RuleValidationError("version must be 1")
        if not isinstance(self.rules, list):
            raise RuleValidationError("rules must be a list")
        if not all(isinstance(rule, Rule) for rule in self.rules):
            raise RuleValidationError("rules must contain only Rule objects")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleSet:
        mapping = _require_mapping(data, "rule set")
        version = mapping.get("version", cls.SUPPORTED_VERSION)
        rules = mapping.get("rules", [])
        if not isinstance(rules, list):
            raise RuleValidationError("rules must be a list")

        return cls(
            version=version,
            rules=[Rule.from_dict(rule_data) for rule_data in rules],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "rules": [rule.to_dict() for rule in self.rules],
        }

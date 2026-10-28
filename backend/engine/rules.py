"""ContentGuard · Rule engine — YAML-driven regex pattern matching.

Loads rules from ``config/rules.yaml``, compiles them once, and runs them
against input text to produce ``RuleSignal`` objects.  Each rule carries a
score, category, and optional ``auto_block`` flag that the decision engine
inspects downstream.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from models.schemas import RuleSignal


@dataclass
class CompiledRule:
    name: str
    category: str
    pattern: re.Pattern
    score: float
    auto_block: bool
    description: str


@dataclass
class RuleConfig:
    version: str
    categories: list[str]
    rules: list[CompiledRule]
    thresholds: dict[str, Any] = field(default_factory=dict)
    severity_map: dict[str, Any] = field(default_factory=dict)


def load_rules(path: Path) -> RuleConfig:
    """Parse ``rules.yaml`` and compile all regex patterns."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    compiled: list[CompiledRule] = []
    for r in raw.get("rules", []):
        compiled.append(CompiledRule(
            name=r["name"],
            category=r["category"],
            pattern=re.compile(r["pattern"], re.IGNORECASE),
            score=float(r["score"]),
            auto_block=bool(r.get("auto_block", False)),
            description=r.get("description", ""),
        ))

    return RuleConfig(
        version=raw.get("version", "unknown"),
        categories=raw.get("categories", []),
        rules=compiled,
        thresholds=raw.get("thresholds", {}),
        severity_map=raw.get("severity", {}),
    )


class RuleEngine:
    """Stateless rule matcher.  Thread-safe once constructed."""

    def __init__(self, config: RuleConfig) -> None:
        self.config = config

    @property
    def policy_version(self) -> str:
        return self.config.version

    def match(self, text: str) -> list[dict]:
        """Return a list of dicts with keys ``signal`` and ``auto_block``."""
        results: list[dict] = []
        lower = text.lower()
        for rule in self.config.rules:
            if rule.pattern.search(lower):
                results.append({
                    "signal": RuleSignal(name=rule.name, score=rule.score),
                    "auto_block": rule.auto_block,
                    "category": rule.category,
                })
        return results

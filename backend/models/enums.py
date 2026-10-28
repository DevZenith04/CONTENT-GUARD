"""ContentGuard · Pydantic enums shared across models, routes and engine."""

from enum import Enum


class Outcome(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class FinalOutcome(str, Enum):
    """Valid final outcomes for reviewer decisions (REVIEW is not a valid final outcome)."""
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"


class Severity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Mode(str, Enum):
    RULE_ONLY = "rule_only"
    LLM_ONLY = "llm_only"
    HYBRID = "hybrid"


class Category(str, Enum):
    THREAT = "threat"
    HARASSMENT = "harassment"
    HATE = "hate"
    SELF_HARM = "self_harm"


class SignalSource(str, Enum):
    RULE = "rule"
    LLM = "llm"


class ReviewStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"

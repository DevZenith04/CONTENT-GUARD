"""ContentGuard · Decision engine — combines rule signals + LLM signals into a single outcome.

Decision logic (matches the frontend preview fixtures and docs):
  1. If any rule with ``auto_block=True`` fired  →  BLOCK
  2. If rule_score >= block_threshold AND llm_confidence >= block_confidence  →  BLOCK
  3. If any LLM signal has ``abstain=True``  →  REVIEW
  4. If any signal and max llm_confidence >= review_threshold  →  REVIEW
  5. If any rule matched but llm_confidence is below review threshold  →  WARN
  6. Otherwise  →  ALLOW
"""

from __future__ import annotations

from dataclasses import dataclass

from models.enums import Outcome, Severity
from models.schemas import LLMSignal, RuleSignal


@dataclass
class DecisionResult:
    outcome: Outcome
    severity: Severity
    categories: list[str]
    explanation: str


# Default thresholds — overridden from rules.yaml in the pipeline
_DEFAULTS = {
    "block": {"rule_score": 0.9, "llm_confidence": 0.85},
    "review": {"llm_confidence": 0.3},
}


class DecisionEngine:
    """Stateless decision maker.  Takes signals and produces a verdict."""

    def __init__(self, thresholds: dict | None = None) -> None:
        self.t = thresholds or _DEFAULTS

    def decide(
        self,
        rule_hits: list[dict],       # from RuleEngine.match()
        llm_signals: list[LLMSignal],
        mode: str,
    ) -> DecisionResult:
        categories: set[str] = set()
        explanations: list[str] = []

        # Gather all rule-related info
        has_auto_block = False
        max_rule_score = 0.0
        for hit in rule_hits:
            categories.add(hit["category"])
            max_rule_score = max(max_rule_score, hit["signal"].score)
            if hit["auto_block"]:
                has_auto_block = True

        # Gather all LLM-related info
        max_llm_conf = 0.0
        dominant_llm_sig = None
        for sig in llm_signals:
            categories.add(sig.category)
            if sig.confidence > max_llm_conf:
                max_llm_conf = sig.confidence
                dominant_llm_sig = sig

        # An abstention is only meaningful if the dominant signal itself abstained and no strong violation exists
        has_abstain = bool(dominant_llm_sig and dominant_llm_sig.abstain and max_llm_conf < 0.75)

        block_t = self.t.get("block", _DEFAULTS["block"])
        review_t = self.t.get("review", _DEFAULTS["review"])

        # ── Decision cascade ──────────────────────────────────

        # 1) Auto-block rule
        if has_auto_block and mode != "llm_only":
            if mode != "rule_only" and max_llm_conf >= block_t["llm_confidence"]:
                explanations.append(
                    "An auto-block rule matched and the contextual model confirms the violation."
                )
            else:
                explanations.append(
                    "An auto-block rule matched. Only rules marked auto_block can block without contextual confirmation."
                )
            return self._result(Outcome.BLOCK, Severity.HIGH, categories, explanations)

        # 2) High rule + high LLM → BLOCK
        if (mode != "llm_only" and max_rule_score >= block_t["rule_score"] and
                mode != "rule_only" and max_llm_conf >= block_t["llm_confidence"]):
            explanations.append(
                f"Rule score ({max_rule_score:.2f}) and model confidence ({max_llm_conf:.2f}) "
                f"both exceed the block threshold."
            )
            return self._result(Outcome.BLOCK, Severity.HIGH, categories, explanations)

        # 3) Overwhelming contextual confidence (>= 0.90) or LLM-only mode with high confidence → BLOCK
        if mode != "rule_only" and (
            max_llm_conf >= 0.90 or (mode == "llm_only" and max_llm_conf >= block_t["llm_confidence"])
        ):
            explanations.append(
                f"The contextual model identified an unambiguous severe violation with high confidence ({max_llm_conf:.2f})."
            )
            return self._result(Outcome.BLOCK, Severity.HIGH, categories, explanations)

        # 4) Rule-only mode routing
        if mode == "rule_only" and rule_hits:
            if max_rule_score >= 0.7:
                explanations.append(
                    f"Rule match on a {', '.join(sorted(categories))} pattern (score: {max_rule_score:.2f}). "
                    "Rule-only mode routes high-confidence pattern matches to human review."
                )
                return self._result(Outcome.REVIEW, Severity.HIGH if max_rule_score >= 0.85 else Severity.MEDIUM, categories, explanations)
            else:
                explanations.append(
                    f"Rule match on a {', '.join(sorted(categories))} pattern with moderate score ({max_rule_score:.2f}). "
                    "In rule-only mode, this issues a warning."
                )
                return self._result(Outcome.WARN, Severity.LOW, categories, explanations)

        # 5) Abstain → REVIEW (sarcasm/metaphor band when not blocked)
        if has_abstain:
            explanations.append(
                "The contextual model abstained, which suggests sarcasm or metaphor. Routed to a reviewer."
            )
            severity = self._severity_from_confidence(max_llm_conf)
            return self._result(Outcome.REVIEW, severity, categories, explanations)

        # 6) Signals present + LLM in review band → REVIEW
        has_signals = bool(rule_hits) or bool(llm_signals)
        if has_signals and max_llm_conf >= review_t["llm_confidence"]:
            if rule_hits and mode != "llm_only":
                explanations.append(
                    f"Rule match on a {', '.join(sorted(categories))} pattern. "
                    f"The contextual model reports confidence at {max_llm_conf:.2f}, inside the review band."
                )
            else:
                explanations.append(
                    f"The contextual model reports ambiguous signals at moderate confidence ({max_llm_conf:.2f}). "
                    "A person should check."
                )
            severity = self._severity_from_confidence(max_llm_conf)
            return self._result(Outcome.REVIEW, severity, categories, explanations)

        # 7) Rule matched but LLM is low → WARN
        if rule_hits and mode != "llm_only":
            explanations.append(
                f"A rule matched but contextual confidence is low ({max_llm_conf:.2f}), "
                "so the result is a warning, not a block."
            )
            return self._result(Outcome.WARN, Severity.LOW, categories, explanations)

        # 8) LLM only mode with weak signals → WARN
        if llm_signals and mode == "llm_only" and max_llm_conf < review_t["llm_confidence"]:
            explanations.append(
                f"The model detected weak signals ({max_llm_conf:.2f}) below the review threshold."
            )
            return self._result(Outcome.WARN, Severity.LOW, categories, explanations)

        # 9) Nothing → ALLOW
        explanations.append("No configured violation detected with sufficient evidence.")
        return self._result(Outcome.ALLOW, Severity.NONE, set(), explanations)

    @staticmethod
    def _severity_from_confidence(conf: float) -> Severity:
        if conf >= 0.7:
            return Severity.HIGH
        if conf >= 0.5:
            return Severity.MEDIUM
        return Severity.LOW

    @staticmethod
    def _result(outcome: Outcome, severity: Severity, cats: set, explanations: list[str]) -> DecisionResult:
        return DecisionResult(
            outcome=outcome,
            severity=severity,
            categories=sorted(cats),
            explanation=" ".join(explanations),
        )

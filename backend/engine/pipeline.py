"""ContentGuard · Pipeline orchestrator — Input → Rules → LLM → Decision → Outcome.

Ties the rule engine, transformer analyzer, and decision engine together.
Manages the full lifecycle of a moderation request:

  1. Receive text + mode
  2. Run rule engine (unless ``llm_only``)
  3. Run transformer (unless ``rule_only``)
  4. Feed signals into decision engine
  5. Persist event + optional review case
  6. Return structured response
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime

from config import settings
from models.enums import Mode, Outcome, ReviewStatus
from models.schemas import (
    EventResponse,
    HistoryEntry,
    LLMSignal,
    ModerateResponse,
    ReviewDetail,
    RuleSignal,
)

from .decision import DecisionEngine
from .llm import TransformerAnalyzer
from .rules import RuleEngine, load_rules

logger = logging.getLogger("contentguard.pipeline")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:7].upper()}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Pipeline:
    """Central orchestrator.  Initialised once at app startup."""

    def __init__(self, settings_obj=None) -> None:
        s = settings_obj or settings
        # Rule engine
        rule_config = load_rules(s.rules_path)
        self.rules = RuleEngine(rule_config)
        self.decision = DecisionEngine(thresholds=rule_config.thresholds)

        # Transformer
        self.llm = TransformerAnalyzer(model_name=s.transformer_model)

    async def startup(self) -> None:
        """Load the transformer model (called once during app lifespan)."""
        await self.llm.load()

    @property
    def policy_version(self) -> str:
        return self.rules.policy_version

    @property
    def model_version(self) -> str:
        return self.llm.model_version

    async def analyze(self, text: str, mode: Mode):
        """Pure analysis: no persistence. Used by the API and the evaluation runner."""
        rule_hits: list[dict] = []
        if mode != Mode.LLM_ONLY:
            rule_hits = self.rules.match(text)

        llm_signals: list[LLMSignal] = []
        if mode != Mode.RULE_ONLY:
            llm_signals = await asyncio.to_thread(self.llm.predict, text)

        result = self.decision.decide(rule_hits, llm_signals, mode.value)
        return result, rule_hits, llm_signals

    async def moderate(self, text: str, mode: Mode, store) -> ModerateResponse:
        """Run the full moderation pipeline and persist the event."""
        start = time.perf_counter_ns()

        result, rule_hits, llm_signals = await self.analyze(text, mode)

        elapsed_ms = int((time.perf_counter_ns() - start) / 1_000_000)
        request_id = _new_id("mod")

        # Flatten signals list for response
        all_signals: list[RuleSignal | LLMSignal] = [h["signal"] for h in rule_hits] + llm_signals

        # ── Stage 4: Persist ──────────────────────────────
        now = _now_iso()
        review = None
        if result.outcome == Outcome.REVIEW:
            case_id = _new_id("case")
            review = ReviewDetail(
                case_id=case_id,
                status=ReviewStatus.OPEN,
                history=[HistoryEntry(at=now, event="Case opened", actor="system")],
            )

        active_model_version = "none" if mode == Mode.RULE_ONLY else self.model_version

        event = EventResponse(
            id=request_id,
            created_at=now,
            mode=mode,
            outcome=result.outcome,
            severity=result.severity,
            categories=result.categories,
            explanation=result.explanation,
            signals=all_signals,
            policy_version=self.policy_version,
            model_version=active_model_version,
            latency_ms=elapsed_ms,
            text_length=len(text),
            review=review,
        )

        await store.save_event(event)

        return ModerateResponse(
            request_id=request_id,
            outcome=result.outcome,
            severity=result.severity,
            categories=result.categories,
            explanation=result.explanation,
            signals=all_signals,
            policy_version=self.policy_version,
            model_version=active_model_version,
            latency_ms=elapsed_ms,
            mode=mode,
            preview=False,
        )

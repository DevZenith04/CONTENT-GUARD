"""ContentGuard · SQLite async storage for events and review cases.

Uses ``aiosqlite`` for non-blocking IO.  Events are serialised as JSON blobs
so the schema stays flexible while still supporting ID lookups and filtered
review queries.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite

from models.enums import FinalOutcome, ReviewStatus
from models.schemas import (
    DecisionResponse,
    EventResponse,
    HistoryEntry,
    ReviewSummary,
)

logger = logging.getLogger("contentguard.store")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,
    outcome     TEXT NOT NULL,
    severity    TEXT NOT NULL,
    mode        TEXT NOT NULL,
    data        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    case_id     TEXT PRIMARY KEY,
    event_id    TEXT NOT NULL REFERENCES events(id),
    status      TEXT NOT NULL DEFAULT 'open',
    severity    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    data        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status);
"""


class Store:
    """Async SQLite store.  Call ``.connect()`` at startup, ``.close()`` at shutdown."""

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(str(self._path))
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()
        await self._seed_if_empty()
        logger.info("SQLite store ready at %s", self._path)

    async def _seed_if_empty(self) -> None:
        cursor = await self._db.execute("SELECT COUNT(*) as cnt FROM events")
        row = await cursor.fetchone()
        if not row or row["cnt"] > 0:
            return

        logger.info("Seeding initial events and review cases into SQLite store...")
        from models.enums import Category, Mode, Outcome, Severity, SignalSource
        from models.schemas import EventResponse, HistoryEntry, LLMSignal, ReviewDetail, RuleSignal

        seeds = [
            EventResponse(
                id="mod_01HZX1A",
                created_at="2026-10-26T09:14:22Z",
                mode=Mode.HYBRID,
                outcome=Outcome.REVIEW,
                severity=Severity.HIGH,
                categories=["threat"],
                explanation="Rule match on a threat pattern. The contextual model reports a direct threat toward a person at 0.91, inside the review band.",
                signals=[
                    RuleSignal(name="threat_direct_first_person", score=0.8),
                    LLMSignal(category="threat", confidence=0.91, abstain=False),
                ],
                policy_version="2026.01.0",
                model_version="transformer:unitary/toxic-bert",
                latency_ms=812,
                text_length=41,
                review=ReviewDetail(
                    case_id="case_7F2",
                    status=ReviewStatus.OPEN,
                    reviewer=None,
                    final_outcome=None,
                    reason=None,
                    history=[HistoryEntry(at="2026-10-26T09:14:23Z", event="Case opened", actor="system")],
                ),
            ),
            EventResponse(
                id="mod_01HZX2B",
                created_at="2026-10-26T09:21:07Z",
                mode=Mode.HYBRID,
                outcome=Outcome.WARN,
                severity=Severity.LOW,
                categories=["harassment"],
                explanation="An insult term matched inside a quoted or reported context. Contextual confidence is moderate, so the result is a warning, not a block.",
                signals=[
                    RuleSignal(name="insult_term", score=0.4),
                    LLMSignal(category="harassment", confidence=0.52, abstain=False),
                ],
                policy_version="2026.01.0",
                model_version="transformer:unitary/toxic-bert",
                latency_ms=640,
                text_length=88,
                review=None,
            ),
            EventResponse(
                id="mod_01HZX3C",
                created_at="2026-10-26T09:33:45Z",
                mode=Mode.HYBRID,
                outcome=Outcome.ALLOW,
                severity=Severity.NONE,
                categories=[],
                explanation="No configured violation detected with sufficient evidence.",
                signals=[],
                policy_version="2026.01.0",
                model_version="transformer:unitary/toxic-bert",
                latency_ms=590,
                text_length=52,
                review=None,
            ),
            EventResponse(
                id="mod_01HZX4D",
                created_at="2026-10-26T09:40:11Z",
                mode=Mode.HYBRID,
                outcome=Outcome.BLOCK,
                severity=Severity.HIGH,
                categories=["threat"],
                explanation="An auto-block rule matched and the contextual model confirms a direct threat. Only rules marked auto_block can block without contextual confirmation.",
                signals=[
                    RuleSignal(name="threat_auto_block", score=0.97),
                    LLMSignal(category="threat", confidence=0.95, abstain=False),
                ],
                policy_version="2026.01.0",
                model_version="transformer:unitary/toxic-bert",
                latency_ms=905,
                text_length=37,
                review=None,
            ),
            EventResponse(
                id="mod_01HZX5E",
                created_at="2026-10-26T10:02:18Z",
                mode=Mode.LLM_ONLY,
                outcome=Outcome.REVIEW,
                severity=Severity.MEDIUM,
                categories=["hate"],
                explanation="The contextual model abstained, which suggests sarcasm or metaphor. Routed to a reviewer.",
                signals=[
                    LLMSignal(category="hate", confidence=0.58, abstain=True),
                ],
                policy_version="2026.01.0",
                model_version="transformer:unitary/toxic-bert",
                latency_ms=730,
                text_length=64,
                review=ReviewDetail(
                    case_id="case_3A9",
                    status=ReviewStatus.RESOLVED,
                    reviewer="rev_04",
                    final_outcome=FinalOutcome.WARN,
                    reason="Sarcastic quotation with no target. Warning only.",
                    history=[
                        HistoryEntry(at="2026-10-26T10:02:19Z", event="Case opened", actor="system"),
                        HistoryEntry(at="2026-10-26T10:15:40Z", event="Assigned", actor="rev_04"),
                        HistoryEntry(at="2026-10-26T10:21:03Z", event="Resolved as WARN", actor="rev_04"),
                    ],
                ),
            ),
            EventResponse(
                id="mod_01HZX6F",
                created_at="2026-10-26T10:30:44Z",
                mode=Mode.HYBRID,
                outcome=Outcome.REVIEW,
                severity=Severity.MEDIUM,
                categories=["self_harm"],
                explanation="No rule matched. The contextual model reports ambiguous distress language at moderate confidence. A person should check for risk.",
                signals=[
                    LLMSignal(category="self_harm", confidence=0.44, abstain=False),
                ],
                policy_version="2026.01.0",
                model_version="transformer:unitary/toxic-bert",
                latency_ms=701,
                text_length=73,
                review=ReviewDetail(
                    case_id="case_9C1",
                    status=ReviewStatus.OPEN,
                    reviewer=None,
                    final_outcome=None,
                    reason=None,
                    history=[HistoryEntry(at="2026-10-26T10:30:45Z", event="Case opened", actor="system")],
                ),
            ),
        ]
        for item in seeds:
            await self.save_event(item)

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    # ── Events ────────────────────────────────────────────

    async def save_event(self, event: EventResponse) -> None:
        data = event.model_dump(mode="json")
        await self._db.execute(
            "INSERT INTO events (id, created_at, outcome, severity, mode, data) VALUES (?, ?, ?, ?, ?, ?)",
            (event.id, event.created_at, event.outcome.value, event.severity.value, event.mode.value, json.dumps(data)),
        )
        # If the event has a review case, persist it too
        if event.review:
            r = event.review
            await self._db.execute(
                "INSERT INTO reviews (case_id, event_id, status, severity, created_at, data) VALUES (?, ?, ?, ?, ?, ?)",
                (r.case_id, event.id, r.status.value, event.severity.value, event.created_at, json.dumps(r.model_dump(mode="json"))),
            )
        await self._db.commit()

    async def get_event(self, event_id: str) -> Optional[EventResponse]:
        cursor = await self._db.execute("SELECT data FROM events WHERE id = ?", (event_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        data = json.loads(row["data"])
        # Merge latest review data if exists
        if data.get("review") and data["review"].get("case_id"):
            review_data = await self._get_review_data(data["review"]["case_id"])
            if review_data:
                data["review"] = review_data
        return EventResponse(**data)

    async def _get_review_data(self, case_id: str) -> Optional[dict]:
        cursor = await self._db.execute("SELECT data FROM reviews WHERE case_id = ?", (case_id,))
        row = await cursor.fetchone()
        return json.loads(row["data"]) if row else None

    # ── Reviews ───────────────────────────────────────────

    async def list_reviews(self) -> list[ReviewSummary]:
        cursor = await self._db.execute(
            """SELECT r.case_id, r.event_id, r.status, r.severity, r.created_at, r.data,
                      e.outcome, e.data as event_data
               FROM reviews r
               JOIN events e ON e.id = r.event_id
               ORDER BY r.created_at DESC"""
        )
        rows = await cursor.fetchall()
        result: list[ReviewSummary] = []
        for row in rows:
            review = json.loads(row["data"])
            event = json.loads(row["event_data"])
            result.append(ReviewSummary(
                case_id=row["case_id"],
                event_id=row["event_id"],
                status=row["status"],
                severity=row["severity"],
                categories=event.get("categories", []),
                created_at=row["created_at"],
                outcome=row["outcome"],
                final_outcome=review.get("final_outcome"),
            ))
        return result

    async def decide_review(
        self, case_id: str, final_outcome: FinalOutcome, reason: str
    ) -> Optional[DecisionResponse]:
        cursor = await self._db.execute("SELECT data FROM reviews WHERE case_id = ?", (case_id,))
        row = await cursor.fetchone()
        if not row:
            return None

        review = json.loads(row["data"])
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        review["status"] = ReviewStatus.RESOLVED.value
        review["final_outcome"] = final_outcome.value
        review["reason"] = reason
        review["reviewer"] = "reviewer_01"
        review["history"].append({
            "at": now,
            "event": f"Resolved as {final_outcome.value}",
            "actor": "reviewer_01",
        })

        await self._db.execute(
            "UPDATE reviews SET status = ?, data = ? WHERE case_id = ?",
            (ReviewStatus.RESOLVED.value, json.dumps(review), case_id),
        )
        await self._db.commit()

        return DecisionResponse(
            case_id=case_id,
            status=ReviewStatus.RESOLVED,
            final_outcome=final_outcome,
        )

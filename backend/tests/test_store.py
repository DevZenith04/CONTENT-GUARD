from datetime import UTC, datetime
from pathlib import Path

import pytest
from models.enums import FinalOutcome, Mode, Outcome, ReviewStatus, Severity
from models.schemas import EventResponse, HistoryEntry, ReviewDetail
from storage.store import Store


@pytest.mark.asyncio
async def test_store_lifecycle(tmp_path: Path):
    db_file = tmp_path / "test_store.db"
    store = Store(db_file)
    await store.connect()

    # Create dummy event
    now = datetime.now(UTC).isoformat(timespec="seconds")
    case_id = "case_TEST01"
    review = ReviewDetail(
        case_id=case_id,
        status=ReviewStatus.OPEN,
        history=[HistoryEntry(at=now, event="Case opened", actor="system")],
    )

    event = EventResponse(
        id="mod_TEST01",
        created_at=now,
        mode=Mode.HYBRID,
        outcome=Outcome.REVIEW,
        severity=Severity.HIGH,
        categories=["threat"],
        explanation="Test event",
        signals=[],
        policy_version="2026.01.0",
        model_version="test-model",
        latency_ms=10,
        text_length=25,
        review=review,
    )

    # Save event
    await store.save_event(event)

    # Fetch event
    fetched = await store.get_event("mod_TEST01")
    assert fetched is not None
    assert fetched.id == "mod_TEST01"
    assert fetched.outcome == Outcome.REVIEW

    # List reviews
    reviews = await store.list_reviews()
    assert len(reviews) >= 1
    assert any(r.case_id == case_id for r in reviews)

    # Decide review
    decide_result = await store.decide_review(case_id, FinalOutcome.BLOCK, "Confirmed severe threat")
    assert decide_result is not None
    assert decide_result.status == ReviewStatus.RESOLVED
    assert decide_result.final_outcome == FinalOutcome.BLOCK

    # Decide unknown case returns None
    unknown_result = await store.decide_review("case_NON_EXISTENT", FinalOutcome.ALLOW, "reason")
    assert unknown_result is None

    # Fetch non-existent event returns None
    assert await store.get_event("mod_UNKNOWN") is None

    await store.close()

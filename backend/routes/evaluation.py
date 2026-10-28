"""ContentGuard · GET /v1/evaluation/latest route.

Returns the latest real evaluation run saved in `backend/results/` if available,
otherwise returns the fallback preview fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from models.schemas import (
    ConfusionCounts,
    EvaluationMeta,
    EvaluationResponse,
    LatencyStats,
    ModeEvaluation,
)

router = APIRouter()

# Fallback preview fixture
_FIXTURE = EvaluationResponse(
    meta=EvaluationMeta(
        dataset_hash="fixture-v1",
        items=200,
        policy_version="2026.01.0",
        model_version="transformer:unitary/toxic-bert",
        run_at=None,
        preview=True,
    ),
    modes={
        "rule_only": ModeEvaluation(
            review_rate=0.11,
            latency_ms=LatencyStats(median=14, p95=31),
            cost_per_1k=None,
            counts={
                "threat": ConfusionCounts(tp=31, fp=12, fn=20, tn=137),
                "harassment": ConfusionCounts(tp=22, fp=19, fn=28, tn=131),
                "hate": ConfusionCounts(tp=9, fp=6, fn=14, tn=171),
                "self_harm": ConfusionCounts(tp=5, fp=4, fn=9, tn=182),
            },
        ),
        "llm_only": ModeEvaluation(
            review_rate=0.18,
            latency_ms=LatencyStats(median=640, p95=1310),
            cost_per_1k=None,
            counts={
                "threat": ConfusionCounts(tp=44, fp=5, fn=7, tn=144),
                "harassment": ConfusionCounts(tp=38, fp=9, fn=12, tn=141),
                "hate": ConfusionCounts(tp=13, fp=4, fn=10, tn=173),
                "self_harm": ConfusionCounts(tp=8, fp=2, fn=6, tn=184),
            },
        ),
        "hybrid": ModeEvaluation(
            review_rate=0.16,
            latency_ms=LatencyStats(median=690, p95=1420),
            cost_per_1k=None,
            counts={
                "threat": ConfusionCounts(tp=46, fp=4, fn=5, tn=145),
                "harassment": ConfusionCounts(tp=41, fp=7, fn=9, tn=143),
                "hate": ConfusionCounts(tp=14, fp=3, fn=9, tn=174),
                "self_harm": ConfusionCounts(tp=9, fp=2, fn=5, tn=184),
            },
        ),
    },
)


@router.get("/evaluation/latest", response_model=EvaluationResponse)
async def evaluation_latest():
    """Return the latest evaluation results."""
    results_dir = Path(__file__).resolve().parent.parent / "results"
    if results_dir.exists():
        eval_files = sorted(results_dir.glob("eval_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if eval_files:
            try:
                latest_file = eval_files[0]
                data = json.loads(latest_file.read_text(encoding="utf-8"))
                return EvaluationResponse.model_validate(data)
            except (json.JSONDecodeError, ValueError, OSError):
                return _FIXTURE
    return _FIXTURE

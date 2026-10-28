"""ContentGuard · GET /v1/evaluation/latest route.

Returns the latest evaluation run.  For now this returns a pre-computed
fixture (same as the frontend preview) until a real evaluation runner
is wired up.  The evaluation runner (evaluation/runner.py) can be hooked
in later to compute results against a labelled dataset.
"""

from fastapi import APIRouter

from models.schemas import (
    ConfusionCounts,
    EvaluationMeta,
    EvaluationResponse,
    LatencyStats,
    ModeEvaluation,
)

router = APIRouter()

# Pre-computed evaluation fixture — same data the frontend shows in preview mode.
# Replace with real runner output when a labelled dataset is available.
_FIXTURE = EvaluationResponse(
    meta=EvaluationMeta(
        dataset_hash="fixture-v1",
        items=200,
        policy_version="2026.01.0",
        model_version="transformer:unitary/toxic-bert",
        run_at=None,
        preview=False,
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
    return _FIXTURE

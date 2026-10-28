"""ContentGuard · Review queue routes.

  GET  /v1/reviews                       — list all review cases
  POST /v1/reviews/{case_id}/decision    — submit a reviewer decision
"""

from fastapi import APIRouter, HTTPException, Request
from models.schemas import DecisionRequest, DecisionResponse, ReviewSummary

router = APIRouter()


@router.get("/reviews", response_model=list[ReviewSummary])
async def list_reviews(request: Request):
    """Return all review cases, newest first."""
    store = request.app.state.store
    return await store.list_reviews()


@router.post("/reviews/{case_id}/decision", response_model=DecisionResponse)
async def decide_review(case_id: str, body: DecisionRequest, request: Request):
    """Record a reviewer's final decision on a case."""
    store = request.app.state.store
    result = await store.decide_review(case_id, body.final_outcome, body.reason)
    if not result:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"Case not found: {case_id}"}},
        )
    return result

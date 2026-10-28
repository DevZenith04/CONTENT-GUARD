"""ContentGuard · POST /v1/moderate route."""

from fastapi import APIRouter, HTTPException, Request
from models.schemas import ModerateRequest, ModerateResponse

router = APIRouter()


@router.post("/moderate", response_model=ModerateResponse)
async def moderate(body: ModerateRequest, request: Request):
    """Run the moderation pipeline on the submitted text."""
    pipeline = request.app.state.pipeline
    store = request.app.state.store

    if len(body.text) > request.app.state.settings.max_text_length:
        raise HTTPException(
            status_code=413,
            detail={"error": {"code": "text_too_long", "message": "Text exceeds the maximum length."}},
        )

    result = await pipeline.moderate(body.text, body.mode, store)
    return result

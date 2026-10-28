"""ContentGuard · GET /v1/moderations/{id} route."""

from fastapi import APIRouter, HTTPException, Request

from models.schemas import EventResponse

router = APIRouter()


@router.get("/moderations/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, request: Request):
    """Retrieve a single moderation event by ID."""
    store = request.app.state.store
    event = await store.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "not_found", "message": f"Event not found: {event_id}"}},
        )
    return event

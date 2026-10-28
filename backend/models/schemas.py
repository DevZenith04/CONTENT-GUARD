"""ContentGuard · Pydantic schemas for all API request / response shapes.
   These mirror exactly what the frontend (api.js) sends and expects."""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .enums import (
    Category, FinalOutcome, Mode, Outcome, ReviewStatus, Severity, SignalSource,
)


# ─── Request bodies ────────────────────────────────────────────────

class ModerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    mode: Mode = Mode.HYBRID


class DecisionRequest(BaseModel):
    final_outcome: FinalOutcome
    reason: str = Field(..., min_length=1)


# ─── Signals ───────────────────────────────────────────────────────

class RuleSignal(BaseModel):
    source: SignalSource = SignalSource.RULE
    name: str
    score: float = Field(..., ge=0.0, le=1.0)


class LLMSignal(BaseModel):
    source: SignalSource = SignalSource.LLM
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    abstain: bool = False


# ─── History entry ─────────────────────────────────────────────────

class HistoryEntry(BaseModel):
    at: str  # ISO datetime string
    event: str
    actor: str


# ─── Review case (nested in event) ────────────────────────────────

class ReviewDetail(BaseModel):
    case_id: str
    status: ReviewStatus
    reviewer: Optional[str] = None
    final_outcome: Optional[FinalOutcome] = None
    reason: Optional[str] = None
    history: list[HistoryEntry] = []


# ─── Response: POST /v1/moderate ───────────────────────────────────

class ModerateResponse(BaseModel):
    request_id: str
    outcome: Outcome
    severity: Severity
    categories: list[str] = []
    explanation: str
    signals: list[RuleSignal | LLMSignal] = []
    policy_version: str
    model_version: str
    latency_ms: Optional[int] = None
    mode: Mode
    preview: bool = False


# ─── Response: GET /v1/moderations/{id} ───────────────────────────

class EventResponse(BaseModel):
    id: str
    created_at: str
    mode: Mode
    outcome: Outcome
    severity: Severity
    categories: list[str] = []
    explanation: str
    signals: list[RuleSignal | LLMSignal] = []
    policy_version: str
    model_version: str
    latency_ms: Optional[int] = None
    text_length: Optional[int] = None
    review: Optional[ReviewDetail] = None


# ─── Response: GET /v1/reviews ─────────────────────────────────────

class ReviewSummary(BaseModel):
    case_id: str
    event_id: str
    status: ReviewStatus
    severity: Severity
    categories: list[str] = []
    created_at: str
    outcome: Outcome
    final_outcome: Optional[str] = None


# ─── Response: POST /v1/reviews/{case_id}/decision ────────────────

class DecisionResponse(BaseModel):
    case_id: str
    status: ReviewStatus
    final_outcome: FinalOutcome


# ─── Response: GET /v1/evaluation/latest ──────────────────────────

class ConfusionCounts(BaseModel):
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0


class LatencyStats(BaseModel):
    median: int
    p95: int


class ModeEvaluation(BaseModel):
    review_rate: float
    latency_ms: LatencyStats
    cost_per_1k: Optional[float] = None
    counts: dict[str, ConfusionCounts]


class EvaluationMeta(BaseModel):
    dataset_hash: str
    items: int
    policy_version: str
    model_version: str
    run_at: Optional[str] = None
    preview: bool = False


class EvaluationResponse(BaseModel):
    meta: EvaluationMeta
    modes: dict[str, ModeEvaluation]


# ─── Error envelope ───────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

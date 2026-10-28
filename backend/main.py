"""ContentGuard · FastAPI application entry point.

Wires together:
  - CORS middleware
  - Custom error handler (returns JSON error envelope the frontend expects)
  - Lifespan: loads transformer model + connects SQLite on startup
  - All /v1 routes
  - Static file serving for the frontend pages
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from engine.pipeline import Pipeline
from storage.store import Store

# ── Logging ────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("contentguard")

# ── Shared instances ──────────────────────────────────

pipeline = Pipeline()
store = Store(settings.db_path)

# ── Lifespan ──────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load model, connect DB.  Shutdown: close DB."""
    await store.connect()
    await pipeline.startup()
    app.state.pipeline = pipeline
    app.state.store = store
    app.state.settings = settings
    logger.info(
        "ContentGuard ready  ·  policy %s  ·  model %s  ·  db %s",
        pipeline.policy_version, pipeline.model_version, settings.db_path,
    )
    yield
    await store.close()
    logger.info("ContentGuard shut down.")


# ── App ───────────────────────────────────────────────

app = FastAPI(
    title="ContentGuard",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Error handlers (JSON envelope the frontend expects) ─

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc.errors())}},
    )


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "not_found", "message": "Resource not found."}},
    )


@app.exception_handler(Exception)
async def generic_error(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal", "message": "Internal server error."}},
    )


# ── Routes ─────────────────────────────────────────────

from routes.moderate import router as moderate_router
from routes.moderations import router as moderations_router
from routes.reviews import router as reviews_router
from routes.evaluation import router as evaluation_router

app.include_router(moderate_router, prefix="/v1")
app.include_router(moderations_router, prefix="/v1")
app.include_router(reviews_router, prefix="/v1")
app.include_router(evaluation_router, prefix="/v1")


# ── Static file serving for frontend ───────────────────

_FRONTEND_DIR = Path(__file__).resolve().parent.parent

# Serve static assets
app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIR / "assets")), name="assets")
app.mount("/js", StaticFiles(directory=str(_FRONTEND_DIR / "js")), name="js")


# Serve HTML pages
@app.get("/")
@app.get("/index.html")
async def serve_index():
    return FileResponse(str(_FRONTEND_DIR / "pages" / "index.html"))


@app.get("/review.html")
async def serve_review():
    return FileResponse(str(_FRONTEND_DIR / "pages" / "review.html"))


@app.get("/event.html")
async def serve_event():
    return FileResponse(str(_FRONTEND_DIR / "pages" / "event.html"))


@app.get("/evaluation.html")
async def serve_evaluation():
    return FileResponse(str(_FRONTEND_DIR / "pages" / "evaluation.html"))

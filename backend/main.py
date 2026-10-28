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

from config import Settings, settings
from engine.pipeline import Pipeline
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from storage.store import Store

# ── Logging ────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-5s  %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("contentguard")


def make_lifespan(store: Store, pipeline: Pipeline, app_settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Startup: load model, connect DB. Shutdown: close DB."""
        await store.connect()
        await pipeline.startup()
        app.state.pipeline = pipeline
        app.state.store = store
        app.state.settings = app_settings
        logger.info(
            "ContentGuard ready  ·  policy %s  ·  model %s  ·  db %s",
            pipeline.policy_version, pipeline.model_version, app_settings.db_path,
        )
        yield
        await store.close()
        logger.info("ContentGuard shut down.")
    return lifespan


def create_app(
    settings_override: Settings | None = None,
    store_override: Store | None = None,
    pipeline_override: Pipeline | None = None,
) -> FastAPI:
    """Factory function to build and configure the FastAPI application."""
    s = settings_override or settings
    store = store_override or Store(s.db_path)
    pipeline = pipeline_override or Pipeline(s)

    app = FastAPI(
        title="ContentGuard",
        version="1.0.0",
        docs_url="/docs",
        lifespan=make_lifespan(store, pipeline, s),
    )

    # Attach to app.state immediately for test environments
    app.state.pipeline = pipeline
    app.state.store = store
    app.state.settings = s

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoints
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/ready")
    async def ready(request: Request):
        p = getattr(request.app.state, "pipeline", None)
        st = getattr(request.app.state, "store", None)
        is_ready = bool(p and st and st._db is not None)
        status_code = 200 if is_ready else 503
        return JSONResponse(
            status_code=status_code,
            content={"status": "ready" if is_ready else "not_ready"},
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

    from routes.evaluation import router as evaluation_router
    from routes.moderate import router as moderate_router
    from routes.moderations import router as moderations_router
    from routes.reviews import router as reviews_router

    app.include_router(moderate_router, prefix="/v1")
    app.include_router(moderations_router, prefix="/v1")
    app.include_router(reviews_router, prefix="/v1")
    app.include_router(evaluation_router, prefix="/v1")

    # ── Static file serving for frontend ───────────────────

    _frontend_dir = Path(__file__).resolve().parent.parent

    # Serve static assets if directory exists
    assets_path = _frontend_dir / "assets"
    js_path = _frontend_dir / "js"
    pages_path = _frontend_dir / "pages"

    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")

    # Serve HTML pages
    if pages_path.exists():
        @app.get("/")
        @app.get("/index.html")
        async def serve_index():
            return FileResponse(str(pages_path / "index.html"))

        @app.get("/review.html")
        async def serve_review():
            return FileResponse(str(pages_path / "review.html"))

        @app.get("/event.html")
        async def serve_event():
            return FileResponse(str(pages_path / "event.html"))

        @app.get("/evaluation.html")
        async def serve_evaluation():
            return FileResponse(str(pages_path / "evaluation.html"))

    return app


app = create_app()

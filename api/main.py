"""
FastAPI application for the Manufacturing Investigation Copilot.
Exposes the same Python pipeline as a REST API for Power Apps integration.

Run with:
    uv run uvicorn api.main:app --reload --port 8000

OpenAPI spec at: http://localhost:8000/openapi.json
Swagger UI at:   http://localhost:8000/docs
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import investigate, extract, config, health
from api.engine_adapter import init_rag_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up RAG pipeline at startup."""
    logger.info("Warming up RAG pipeline...")
    cases, collection = init_rag_pipeline()
    if cases is not None:
        logger.info("RAG pipeline ready: %d cases loaded", len(cases))
    else:
        logger.warning("RAG pipeline failed to initialize")
    yield


app = FastAPI(
    title="Manufacturing Investigation Copilot API",
    version="1.0.0",
    description=(
        "REST API for the AI-Guided Manufacturing Investigation Copilot. "
        "Provides investigation analysis, NLP field extraction, and configuration "
        "endpoints for Power Apps integration."
    ),
    lifespan=lifespan,
)

# CORS middleware for Power Apps and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.powerapps.com",
        "https://*.powerautomate.com",
        "http://localhost:3000",
        "http://localhost:8501",  # Streamlit
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(investigate.router, prefix="/api/v1", tags=["investigate"])
app.include_router(extract.router, prefix="/api/v1", tags=["extract"])
app.include_router(config.router, prefix="/api/v1", tags=["config"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

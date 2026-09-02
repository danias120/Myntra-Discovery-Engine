"""
Phase 5.5: FastAPI Backend Application

Exposes RAG Assistant, Themes Taxonomy, 2x2 Opportunity Priority Matrix,
Segmented Cuts, Grounded Research Reports, and Automated Cloud Initialization.
"""

from __future__ import annotations

import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.query import router as query_router
from api.routes.analytics import router as analytics_router
from src.rag.vector_store import vector_store
from src.utils.logger import get_logger

logger = get_logger("fastapi_app")

FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

app = FastAPI(
    title="Myntra Wishlist Discovery & Opportunity Engine API",
    description="Grounded Qualitative RAG Assistant and Product Opportunity Quantification Engine for Myntra UX Research",
    version="1.0.0",
)

# CORS Configuration for Localhost, Vercel, and Custom Domains
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]
if FRONTEND_URL and FRONTEND_URL != "*":
    origins.append(FRONTEND_URL.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if FRONTEND_URL == "*" else origins,
    allow_origin_regex=r"https://.*\.vercel\.app" if FRONTEND_URL != "*" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(query_router)
app.include_router(analytics_router)


@app.on_event("startup")
async def startup_event():
    """
    Automated Cloud Startup: Verifies vector index existence.
    If running on a fresh container (e.g. Railway deploy) where ChromaDB is unindexed,
    automatically orchestrates vector index creation from clean corpus chunks.
    """
    logger.info("Initializing Myntra Discovery Engine backend on startup...")
    stats = vector_store.get_stats()
    corpus_count = stats.get("corpus_collection_count", 0)
    logger.info(f"Current ChromaDB status: {corpus_count} corpus chunks, {stats.get('themes_collection_count', 0)} themes.")

    if corpus_count == 0:
        logger.info("ChromaDB collection is unindexed. Automatically building RAG vector index from clean corpus...")
        try:
            from src.rag.runner import build_rag_index
            build_res = build_rag_index()
            logger.info(f"Auto-indexing successful on container startup: {build_res}")
        except Exception as err:
            logger.error(f"Auto-indexing encountered an error: {err}")


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestrators and monitoring."""
    stats = vector_store.get_stats()
    return {
        "status": "healthy",
        "service": "myntra-discovery-engine",
        "timestamp": time.time(),
        "vector_store": stats,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Myntra Wishlist Discovery & Opportunity Engine API is active.",
        "docs": "/docs",
        "health": "/api/health",
    }

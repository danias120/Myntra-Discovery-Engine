"""
Phase 5.5: FastAPI Backend Application

Exposes RAG Assistant, Themes Taxonomy, 2x2 Opportunity Priority Matrix,
Segmented Cuts, and Grounded Research Reports.
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

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app = FastAPI(
    title="Myntra Wishlist Discovery & Opportunity Engine API",
    description="Grounded Qualitative RAG Assistant and Product Opportunity Quantification Engine for Myntra UX Research",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(query_router)
app.include_router(analytics_router)


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

"""
FastAPI Backend Routes: Query & RAG Assistant
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.rag.generator import answer_generator
from src.rag.retriever import retriever

router = APIRouter(tags=["RAG & Query"])


class QueryRequest(BaseModel):
    query: str = Field(..., description="User search or conversational research question")
    stream: bool = Field(False, description="Enable SSE streaming token deltas")
    scope: Optional[str] = Field("both", description="'corpus', 'themes', or 'both'")
    filter_platform: Optional[str] = Field(None, description="Optional platform filter (e.g. reddit, quora)")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Recent conversation history")


@router.post("/api/query")
async def query_rag(req: QueryRequest):
    """
    Accepts user query, retrieves grounded customer evidence, and returns a verified cited answer.
    """
    filter_dict = None
    if req.filter_platform and req.filter_platform.lower() not in ("all", "all sources"):
        plat = req.filter_platform.lower().strip()
        plat_map = {"google play": "playstore", "app store": "appstore"}
        filter_dict = {"source_platform": plat_map.get(plat, plat)}

    if req.stream:
        return StreamingResponse(
            answer_generator.generate_stream(
                query=req.query,
                conversation_history=req.conversation_history,
                filter_dict=filter_dict,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    result = answer_generator.generate(
        query=req.query,
        conversation_history=req.conversation_history,
        filter_dict=filter_dict,
    )
    return result

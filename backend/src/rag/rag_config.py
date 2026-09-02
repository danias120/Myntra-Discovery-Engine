"""
Phase 5.1b: RAG Configuration Module

Centralized configuration dataclass for:
1. Embedding Model (BAAI/bge-small-en-v1.5, 384 dimensions, batch size 64)
2. Vector Store (ChromaDB persistent storage, collections)
3. Initial Retrieval (Top-K candidates, retrieval scope)
4. Cross-Encoder Reranker (ms-marco-MiniLM-L-6-v2, final top-K selection)
5. Context Window & LLM Generation settings
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CHROMA_CANDIDATE = os.path.join(_BACKEND_DIR, "data", "chroma")
if not os.path.exists(_CHROMA_CANDIDATE):
    if os.path.exists("backend/data/chroma"):
        _CHROMA_CANDIDATE = os.path.abspath("backend/data/chroma")
    elif os.path.exists("data/chroma"):
        _CHROMA_CANDIDATE = os.path.abspath("data/chroma")

_RESOLVED_CHROMA_DIR = _CHROMA_CANDIDATE


@dataclass
class RAGConfig:
    """All retrieval, embedding, reranking, and generation settings in one place."""

    # 1. Embedding Model Settings
    EMBEDDING_MODEL: str = os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    EMBEDDING_DIM: int = 384
    QUERY_PREFIX: str = "Represent this sentence for searching relevant passages: "
    EMBED_BATCH_SIZE: int = 64
    NORMALIZE_EMBEDDINGS: bool = True

    # 2. Vector Store Settings
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", _RESOLVED_CHROMA_DIR)
    CORPUS_COLLECTION_NAME: str = "myntra_corpus_chunks"
    THEMES_COLLECTION_NAME: str = "myntra_theme_summaries"

    # 3. Initial Retrieval Settings
    INITIAL_TOP_K: int = 20          # Candidates retrieved from vector store
    RETRIEVAL_SCOPE: str = "both"    # "corpus", "themes", or "both"
    SIMILARITY_METRIC: str = "cosine" # Cosine distance / inner product

    # 4. Cross-Encoder Reranker Settings
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    RERANKER_ENABLED: bool = True
    FINAL_TOP_K: int = 8             # Snippets sent to LLM prompt

    # 5. Generation Context Window & Guardrails
    MAX_CONTEXT_TOKENS: int = 3000   # Token budget for retrieved context
    TEMPERATURE: float = 0.2
    SYSTEM_ROLE: str = "Senior Qualitative Research Assistant for Myntra Wishlist Analytics"
    STRICT_CITATION_REQUIRED: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serializes configuration to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RAGConfig:
        """Constructs RAGConfig from a dictionary with key validation."""
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


# Default global configuration instance
default_rag_config = RAGConfig()

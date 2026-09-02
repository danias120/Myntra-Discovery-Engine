"""
RAG Package

Provides dense semantic embeddings, vector indexing, cross-encoder reranking,
hybrid retrieval, grounded conversational generation, pipeline orchestration, and evaluation benchmarks.
"""

from src.rag.rag_config import RAGConfig, default_rag_config
from src.rag.embedder import (
    CorpusEmbedder,
    corpus_embedder,
    sanitize_metadata_for_chroma,
)
from src.rag.vector_store import (
    VectorStore,
    vector_store,
)
from src.rag.reranker import (
    Reranker,
    reranker,
)
from src.rag.retriever import (
    Retriever,
    retriever,
)
from src.rag.generator import (
    AnswerGenerator,
    answer_generator,
)
from src.rag.runner import (
    build_rag_index,
    load_corpus,
    load_themes,
    serve_api,
)
from src.rag.evaluator import (
    RetrievalEvaluator,
)

__all__ = [
    "RAGConfig",
    "default_rag_config",
    "CorpusEmbedder",
    "corpus_embedder",
    "sanitize_metadata_for_chroma",
    "VectorStore",
    "vector_store",
    "Reranker",
    "reranker",
    "Retriever",
    "retriever",
    "AnswerGenerator",
    "answer_generator",
    "build_rag_index",
    "load_corpus",
    "load_themes",
    "serve_api",
    "RetrievalEvaluator",
]

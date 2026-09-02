"""
Phase 5.7: RAG Orchestrator Module (runner.py)

Provides end-to-end orchestration for:
1. Loading clean corpus chunks (data/clean/corpus.jsonl) & thematic syntheses (data/clean/themes.json)
2. Building/rebuilding the ChromaDB vector index with BGE-small embeddings (BAAI/bge-small-en-v1.5)
3. Serving the FastAPI local backend application
4. CLI execution for indexing and API server launch

Conforms to Phase 5.7 specifications in Docs/implementation-plan.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from src.rag.embedder import CorpusEmbedder, corpus_embedder
from src.rag.rag_config import default_rag_config, RAGConfig
from src.rag.vector_store import VectorStore, vector_store
from src.utils.logger import get_logger

logger = get_logger("rag_orchestrator")

DEFAULT_CORPUS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "clean", "corpus.jsonl")
DEFAULT_THEMES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "clean", "themes.json")


def load_corpus(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads clean customer evidence records from corpus.jsonl.
    """
    path = file_path or DEFAULT_CORPUS_PATH
    if not os.path.exists(path):
        # Fallback relative path check
        path = os.path.join("data", "clean", "corpus.jsonl")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Clean corpus file not found at: '{path}'")

    corpus: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if line_str:
                try:
                    record = json.loads(line_str)
                    corpus.append(record)
                except json.JSONDecodeError as err:
                    logger.warning(f"Skipping malformed JSON at line {line_num}: {err}")

    logger.info(f"Loaded {len(corpus)} customer evidence chunks from '{path}'.")
    return corpus


def load_themes(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads synthesized theme objects from themes.json.
    """
    path = file_path or DEFAULT_THEMES_PATH
    if not os.path.exists(path):
        path = os.path.join("data", "clean", "themes.json")

    if not os.path.exists(path):
        raise FileNotFoundError(f"Themes synthesis file not found at: '{path}'")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    themes = data.get("primary_themes") or data.get("themes") or []
    if isinstance(themes, dict):
        themes = list(themes.values())

    logger.info(f"Loaded {len(themes)} synthesized research themes from '{path}'.")
    return themes


def build_rag_index(
    config: Optional[RAGConfig] = None,
    corpus_path: Optional[str] = None,
    themes_path: Optional[str] = None,
    batch_size: int = 250,
) -> Dict[str, Any]:
    """
    Builds or rebuilds the ChromaDB vector index with BGE-small embeddings.
    
    Returns:
        dict: {"corpus_chunks_indexed": int, "themes_indexed": int, "elapsed_sec": float, "status": str}
    """
    start_time = time.time()
    cfg = config or default_rag_config
    
    logger.info("=== Phase 5.7: Starting RAG Vector Index Construction ===")
    corpus = load_corpus(corpus_path)
    themes = load_themes(themes_path)

    embedder = CorpusEmbedder(cfg)
    v_store = VectorStore(cfg, embedder=embedder)
    
    counts = v_store.build_index(corpus_chunks=corpus, themes=themes, batch_size=batch_size)
    elapsed = round(time.time() - start_time, 2)

    result = {
        "status": "success",
        "corpus_chunks_indexed": counts.get("corpus_chunks", len(corpus)),
        "themes_indexed": counts.get("themes", len(themes)),
        "embedding_model": cfg.EMBEDDING_MODEL,
        "embedding_dim": cfg.EMBEDDING_DIM,
        "persist_dir": cfg.CHROMA_PERSIST_DIR,
        "elapsed_sec": elapsed,
    }
    logger.info(f"=== RAG Vector Index Build Complete in {elapsed}s: {result} ===")
    return result


def serve_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """
    Launches the FastAPI server for local development and API servicing.
    """
    import uvicorn

    logger.info(f"Launching FastAPI server on http://{host}:{port} (reload={reload})...")
    uvicorn.run("api.main:app", host=host, port=port, reload=reload)


def main():
    """CLI Entry point for RAG runner orchestrator."""
    parser = argparse.ArgumentParser(description="Myntra Discovery Engine - RAG Orchestrator")
    parser.add_argument("--build-index", action="store_true", help="Build/rebuild the ChromaDB vector index")
    parser.add_argument("--serve", action="store_true", help="Launch the FastAPI server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address for FastAPI server")
    parser.add_argument("--port", type="int", default=8000, help="Port for FastAPI server")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload for server")

    args = parser.parse_args()

    if args.build_index:
        res = build_rag_index()
        print(json.dumps(res, indent=2))

    if args.serve:
        serve_api(host=args.host, port=args.port, reload=not args.no_reload)

    if not args.build_index and not args.serve:
        # Default: if run directly without args, show status and summary
        corpus = load_corpus()
        themes = load_themes()
        print(f"RAG Orchestrator Ready:")
        print(f"  • Corpus Chunks Available: {len(corpus)}")
        print(f"  • Themes Available: {len(themes)}")
        print(f"  • Vector Store Persist Dir: {default_rag_config.CHROMA_PERSIST_DIR}")
        print(f"  • Embedding Model: {default_rag_config.EMBEDDING_MODEL}")


if __name__ == "__main__":
    main()

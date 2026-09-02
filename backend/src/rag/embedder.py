"""
Phase 5.1: BGE-small Corpus & Query Embedder

Generates dense 384-dimensional sentence embeddings using BAAI/bge-small-en-v1.5
(or all-MiniLM-L6-v2 fallback) with instruction prefix support for queries and
batch memory management.

Handles Edge Cases: EC-5.01, EC-5.02, EC-5.03, EC-5.04
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from sentence_transformers import SentenceTransformer

from src.rag.rag_config import default_rag_config, RAGConfig
from src.utils.logger import get_logger

logger = get_logger("corpus_embedder")


def sanitize_metadata_for_chroma(meta: Dict[str, Any]) -> Dict[str, Union[str, int, float, bool]]:
    """
    Sanitizes dictionary values to ChromaDB-supported primitive types (str, int, float, bool).
    Converts None, lists, and dicts to strings.
    """
    clean_meta: Dict[str, Union[str, int, float, bool]] = {}
    for k, v in meta.items():
        if v is None:
            clean_meta[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            clean_meta[k] = v
        elif isinstance(v, (list, dict)):
            clean_meta[k] = json.dumps(v, ensure_ascii=False)
        else:
            clean_meta[k] = str(v)
    return clean_meta


class CorpusEmbedder:
    """
    Dense semantic embedder for corpus chunks, themes, and search queries.
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or default_rag_config
        self.model_name = self.config.EMBEDDING_MODEL
        self.query_prefix = self.config.QUERY_PREFIX
        self.batch_size = self.config.EMBED_BATCH_SIZE
        self.normalize = self.config.NORMALIZE_EMBEDDINGS

        logger.info(f"Loading SentenceTransformer embedding model: '{self.model_name}'...")
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            logger.warning(f"Could not load '{self.model_name}': {e}. Falling back to 'all-MiniLM-L6-v2'...")
            self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.model = SentenceTransformer(self.model_name)

        logger.info(f"Embedding model ready: {self.model_name} (Dim: {self.config.EMBEDDING_DIM})")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Encodes a list of raw text strings into dense normalized embedding vectors."""
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=self.normalize,
        )
        return embeddings.tolist()

    def embed_corpus(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        """
        Embeds clean evidence chunks in batches.
        Returns list of (chunk_id, embedding_vector, sanitized_metadata) tuples.
        """
        start_time = time.time()
        logger.info(f"Generating dense embeddings for {len(chunks)} clean corpus chunks...")

        texts = [c.get("text", "").strip() for c in chunks]
        embeddings = self.embed_texts(texts)

        results: List[Tuple[str, List[float], Dict[str, Any]]] = []

        for idx, chunk in enumerate(chunks):
            cid = chunk.get("chunk_id", f"chunk_{idx}")
            vec = embeddings[idx]

            raw_meta = {
                "chunk_id": cid,
                "parent_id": chunk.get("parent_id", cid),
                "source_platform": chunk.get("source_platform", "unknown"),
                "source_url": chunk.get("source_url") or "",
                "timestamp": chunk.get("timestamp") or "",
                "word_count": len(chunk.get("text", "").split()),
                "text_snippet": chunk.get("text", "")[:500],
            }

            # Merge any existing nested metadata
            if isinstance(chunk.get("metadata"), dict):
                for k, v in chunk["metadata"].items():
                    if k not in raw_meta:
                        raw_meta[k] = v

            sanitized_meta = sanitize_metadata_for_chroma(raw_meta)
            results.append((cid, vec, sanitized_meta))

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Corpus embedding complete in {elapsed}s: Generated {len(results)} vectors.")
        return results

    def embed_themes(
        self, themes: List[Dict[str, Any]]
    ) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        """
        Embeds primary themes with their descriptions, sub-themes, and top quotes.
        Returns list of (theme_id, embedding_vector, sanitized_metadata) tuples.
        """
        theme_texts: List[str] = []
        for t in themes:
            tid = t.get("theme_id", "")
            name = t.get("name", "")
            desc = t.get("description", "")
            sub_names = ", ".join([st.get("name", "") for st in t.get("sub_themes", [])])
            combined = f"Theme: {name}\nDescription: {desc}\nKey Areas: {sub_names}"
            theme_texts.append(combined)

        embeddings = self.embed_texts(theme_texts)
        results: List[Tuple[str, List[float], Dict[str, Any]]] = []

        for idx, t in enumerate(themes):
            tid = t.get("theme_id", f"T-{idx+1:02d}")
            vec = embeddings[idx]

            raw_meta = {
                "theme_id": tid,
                "theme_name": t.get("name", ""),
                "description": t.get("description", "")[:500],
                "opportunity_score": float(t.get("opportunity_score", 75.0)),
                "rank": int(t.get("rank", idx + 1)),
                "sub_themes_count": len(t.get("sub_themes", [])),
                "total_evidence_count": int(t.get("total_evidence_count", 0)),
            }
            sanitized_meta = sanitize_metadata_for_chroma(raw_meta)
            results.append((tid, vec, sanitized_meta))

        return results

    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a user search query.
        Prepends BGE instruction prefix if configured (EC-5.02).
        """
        if not query:
            return [0.0] * self.config.EMBEDDING_DIM

        prefixed_query = f"{self.query_prefix}{query.strip()}" if self.query_prefix else query.strip()
        vec = self.embed_texts([prefixed_query])[0]
        return vec


# Global singleton instance
corpus_embedder = CorpusEmbedder()

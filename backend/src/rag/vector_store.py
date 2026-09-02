"""
Phase 5.2: ChromaDB Vector Store Module

Provides persistent vector indexing and similarity search for:
1. 'myntra_corpus_chunks' collection (2,065 clean customer evidence chunks)
2. 'myntra_theme_summaries' collection (8 primary research themes)

Handles Edge Cases: EC-5.04, EC-5.05, EC-5.06
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import chromadb
from chromadb.config import Settings

from src.rag.embedder import corpus_embedder, CorpusEmbedder, sanitize_metadata_for_chroma
from src.rag.rag_config import default_rag_config, RAGConfig
from src.utils.logger import get_logger

logger = get_logger("vector_store")


class VectorStore:
    """
    Persistent ChromaDB vector index manager for customer evidence chunks and thematic summaries.
    """

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        embedder: Optional[CorpusEmbedder] = None,
    ):
        self.config = config or default_rag_config
        self.embedder = embedder or corpus_embedder
        self.persist_dir = self.config.CHROMA_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)

        logger.info(f"Initializing Persistent ChromaDB client at: '{self.persist_dir}'...")
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # Get or create collections with cosine distance
        self.corpus_col = self.client.get_or_create_collection(
            name=self.config.CORPUS_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self.themes_col = self.client.get_or_create_collection(
            name=self.config.THEMES_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB Collections Ready: '{self.config.CORPUS_COLLECTION_NAME}' ({self.corpus_col.count()} items), "
            f"'{self.config.THEMES_COLLECTION_NAME}' ({self.themes_col.count()} items)."
        )

    def build_index(
        self,
        corpus_chunks: List[Dict[str, Any]],
        themes: List[Dict[str, Any]],
        batch_size: int = 250,
    ) -> Dict[str, int]:
        """
        Generates dense embeddings and upserts corpus chunks and themes into persistent collections.
        """
        start_time = time.time()
        logger.info(
            f"=== Building ChromaDB Index for {len(corpus_chunks)} Corpus Chunks & {len(themes)} Themes ==="
        )

        # 1. Index Corpus Chunks
        if corpus_chunks:
            logger.info("Generating corpus embeddings...")
            embedded_corpus = self.embedder.embed_corpus(corpus_chunks)

            total_chunks = len(embedded_corpus)
            logger.info(f"Upserting {total_chunks} chunks into '{self.config.CORPUS_COLLECTION_NAME}' in batches of {batch_size}...")

            for b_idx in range(0, total_chunks, batch_size):
                b_slice = embedded_corpus[b_idx : b_idx + batch_size]
                b_ids = [item[0] for item in b_slice]
                b_vecs = [item[1] for item in b_slice]
                b_metas = [item[2] for item in b_slice]
                # Corresponding original chunk texts
                b_docs = [corpus_chunks[b_idx + i].get("text", "") for i in range(len(b_slice))]

                self.corpus_col.upsert(
                    ids=b_ids,
                    embeddings=b_vecs,
                    metadatas=b_metas,
                    documents=b_docs,
                )

        # 2. Index Primary Themes
        if themes:
            logger.info("Generating theme embeddings...")
            embedded_themes = self.embedder.embed_themes(themes)

            t_ids = [item[0] for item in embedded_themes]
            t_vecs = [item[1] for item in embedded_themes]
            t_metas = [item[2] for item in embedded_themes]
            t_docs = [
                f"Theme: {themes[i].get('name')}\nDescription: {themes[i].get('description')}"
                for i in range(len(embedded_themes))
            ]

            self.themes_col.upsert(
                ids=t_ids,
                embeddings=t_vecs,
                metadatas=t_metas,
                documents=t_docs,
            )

        elapsed = round(time.time() - start_time, 2)
        counts = {
            "corpus_chunks_indexed": self.corpus_col.count(),
            "theme_summaries_indexed": self.themes_col.count(),
            "indexing_time_sec": elapsed,
        }
        logger.info(
            f"=== Indexing Complete in {elapsed}s: "
            f"{counts['corpus_chunks_indexed']} chunks, {counts['theme_summaries_indexed']} themes in ChromaDB ==="
        )
        return counts

    def search_corpus(
        self,
        query: Union[str, List[float]],
        top_k: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Searches 'myntra_corpus_chunks' collection for top-K semantically similar evidence chunks.
        """
        k = top_k or self.config.INITIAL_TOP_K
        if isinstance(query, str):
            query_vec = self.embedder.embed_query(query)
        else:
            query_vec = query

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vec],
            "n_results": min(k, max(1, self.corpus_col.count())),
            "include": ["documents", "metadatas", "distances"],
        }
        if filter_dict:
            kwargs["where"] = filter_dict

        results = self.corpus_col.query(**kwargs)
        matched_items: List[Dict[str, Any]] = []

        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else [""] * len(ids)
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

            for i in range(len(ids)):
                # Convert cosine distance (0 to 2) to cosine similarity (1 - dist)
                dist = distances[i]
                sim_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

                matched_items.append({
                    "chunk_id": ids[i],
                    "text": docs[i],
                    "score": round(sim_score, 4),
                    "distance": round(dist, 4),
                    "source_platform": metas[i].get("source_platform", "unknown"),
                    "source_url": metas[i].get("source_url", ""),
                    "timestamp": metas[i].get("timestamp", ""),
                    "metadata": metas[i],
                })

        return matched_items

    def search_themes(
        self,
        query: Union[str, List[float]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Searches 'myntra_theme_summaries' collection for top-K relevant research themes.
        """
        if isinstance(query, str):
            query_vec = self.embedder.embed_query(query)
        else:
            query_vec = query

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vec],
            "n_results": min(top_k, max(1, self.themes_col.count())),
            "include": ["documents", "metadatas", "distances"],
        }

        results = self.themes_col.query(**kwargs)
        matched_themes: List[Dict[str, Any]] = []

        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else [""] * len(ids)
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

            for i in range(len(ids)):
                dist = distances[i]
                sim_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

                matched_themes.append({
                    "theme_id": ids[i],
                    "theme_name": metas[i].get("theme_name", ids[i]),
                    "description": docs[i],
                    "score": round(sim_score, 4),
                    "opportunity_score": metas[i].get("opportunity_score", 75.0),
                    "rank": metas[i].get("rank", i + 1),
                    "metadata": metas[i],
                })

        return matched_themes

    def get_stats(self) -> Dict[str, Any]:
        """Returns collection counts and storage location."""
        return {
            "persist_dir": self.persist_dir,
            "corpus_collection_count": self.corpus_col.count(),
            "themes_collection_count": self.themes_col.count(),
        }


# Global singleton instance
vector_store = VectorStore()

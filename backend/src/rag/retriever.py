"""
Phase 5.4: Retriever Module (Retrieve -> Rerank -> Top-K Context Selection)

Full retrieval pipeline orchestrating:
1. Instruction-aware query embedding via BGE-small
2. Initial candidate retrieval (Top 20) from ChromaDB (corpus chunks & theme summaries)
3. Deep semantic cross-encoder re-ranking via ms-marco-MiniLM-L-6-v2
4. Top-K selection (Top 5-8) with token budget constraint and citation formatting

Handles Edge Cases: EC-5.07, EC-5.08, EC-5.09, EC-5.10
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from src.rag.embedder import corpus_embedder as global_embedder, CorpusEmbedder
from src.rag.rag_config import default_rag_config, RAGConfig
from src.rag.reranker import reranker as global_reranker, Reranker
from src.rag.vector_store import vector_store as global_vector_store, VectorStore
from src.utils.logger import get_logger

logger = get_logger("retriever")


class Retriever:
    """
    Two-stage Hybrid Semantic Retriever with Cross-Encoder Reranking and Grounded Context Assembly.
    """

    def __init__(
        self,
        embedder: Optional[CorpusEmbedder] = None,
        vector_store: Optional[VectorStore] = None,
        reranker: Optional[Reranker] = None,
        config: Optional[RAGConfig] = None,
    ):
        self.config = config or default_rag_config
        self.embedder = embedder or global_embedder
        self.vector_store = vector_store or global_vector_store
        self.reranker = reranker or global_reranker
        self.initial_k = self.config.INITIAL_TOP_K
        self.final_k = self.config.FINAL_TOP_K
        self.default_scope = self.config.RETRIEVAL_SCOPE
        self.max_context_tokens = self.config.MAX_CONTEXT_TOKENS

    def retrieve(
        self,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        scope: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes end-to-end retrieval:
        1. Embeds query with instruction prefix
        2. Retrieves initial candidates from Vector Store
        3. Reranks candidates with Cross-Encoder
        4. Selects top_k and formats with DocID citations
        """
        start_time = time.time()
        active_scope = scope or self.default_scope
        final_limit = top_k or self.final_k

        if not query or not query.strip():
            return []

        # Auto-detect source platform if mentioned in query text (EC-5.07)
        effective_filter = filter_dict
        if not effective_filter:
            q_lower = query.lower()
            if "reddit" in q_lower:
                effective_filter = {"source_platform": "reddit"}
            elif "quora" in q_lower:
                effective_filter = {"source_platform": "quora"}
            elif "app store" in q_lower or "appstore" in q_lower:
                effective_filter = {"source_platform": "appstore"}
            elif "google play" in q_lower or "playstore" in q_lower or "play store" in q_lower:
                effective_filter = {"source_platform": "playstore"}
            elif "survey" in q_lower:
                effective_filter = {"source_platform": "survey"}
            elif "interview" in q_lower:
                effective_filter = {"source_platform": "interview"}

        # 1. Embed Query
        query_vec = self.embedder.embed_query(query)

        # 2. Stage 1 Retrieval: Vector Store
        candidates: List[Dict[str, Any]] = []

        if active_scope in ("corpus", "both"):
            corpus_hits = self.vector_store.search_corpus(
                query=query_vec,
                top_k=self.initial_k,
                filter_dict=effective_filter,
            )
            for hit in corpus_hits:
                hit["item_type"] = "corpus_chunk"
                candidates.append(hit)

        if active_scope in ("themes", "both"):
            theme_hits = self.vector_store.search_themes(
                query=query_vec,
                top_k=2,
            )
            for hit in theme_hits:
                hit["item_type"] = "theme_summary"
                hit["chunk_id"] = hit.get("theme_id", "T-00")
                hit["text"] = hit.get("description", "")
                candidates.append(hit)

        # Deduplicate candidates by chunk_id/theme_id (EC-5.08)
        seen_ids = set()
        unique_candidates: List[Dict[str, Any]] = []
        for c in candidates:
            cid = c.get("chunk_id")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                unique_candidates.append(c)

        # 3. Stage 2 Retrieval: Cross-Encoder Reranking
        reranked_docs = self.reranker.rerank(
            query=query,
            candidates=unique_candidates,
            top_k=final_limit,
        )

        # 4. Apply Token Budget Constraint (EC-5.10)
        # Approximate 1 token ~= 4 chars
        max_char_budget = self.max_context_tokens * 4
        current_char_count = 0
        budget_constrained_docs: List[Dict[str, Any]] = []

        for doc in reranked_docs:
            doc_text = doc.get("text", "")
            doc_len = len(doc_text)
            if current_char_count + doc_len <= max_char_budget or not budget_constrained_docs:
                budget_constrained_docs.append(doc)
                current_char_count += doc_len
            else:
                break

        elapsed = round(time.time() - start_time, 3)
        logger.info(
            f"Retriever complete in {elapsed}s: Retrieved {len(budget_constrained_docs)} passages for query."
        )
        return budget_constrained_docs

    def format_context_for_llm(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved passages into clear citation-ready Markdown blocks for LLM prompt context.
        """
        if not retrieved_docs:
            return "No relevant customer evidence found in the research corpus."

        blocks: List[str] = []
        for idx, doc in enumerate(retrieved_docs):
            cid = doc.get("chunk_id", f"doc_{idx+1}")
            platform = doc.get("source_platform", "corpus")
            url = doc.get("source_url", "")
            text = doc.get("text", "").strip()
            score = doc.get("rerank_score", doc.get("score", 0.0))

            header = f"[DocID: {cid}] | Source: {platform.upper()}"
            if url:
                header += f" | URL: {url}"

            blocks.append(f"--- Evidence {idx+1} ({header}) ---\n{text}\n")

        return "\n".join(blocks)


# Global singleton instance
retriever = Retriever()

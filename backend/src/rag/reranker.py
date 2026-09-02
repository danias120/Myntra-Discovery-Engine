"""
Phase 5.3: Cross-Encoder Reranker Module

Reranks candidate evidence passages and themes using a deep cross-encoder model
(cross-encoder/ms-marco-MiniLM-L-6-v2) for high-precision semantic relevance.

Handles Edge Cases: EC-5.07, EC-5.08, EC-5.09
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from sentence_transformers import CrossEncoder

from src.rag.rag_config import default_rag_config, RAGConfig
from src.utils.logger import get_logger

logger = get_logger("reranker")


class Reranker:
    """
    High-precision Cross-Encoder for passage re-ranking and semantic relevance scoring.
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or default_rag_config
        self.model_name = self.config.RERANKER_MODEL
        self.enabled = self.config.RERANKER_ENABLED
        self.final_k = self.config.FINAL_TOP_K
        self.model: Optional[CrossEncoder] = None

        if self.enabled:
            logger.info(f"Loading CrossEncoder model: '{self.model_name}'...")
            try:
                self.model = CrossEncoder(self.model_name)
                logger.info(f"CrossEncoder model ready: '{self.model_name}'.")
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder '{self.model_name}': {e}. Falling back to cosine score ranking.")
                self.model = None

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Re-scores and re-orders candidate passages using the cross-encoder.
        Returns top_k most relevant items.
        """
        k = top_k or self.final_k
        if not candidates or not query:
            return candidates[:k]

        if not self.enabled or self.model is None:
            # Fallback: Sort by original vector similarity score
            sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)
            return sorted_candidates[:k]

        start_time = time.time()
        # Build query-passage pairs
        pairs: List[Tuple[str, str]] = []
        for c in candidates:
            passage_text = c.get("text") or c.get("description") or c.get("document", "")
            pairs.append((query.strip(), passage_text.strip()))

        try:
            scores = self.model.predict(pairs)
            for idx, c in enumerate(candidates):
                c_score = float(scores[idx])
                c["rerank_score"] = round(c_score, 4)
                c["original_score"] = c.get("score", 0.0)

            # Sort by cross-encoder score descending
            ranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
            elapsed = round(time.time() - start_time, 3)
            logger.debug(f"Cross-encoder reranked {len(candidates)} candidates down to {min(k, len(ranked))} in {elapsed}s.")
            return ranked[:k]

        except Exception as e:
            logger.error(f"Error during cross-encoder prediction: {e}. Returning original vector ranking.")
            return candidates[:k]


# Global singleton instance
reranker = Reranker()

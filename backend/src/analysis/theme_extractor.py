"""
Pass 1: Micro-Theme Extractor Module

Extracts qualitative micro-themes, friction points, mental models, and decision triggers
from batches of clean text chunks using Gemini LLM with structured JSON output,
SHA-256 response caching, token-bucket rate limiting, and verbatim quote verification.

Handles Edge Cases: EC-3.01, EC-3.05, EC-3.06, EC-3.07, EC-3.08
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from src.analysis.prompts import (
    BATCH_THEME_EXTRACTION_SYSTEM_PROMPT,
    BatchExtractionOutput,
    ThemeEvidenceItem,
    format_batch_extraction_prompt,
    verify_quote_verbatim,
)
from src.utils.logger import get_logger
from src.utils.llm_client import default_llm_client, LLMClient

logger = get_logger("theme_extractor")


def clean_json_response(text: str) -> str:
    """Strips markdown backticks and extracts pure JSON payload (EC-3.06)."""
    if not text:
        return ""
    text = text.strip()
    # Remove markdown ```json ... ``` wrapper if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


class ThemeExtractor:
    """
    Orchestrates batch-level qualitative evidence extraction using Gemini LLM.
    """

    def __init__(self, batch_size: int = 20, llm_client: Optional[LLMClient] = None):
        self.batch_size = batch_size
        self.llm_client = llm_client or default_llm_client
        self.stats = {
            "total_chunks_processed": 0,
            "total_batches_executed": 0,
            "total_evidence_items_extracted": 0,
            "hallucinated_quotes_dropped": 0,
            "cache_hits": 0,
            "category_distribution": {},
            "sentiment_distribution": {},
        }

    def process_batch(
        self, batch_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Processes a single batch of 15-25 chunks through LLM theme extraction.
        Verifies verbatim quotes against source chunks.
        """
        if not batch_chunks:
            return []

        chunk_lookup = {c["chunk_id"]: c for c in batch_chunks if "chunk_id" in c}
        prompt = format_batch_extraction_prompt(batch_chunks)

        response_text = self.llm_client.generate(
            prompt=prompt,
            system_prompt=BATCH_THEME_EXTRACTION_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.1,
            use_cache=True,
        )

        cleaned_json = clean_json_response(response_text)
        if not cleaned_json:
            logger.warning("Empty response from LLM for batch extraction.")
            return []

        # Parse JSON
        raw_items: List[Dict[str, Any]] = []
        try:
            parsed = json.loads(cleaned_json)
            if isinstance(parsed, dict) and "evidence_items" in parsed:
                raw_items = parsed["evidence_items"]
            elif isinstance(parsed, list):
                raw_items = parsed
            elif isinstance(parsed, dict):
                # Try finding any list value in the dict
                for v in parsed.values():
                    if isinstance(v, list):
                        raw_items = v
                        break
        except Exception as e:
            logger.error(f"JSON parsing error in batch theme extraction: {e}. Raw text snippet: {cleaned_json[:200]}")
            return []

        valid_evidence: List[Dict[str, Any]] = []

        for raw_item in raw_items:
            try:
                item = ThemeEvidenceItem(**raw_item)
            except Exception as e:
                logger.debug(f"Pydantic validation failed for item {raw_item}: {e}")
                continue

            # Verify chunk ID exists in current batch
            cid = item.source_chunk_id
            if cid not in chunk_lookup:
                # Try matching by fallback
                continue

            source_chunk = chunk_lookup[cid]
            source_text = source_chunk.get("text", "")

            # Verbatim Quote Verification (EC-3.01)
            is_verbatim = verify_quote_verbatim(item.verbatim_quote, source_text)
            if not is_verbatim:
                self.stats["hallucinated_quotes_dropped"] += 1
                logger.debug(f"Dropped hallucinated quote: '{item.verbatim_quote}' (Not in chunk {cid})")
                continue

            # Build enriched evidence dict
            evidence_dict = item.model_dump()
            evidence_dict["source_platform"] = source_chunk.get("source_platform", "unknown")
            evidence_dict["source_url"] = source_chunk.get("source_url")
            evidence_dict["timestamp"] = source_chunk.get("timestamp")
            evidence_dict["parent_id"] = source_chunk.get("parent_id", cid)

            # Update stats
            cat = evidence_dict["category"]
            sent = evidence_dict["sentiment"]
            self.stats["category_distribution"][cat] = self.stats["category_distribution"].get(cat, 0) + 1
            self.stats["sentiment_distribution"][sent] = self.stats["sentiment_distribution"].get(sent, 0) + 1

            valid_evidence.append(evidence_dict)

        return valid_evidence

    def extract_from_chunks(
        self,
        chunks: List[Dict[str, Any]],
        output_file: Optional[str] = "data/clean/extracted_evidence.jsonl",
    ) -> List[Dict[str, Any]]:
        """
        Executes Pass 1 micro-theme extraction across all clean chunks in batches.
        Writes extracted evidence items to output_file.
        """
        start_time = time.time()
        self.stats["total_chunks_processed"] = len(chunks)
        total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
        logger.info(f"Starting Pass 1 Micro-Theme Extraction on {len(chunks)} chunks across {total_batches} batches...")

        all_evidence: List[Dict[str, Any]] = []

        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            # Clear previous output file if starting fresh
            open(output_file, "w", encoding="utf-8").close()

        for batch_idx in range(total_batches):
            start_i = batch_idx * self.batch_size
            end_i = min(len(chunks), start_i + self.batch_size)
            batch_slice = chunks[start_i:end_i]

            logger.info(f"Processing Batch {batch_idx + 1}/{total_batches} ({len(batch_slice)} chunks)...")
            batch_evidence = self.process_batch(batch_slice)
            self.stats["total_batches_executed"] += 1
            self.stats["total_evidence_items_extracted"] += len(batch_evidence)
            all_evidence.extend(batch_evidence)

            # Stream save to output_file
            if output_file and batch_evidence:
                with open(output_file, "a", encoding="utf-8") as f:
                    for ev in batch_evidence:
                        f.write(json.dumps(ev, ensure_ascii=False) + "\n")

        elapsed = round(time.time() - start_time, 2)
        logger.info(
            f"Pass 1 Completed in {elapsed}s: Extracted {len(all_evidence)} valid qualitative evidence items "
            f"({self.stats['hallucinated_quotes_dropped']} hallucinated quotes dropped)."
        )
        return all_evidence

    def get_stats(self) -> Dict[str, Any]:
        """Returns extraction statistics."""
        return self.stats


# Global singleton instance
theme_extractor = ThemeExtractor()

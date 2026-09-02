"""
Cleaning Pipeline Runner

Orchestrates the end-to-end 5-stage cleaning and normalization pipeline:
Raw Record -> PII Stripper -> Spam Filter -> Relevance Filter -> Deduplicator -> Chunker -> Clean Corpus

Generates:
- backend/data/clean/corpus.jsonl
- backend/data/clean/cleaning_log.json
"""

from __future__ import annotations

import glob
import json
import os
import statistics
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.cleaning.chunker import chunker
from src.cleaning.deduplicator import deduplicator
from src.cleaning.pii_stripper import pii_stripper
from src.cleaning.relevance_filter import relevance_filter
from src.cleaning.spam_filter import spam_filter
from src.utils.logger import get_logger

logger = get_logger("cleaning_runner")


def run_cleaning_pipeline(
    raw_dir: str = "data/raw",
    output_dir: str = "data/clean",
) -> Dict[str, Any]:
    """
    Executes the 5-step deterministic text cleaning pipeline across all raw data sources.
    """
    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)
    clean_corpus_path = os.path.join(output_dir, "corpus.jsonl")
    cleaning_log_path = os.path.join(output_dir, "cleaning_log.json")

    logger.info("=== Starting Phase 2: Cleaning & Normalization Pipeline ===")

    # 1. Load all raw files
    raw_files = sorted([f for f in glob.glob(os.path.join(raw_dir, "*.jsonl")) if not f.endswith(".gitkeep")])
    raw_records: List[Dict[str, Any]] = []
    input_platform_counts: Dict[str, int] = {}

    for fpath in raw_files:
        p_name = os.path.basename(fpath).replace(".jsonl", "")
        p_count = 0
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    raw_records.append(rec)
                    p_count += 1
                except Exception as e:
                    logger.warning(f"Error reading line in {fpath}: {e}")
        input_platform_counts[p_name] = p_count

    total_input = len(raw_records)
    logger.info(f"Loaded {total_input} raw evidence records across {len(raw_files)} files.")

    timings: Dict[str, float] = {}

    # Stage 1: PII Stripping
    t0 = time.time()
    logger.info("Step 1/5: Running PII Stripper (Regex + SpaCy NER with Brand Whitelisting)...")
    pii_sanitized_records: List[Dict[str, Any]] = []
    for rec in raw_records:
        clean_rec = pii_stripper.sanitize_record(rec)
        pii_sanitized_records.append(clean_rec)
    timings["pii_stripping_sec"] = round(time.time() - t0, 3)

    # Stage 2: Spam & Boilerplate Filtering
    t0 = time.time()
    logger.info("Step 2/5: Running Spam & Boilerplate Filter...")
    spam_passed_records: List[Dict[str, Any]] = []
    for rec in pii_sanitized_records:
        processed = spam_filter.process_record(rec)
        if processed is not None:
            spam_passed_records.append(processed)
    timings["spam_filtering_sec"] = round(time.time() - t0, 3)

    # Stage 3: 2-Tier Relevance Filter
    t0 = time.time()
    logger.info("Step 3/5: Running 2-Tier Relevance Filter (Fashion Wishlist & Shopping Behavior)...")
    relevance_passed_records: List[Dict[str, Any]] = []
    for rec in spam_passed_records:
        processed = relevance_filter.process_record(rec)
        if processed is not None:
            relevance_passed_records.append(processed)
    timings["relevance_filtering_sec"] = round(time.time() - t0, 3)

    # Stage 4: Two-Tier Deduplication (Exact SHA-256 + MinHash LSH)
    t0 = time.time()
    logger.info("Step 4/5: Running Two-Tier Deduplicator (Exact + MinHash LSH J>=0.85)...")
    deduped_records = deduplicator.deduplicate_records(relevance_passed_records)
    timings["deduplication_sec"] = round(time.time() - t0, 3)

    # Stage 5: Semantic Chunker
    t0 = time.time()
    logger.info("Step 5/5: Running Semantic Sentence-Boundary Chunker...")
    clean_chunks: List[Dict[str, Any]] = []
    output_platform_counts: Dict[str, int] = {}

    for rec in deduped_records:
        chunks = chunker.chunk_record(rec)
        for c in chunks:
            clean_chunks.append(c)
            p = c.get("source_platform", "unknown")
            output_platform_counts[p] = output_platform_counts.get(p, 0) + 1
    timings["chunking_sec"] = round(time.time() - t0, 3)

    # Write clean corpus
    with open(clean_corpus_path, "w", encoding="utf-8") as f:
        for c in clean_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    total_execution_time = round(time.time() - start_time, 3)
    timings["total_pipeline_sec"] = total_execution_time

    # Calculate word distribution statistics
    word_counts = [c.get("word_count", len(c.get("text", "").split())) for c in clean_chunks]
    char_counts = [c.get("char_count", len(c.get("text", ""))) for c in clean_chunks]

    word_stats = {
        "min": min(word_counts) if word_counts else 0,
        "max": max(word_counts) if word_counts else 0,
        "mean": round(statistics.mean(word_counts), 2) if word_counts else 0,
        "median": statistics.median(word_counts) if word_counts else 0,
        "p95": statistics.quantiles(word_counts, n=20)[18] if len(word_counts) >= 20 else (max(word_counts) if word_counts else 0),
    }

    # Compile comprehensive cleaning log
    cleaning_log = {
        "pipeline_run_timestamp": datetime.now(timezone.utc).isoformat(),
        "execution_time_sec": total_execution_time,
        "timings_by_stage_sec": timings,
        "input_summary": {
            "total_raw_records": total_input,
            "platform_breakdown": input_platform_counts,
        },
        "stage_statistics": {
            "pii_stripper": {
                "records_processed": len(pii_sanitized_records),
                "pii_redacted": True,
            },
            "spam_filter": spam_filter.get_stats(),
            "relevance_filter": relevance_filter.get_stats(),
            "deduplicator": deduplicator.get_stats(),
            "chunker": chunker.get_stats(),
        },
        "output_summary": {
            "total_clean_chunks": len(clean_chunks),
            "output_platform_breakdown": output_platform_counts,
            "word_count_distribution": word_stats,
            "clean_corpus_path": clean_corpus_path,
        },
    }

    with open(cleaning_log_path, "w", encoding="utf-8") as f:
        json.dump(cleaning_log, f, indent=2, ensure_ascii=False)

    logger.info(
        f"=== Phase 2 Completed: {total_input} raw records -> {len(clean_chunks)} clean chunks in {total_execution_time}s ==="
    )
    return cleaning_log


if __name__ == "__main__":
    run_cleaning_pipeline()

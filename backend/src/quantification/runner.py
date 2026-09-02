"""
Phase 4: Quantification Pipeline Orchestrator

Executes end-to-end Opportunity Quantification:
1. OpportunityScorer -> data/clean/opportunity_scores.json
2. SegmentSlicer -> data/clean/segmented_opportunities.json
3. MatrixGenerator -> data/clean/opportunity_matrix.json, reports/opportunity_report.md, reports/segment_view.md
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict

from src.quantification.scorer import opportunity_scorer
from src.quantification.segment_slicer import segment_slicer
from src.quantification.matrix_generator import matrix_generator
from src.utils.logger import get_logger

logger = get_logger("quantification_runner")

THEMES_FILE = "data/clean/themes.json"
CORPUS_FILE = "data/clean/corpus.jsonl"
QUANT_LOG_FILE = "data/clean/quantification_log.json"


def run_quantification() -> Dict[str, Any]:
    """Runs full Opportunity Quantification & Prioritization pipeline."""
    start_time = time.time()
    logger.info("=== Starting Phase 4: Opportunity Quantification & Prioritization ===")

    # 1. Load Themes
    with open(THEMES_FILE, "r", encoding="utf-8") as f:
        themes_data = json.load(f)
    themes = themes_data.get("primary_themes", [])
    logger.info(f"Loaded {len(themes)} primary themes from {THEMES_FILE}.")

    # 2. Count clean corpus chunks
    total_chunks = sum(1 for line in open(CORPUS_FILE, "r", encoding="utf-8") if line.strip())

    # Step 1: Scorer
    logger.info("Step 1/3: Scoring and ranking opportunities...")
    scores_data = opportunity_scorer.score_all(themes=themes, total_chunks=total_chunks)
    scored_themes = scores_data.get("ranked_opportunities", [])

    # Step 2: Segment Slicer
    logger.info("Step 2/3: Slicing opportunities across categories, price bands, and occasions...")
    seg_data = segment_slicer.slice_all(themes=themes)
    segmented_themes = seg_data.get("segmented_opportunities", [])

    # Step 3: Matrix Generator & Executive Reports
    logger.info("Step 3/3: Generating 2x2 Priority Matrix and Executive Reports...")
    matrix_data = matrix_generator.generate(
        scored_themes=scored_themes,
        segmented_themes=segmented_themes,
        themes_raw=themes,
    )

    elapsed = round(time.time() - start_time, 2)
    log_payload = {
        "execution_timestamp": time.time(),
        "total_execution_time_sec": elapsed,
        "total_themes_quantified": len(scored_themes),
        "top_ranked_opportunity": scored_themes[0]["theme_name"] if scored_themes else "",
        "top_opportunity_score": scored_themes[0]["opportunity_score"] if scored_themes else 0.0,
        "quadrant_distribution": matrix_data.get("quadrant_distribution", {}),
        "output_files": [
            "data/clean/opportunity_scores.json",
            "data/clean/segmented_opportunities.json",
            "data/clean/opportunity_matrix.json",
            "reports/opportunity_report.md",
            "reports/segment_view.md",
        ],
    }

    with open(QUANT_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log_payload, f, indent=2, ensure_ascii=False)

    logger.info(f"=== Phase 4 Complete in {elapsed}s: All artifacts generated successfully ===")
    return log_payload


if __name__ == "__main__":
    run_quantification()

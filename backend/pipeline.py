#!/usr/bin/env python3
"""
Discovery Engine Pipeline Orchestrator

Runs the five-stage pipeline for the Myntra Wishlist Discovery Engine:
  1. Data Sourcing & Ingestion (Scrapers + First-party Research Data)
  2. Cleaning & Normalization (PII Stripping, Dedup, Spam Filter, Chunking)
  3. Thematic Analysis Engine (Pass 1 Map + Pass 2 Reduce Macro Themes)
  4. Opportunity Quantification & Prioritization (Scoring, Ranking, Segmentation)
  5. RAG Assistant (Vector Store Indexing, Server, Benchmark Evaluation)

Usage:
    python pipeline.py --all          # Run stages 1–5a sequentially
    python pipeline.py --ingest       # Stage 1: Data Sourcing & Ingestion
    python pipeline.py --clean        # Stage 2: Cleaning & Normalization
    python pipeline.py --analyze      # Stage 3: Thematic Analysis
    python pipeline.py --quantify     # Stage 4: Opportunity Quantification
    python pipeline.py --rag-build    # Stage 5a: Build RAG vector index
    python pipeline.py --rag-serve    # Stage 5b: Launch FastAPI server
    python pipeline.py --eval         # Run RAG retrieval evaluation benchmark
    python pipeline.py --check-config # Validate environment & active configuration
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Add backend and src to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.utils.config import (
    RAW_DIR,
    CLEAN_DIR,
    THEMES_DIR,
    MATRIX_DIR,
    VECTORSTORE_DIR,
    REPORTS_DIR,
    validate_config,
    get_config_summary,
)
from src.utils.logger import get_logger

logger = get_logger("pipeline")


def check_stage_prerequisites(stage: str) -> bool:
    """
    Validates entry criteria before executing a pipeline stage (handles EC-X.01).
    """
    if stage == "clean":
        raw_files = list(RAW_DIR.glob("*.jsonl"))
        if not raw_files:
            logger.error(
                f"Prerequisite failed: Stage 2 (Clean) requires raw data in {RAW_DIR}. Run --ingest first."
            )
            return False

    elif stage == "analyze":
        clean_corpus = CLEAN_DIR / "corpus.jsonl"
        if not clean_corpus.exists() or clean_corpus.stat().st_size == 0:
            logger.error(
                f"Prerequisite failed: Stage 3 (Analyze) requires {clean_corpus}. Run --clean first."
            )
            return False

    elif stage == "quantify":
        themes_file = THEMES_DIR / "themes.jsonl"
        if not themes_file.exists() or themes_file.stat().st_size == 0:
            logger.error(
                f"Prerequisite failed: Stage 4 (Quantify) requires {themes_file}. Run --analyze first."
            )
            return False

    elif stage == "rag-build":
        clean_corpus = CLEAN_DIR / "corpus.jsonl"
        themes_file = THEMES_DIR / "themes.jsonl"
        if not clean_corpus.exists() or not themes_file.exists():
            logger.error(
                f"Prerequisite failed: Stage 5a (RAG Build) requires both {clean_corpus} and {themes_file}."
            )
            return False

    return True


# === Stage Execution Handlers ===

def run_ingestion() -> dict:
    """Stage 1: Ingestion & Sourcing."""
    logger.info("Starting Stage 1: Data Sourcing & Ingestion...")
    try:
        from src.ingestion.runner import run_ingestion as execute_ingestion
        return execute_ingestion()
    except ImportError:
        logger.warning("Stage 1 runner (src.ingestion.runner) not yet implemented.")
        return {"status": "pending_implementation", "stage": "ingestion"}


def run_cleaning() -> dict:
    """Stage 2: Cleaning, PII removal, deduplication, chunking."""
    logger.info("Starting Stage 2: Cleaning & Normalization...")
    try:
        from src.cleaning.runner import run_cleaning as execute_cleaning
        return execute_cleaning()
    except ImportError:
        logger.warning("Stage 2 runner (src.cleaning.runner) not yet implemented.")
        return {"status": "pending_implementation", "stage": "cleaning"}


def run_analysis() -> dict:
    """Stage 3: Map-Reduce Thematic Analysis."""
    logger.info("Starting Stage 3: Thematic Analysis Engine...")
    try:
        from src.analysis.runner import run_analysis as execute_analysis
        return execute_analysis()
    except ImportError:
        logger.warning("Stage 3 runner (src.analysis.runner) not yet implemented.")
        return {"status": "pending_implementation", "stage": "analysis"}


def run_quantification() -> dict:
    """Stage 4: Scoring, Ranking, and Opportunity Matrix."""
    logger.info("Starting Stage 4: Opportunity Quantification...")
    try:
        from src.quantification.runner import run_quantification as execute_quantification
        return execute_quantification()
    except ImportError:
        logger.warning("Stage 4 runner (src.quantification.runner) not yet implemented.")
        return {"status": "pending_implementation", "stage": "quantification"}


def run_rag_build() -> dict:
    """Stage 5a: Vector Store Index Build."""
    logger.info("Starting Stage 5a: Building RAG Vector Index...")
    try:
        from src.rag.embedder import CorpusEmbedder
        from src.rag.vector_store import VectorStore
        from src.rag.rag_config import RAGConfig
        config = RAGConfig()
        vector_store = VectorStore(VECTORSTORE_DIR)
        # return vector_store.build_index(...)
        return {"status": "ready"}
    except ImportError:
        logger.warning("Stage 5a modules (src.rag.*) not yet implemented.")
        return {"status": "pending_implementation", "stage": "rag_build"}


def run_rag_serve():
    """Stage 5b: FastAPI REST API / SSE Server."""
    logger.info("Launching FastAPI server on port 8000...")
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)


def run_eval() -> dict:
    """Stage 5c: Retrieval Benchmark Evaluation."""
    logger.info("Starting Retrieval Benchmark Evaluation...")
    try:
        from src.rag.evaluator import RetrievalEvaluator
        # return evaluator.evaluate()
        return {"status": "ready"}
    except ImportError:
        logger.warning("Evaluation module (src.rag.evaluator) not yet implemented.")
        return {"status": "pending_implementation", "stage": "eval"}


def run_check_config():
    """Prints diagnostic summary of configuration and directory structure."""
    print("\n" + "=" * 60)
    print("  Discovery Engine — Environment Configuration Check")
    print("=" * 60)
    
    validation = validate_config()
    print("\n[Service Configuration Status]")
    for k, v in validation.items():
        status_icon = "✔ Configured" if v else "✖ Not Set (Optional / Check .env)"
        print(f"  • {k:<25}: {status_icon}")
        
    summary = get_config_summary()
    print("\n[Active Configuration Parameters]")
    for k, v in summary.items():
        print(f"  • {k:<25}: {v}")

    print("\n[Directory Paths]")
    paths = [
        ("Raw Data", RAW_DIR),
        ("Clean Corpus", CLEAN_DIR),
        ("Themes", THEMES_DIR),
        ("Matrix", MATRIX_DIR),
        ("Vector Store", VECTORSTORE_DIR),
        ("Reports", REPORTS_DIR),
    ]
    for label, p in paths:
        exists_icon = "✔ Exists" if p.exists() else "✖ Missing"
        print(f"  • {label:<25}: {exists_icon} ({p})")
        
    print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Myntra Wishlist Discovery Engine — Pipeline Orchestrator"
    )
    
    parser.add_argument("--ingest", action="store_true", 
                        help="Stage 1: Data Sourcing & Ingestion")
    parser.add_argument("--clean", action="store_true", 
                        help="Stage 2: Cleaning & Normalization")
    parser.add_argument("--analyze", action="store_true", 
                        help="Stage 3: Thematic Analysis Engine")
    parser.add_argument("--quantify", action="store_true", 
                        help="Stage 4: Opportunity Quantification")
    parser.add_argument("--rag-build", action="store_true", 
                        help="Stage 5a: Build RAG vector index")
    parser.add_argument("--rag-serve", action="store_true", 
                        help="Stage 5b: Launch RAG API server")
    parser.add_argument("--eval", action="store_true", 
                        help="Stage 5c: Run retrieval evaluation benchmark")
    parser.add_argument("--all", action="store_true", 
                        help="Run stages 1–5a sequentially")
    parser.add_argument("--check-config", action="store_true", 
                        help="Diagnose environment variables and directory paths")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)
        
    if args.check_config:
        run_check_config()
        return

    stages: list[tuple[str, str, callable]] = []
    
    if args.all or args.ingest:
        stages.append(("ingest", "Stage 1: Data Sourcing & Ingestion", run_ingestion))
    if args.all or args.clean:
        stages.append(("clean", "Stage 2: Cleaning & Normalization", run_cleaning))
    if args.all or args.analyze:
        stages.append(("analyze", "Stage 3: Thematic Analysis", run_analysis))
    if args.all or args.quantify:
        stages.append(("quantify", "Stage 4: Opportunity Quantification", run_quantification))
    if args.all or args.rag_build:
        stages.append(("rag-build", "Stage 5a: Build RAG Vector Index", run_rag_build))
    if args.eval:
        stages.append(("eval", "Stage 5c: Retrieval Benchmark Evaluation", run_eval))
    if args.rag_serve:
        stages.append(("rag-serve", "Stage 5b: Launch FastAPI Server", run_rag_serve))
    
    start_time = time.time()
    
    for stage_key, stage_label, handler in stages:
        print(f"\n{'='*60}")
        print(f"  {stage_label}")
        print(f"{'='*60}\n")
        
        # Check prerequisites before starting stage
        if not check_stage_prerequisites(stage_key):
            logger.error(f"Stopping pipeline due to prerequisite failure at '{stage_label}'.")
            sys.exit(1)
            
        stage_start = time.time()
        result = handler()
        duration = time.time() - stage_start
        
        if result and isinstance(result, dict) and result.get("status") == "error":
            logger.error(f"❌ {stage_label} failed: {result}")
            sys.exit(1)
            
        print(f"\n✔ {stage_label} completed in {duration:.2f}s | Result: {result}")
    
    total_duration = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  Discovery Engine Pipeline finished in {total_duration:.2f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

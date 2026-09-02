"""
Ingestion Orchestrator Runner

Executes all platform scrapers and first-party research ingesters sequentially,
aggregates statistics, and produces data/raw/ingestion_log.json.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.ingestion.config import (
    QUERY_TERMS,
    RECENCY_MONTHS,
    TARGET_RECORDS_PER_SOURCE,
    get_query_terms_for_platform,
)
from src.ingestion.reddit_scraper import RedditScraper
from src.ingestion.quora_scraper import QuoraScraper
from src.ingestion.appstore_scraper import AppStoreScraper
from src.ingestion.playstore_scraper import PlayStoreScraper
from src.ingestion.youtube_scraper import YouTubeScraper
from src.ingestion.instagram_scraper import InstagramScraper
from src.ingestion.myntra_scraper import MyntraScraper
from src.ingestion.forum_scraper import ForumScraper
from src.ingestion.research_ingester import ResearchIngester
from src.utils.config import RAW_DIR
from src.utils.logger import get_logger

logger = get_logger("ingestion_runner")


def run_ingestion(
    max_records_per_source: int = TARGET_RECORDS_PER_SOURCE,
    recency_months: int = RECENCY_MONTHS,
    output_dir: Path = RAW_DIR,
) -> Dict[str, Any]:
    """
    Orchestrates sequential execution of all scrapers and research loaders.
    """
    start_time = time.time()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scrapers = [
        AppStoreScraper(),
        PlayStoreScraper(),
        RedditScraper(),
        YouTubeScraper(),
        MyntraScraper(),
        InstagramScraper(),
        QuoraScraper(),
        ForumScraper(),
    ]

    stats: Dict[str, Any] = {
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_records_ingested": 0,
        "platform_counts": {},
        "files_generated": [],
        "errors": {},
        "duration_seconds": 0.0,
    }

    logger.info("==================================================")
    logger.info("  Starting Discovery Engine Data Ingestion")
    logger.info("==================================================")

    # 1. Run all web/social scrapers
    for scraper in scrapers:
        platform = scraper.get_source_name()
        query_list = get_query_terms_for_platform(platform)
        scraper.configure(
            query_terms=query_list,
            recency_months=recency_months,
            max_results=max_records_per_source,
        )

        try:
            logger.info(f"Executing scraper: {platform}...")
            file_path = scraper.export(output_dir=output_dir)
            
            # Count records in generated file
            count = 0
            if Path(file_path).exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    count = sum(1 for _ in f)

            stats["platform_counts"][platform] = count
            stats["files_generated"].append(str(file_path))
            stats["total_records_ingested"] += count
            logger.info(f"Completed {platform}: {count} records in {file_path}")

        except Exception as e:
            logger.error(f"Error during ingestion for {platform}: {e}")
            stats["errors"][platform] = str(e)

    # 2. Ingest first-party research data (interviews & surveys)
    try:
        logger.info("Ingesting first-party user research data (interviews & surveys)...")
        research_ingester = ResearchIngester()
        research_files = research_ingester.export(output_dir=output_dir)
        
        for r_type, f_path in research_files.items():
            count = 0
            if Path(f_path).exists():
                with open(f_path, "r", encoding="utf-8") as f:
                    count = sum(1 for _ in f)
            stats["platform_counts"][r_type] = count
            stats["files_generated"].append(str(f_path))
            stats["total_records_ingested"] += count
            logger.info(f"Completed {r_type}: {count} records in {f_path}")

    except Exception as e:
        logger.error(f"Error during research data ingestion: {e}")
        stats["errors"]["first_party_research"] = str(e)

    stats["duration_seconds"] = round(time.time() - start_time, 2)

    # 3. Write summary ingestion log
    log_file = output_dir / "ingestion_log.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info(f"Ingestion log written to {log_file}")
    logger.info(f"Ingestion finished in {stats['duration_seconds']}s | Total records: {stats['total_records_ingested']}")
    return stats


if __name__ == "__main__":
    run_ingestion()

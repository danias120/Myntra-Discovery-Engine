"""
Base Scraper Interface

Defines the abstract interface and common utilities for all platform scrapers:
  - Reddit, Quora, App Store, Play Store, YouTube, Instagram, Myntra Reviews, Fashion Forums
"""

from __future__ import annotations

import json
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from bs4 import BeautifulSoup
from src.utils.config import RAW_DIR
from src.utils.logger import get_logger
from src.utils.rate_limiter import get_limiter

logger = get_logger("base_scraper")

# Forbidden PII keys that must NEVER exist in raw records
FORBIDDEN_PII_KEYS = {
    "username",
    "author",
    "email",
    "device_id",
    "account_id",
    "user_id",
    "user",
    "reviewer_name",
    "commenter_name",
    "channel_title",
}


def sanitize_text(text: Optional[str]) -> str:
    """
    Cleans raw HTML/markdown markup, strips leading/trailing whitespaces,
    and returns sanitized plain text. (Handles EC-1.16)
    """
    if not text:
        return ""

    # Strip HTML tags if present
    if "<" in text and ">" in text:
        try:
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text(separator=" ")
        except Exception:
            text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate_raw_record(record: Dict[str, Any]) -> bool:
    """
    Validates a record against the raw data schema and ensures zero PII fields.
    """
    required_fields = [
        "record_id",
        "source_platform",
        "text",
        "ingestion_timestamp",
        "source_type",
        "metadata",
    ]

    for field in required_fields:
        if field not in record:
            logger.warning(f"Record missing required field: {field}")
            return False

    # PII Check: Ensure no forbidden keys exist at root or in metadata
    for key in record.keys():
        if key.lower() in FORBIDDEN_PII_KEYS:
            logger.error(f"PII violation: forbidden root key '{key}' found in record.")
            return False

    if isinstance(record.get("metadata"), dict):
        for key in record["metadata"].keys():
            if key.lower() in FORBIDDEN_PII_KEYS:
                logger.error(f"PII violation: forbidden metadata key '{key}' found in record.")
                return False

    # Text must be non-empty string
    if not isinstance(record["text"], str) or not record["text"].strip():
        return False

    return True


class BaseScraper(ABC):
    """Abstract interface for all platform scrapers."""

    def __init__(self):
        self.query_terms: List[str] = []
        self.recency_months: int = 12
        self.max_results: int = 200
        self.limiter = get_limiter(self.get_source_name())
        self._seen_urls: Set[str] = set()
        self._seen_texts: Set[str] = set()

    @abstractmethod
    def get_source_name(self) -> str:
        """Returns the canonical platform name (e.g., 'reddit', 'youtube', 'appstore')."""
        pass

    def configure(
        self,
        query_terms: List[str],
        recency_months: int = 12,
        max_results: int = 200,
    ) -> None:
        """Configures search query terms and limits for this scraping run."""
        self.query_terms = query_terms
        self.recency_months = recency_months
        self.max_results = max_results
        self._seen_urls.clear()
        self._seen_texts.clear()

    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """
        Executes the scraping process and returns a list of raw records
        conforming to the raw schema.
        """
        pass

    def create_record(
        self,
        text: str,
        source_url: Optional[str] = None,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Factory helper to create a standardized, PII-free RawRecord dictionary.
        Handles deduplication (EC-1.15), HTML sanitization (EC-1.16), and schema creation.
        """
        cleaned_text = sanitize_text(text)
        if not cleaned_text or len(cleaned_text.split()) < 3:
            # Skip empty or negligible content (EC-1.19)
            return None

        # Intra-run deduplication
        if source_url and source_url in self._seen_urls:
            return None
        if cleaned_text in self._seen_texts:
            return None

        if source_url:
            self._seen_urls.add(source_url)
        self._seen_texts.add(cleaned_text)

        # Sanitize metadata to remove any forbidden PII keys
        clean_metadata: Dict[str, Any] = {}
        if metadata and isinstance(metadata, dict):
            for k, v in metadata.items():
                if k.lower() not in FORBIDDEN_PII_KEYS:
                    clean_metadata[k] = v

        record = {
            "record_id": str(uuid.uuid4()),
            "source_platform": self.get_source_name(),
            "source_url": source_url,
            "text": cleaned_text,
            "timestamp": timestamp,
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
            "source_type": "scraped",
            "metadata": clean_metadata,
        }

        if validate_raw_record(record):
            return record
        return None

    def export(self, output_dir: Optional[Path] = None) -> str:
        """
        Fetches records and writes JSONL file to output_dir.
        Returns the written file path as string.
        """
        target_dir = Path(output_dir or RAW_DIR)
        target_dir.mkdir(parents=True, exist_ok=True)

        platform = self.get_source_name()
        current_ym = datetime.now(timezone.utc).strftime("%Y-%m")
        output_file = target_dir / f"{platform}_{current_ym}.jsonl"

        logger.info(f"Fetching records for platform: {platform}...")
        records = self.fetch()

        valid_records = [r for r in records if validate_raw_record(r)]
        logger.info(f"Fetched {len(valid_records)} valid records for {platform}.")

        with open(output_file, "a", encoding="utf-8") as f:
            for rec in valid_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        logger.info(f"Exported {len(valid_records)} records to {output_file}")
        return str(output_file)

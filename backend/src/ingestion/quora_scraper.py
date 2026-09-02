"""
Quora Scraper

Scrapes fashion wishlisting and shopping questions and answers from Quora
via Apify Quora Scraper actors.
"""

from __future__ import annotations

from typing import Any, Dict, List
from src.ingestion.base_scraper import BaseScraper
from src.ingestion.apify_helper import apify_helper
from src.utils.logger import get_logger

logger = get_logger("quora_scraper")


class QuoraScraper(BaseScraper):
    """Scrapes Quora discussions regarding fashion buying decisions and shopping issues."""

    def get_source_name(self) -> str:
        return "quora"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetches Quora questions and top answers using Apify.
        """
        records: List[Dict[str, Any]] = []
        if not apify_helper.is_available:
            logger.info("Apify not configured. Quora scraper requires Apify actor.")
            return records

        actor_id = "crawlerbros/quora-search-scraper"
        search_terms = self.query_terms[:5] if self.query_terms else ["myntra wishlist", "myntra review"]

        for term in search_terms:
            if len(records) >= self.max_results:
                break

            run_input = {
                "search": term,
                "maxResults": min(50, self.max_results - len(records)),
                "language": "en",
            }

            try:
                self.limiter.acquire()
                items = apify_helper.run_actor(actor_id, run_input, timeout_secs=120)

                for item in items:
                    question = item.get("question") or item.get("title") or ""
                    answer = item.get("answer") or item.get("text") or ""
                    url = item.get("url") or item.get("link")
                    timestamp = item.get("date") or item.get("createdAt")

                    # Discard truncated/login-wall content < 30 words (EC-1.12)
                    combined_text = f"Q: {question}\nA: {answer}".strip() if answer else question
                    if len(combined_text.split()) < 10:
                        continue

                    rec = self.create_record(
                        text=combined_text,
                        source_url=url,
                        timestamp=timestamp,
                        metadata={
                            "question_title": question,
                            "upvotes": item.get("upvotes"),
                        },
                    )
                    if rec:
                        records.append(rec)

            except Exception as e:
                logger.warning(f"Error scraping Quora for '{term}': {e}")
                continue

        return records

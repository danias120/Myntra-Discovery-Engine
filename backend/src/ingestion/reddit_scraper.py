"""
Reddit Scraper

Scrapes fashion wishlisting, shopping, and sizing discussions from targeted subreddits
via Apify Reddit Scrapers with fallback to Reddit public JSON feeds.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
import requests

from src.ingestion.base_scraper import BaseScraper
from src.ingestion.config import TARGET_SUBREDDITS
from src.ingestion.apify_helper import apify_helper
from src.utils.logger import get_logger

logger = get_logger("reddit_scraper")


class RedditScraper(BaseScraper):
    """Scrapes Reddit posts and comments regarding fashion shopping and wishlists."""

    def __init__(self):
        super().__init__()
        self.subreddits = TARGET_SUBREDDITS

    def get_source_name(self) -> str:
        return "reddit"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetches Reddit posts and comments using Apify or public search endpoint.
        """
        records: List[Dict[str, Any]] = []

        # Attempt 1: Use Apify Reddit Scraper if configured
        if apify_helper.is_available:
            try:
                records = self._fetch_via_apify()
                if records:
                    return records
            except Exception as e:
                logger.warning(f"Apify Reddit scrape failed, falling back to public feed: {e}")

        # Attempt 2: Direct public Reddit search JSON endpoints (Free, rate-limited)
        records = self._fetch_via_public_api()
        return records

    def _fetch_via_apify(self) -> List[Dict[str, Any]]:
        """Uses Apify Reddit Scraper actor."""
        records = []
        actor_id = "trudax/reddit-scraper-lite"

        search_terms = self.query_terms[:5] if self.query_terms else ["myntra wishlist", "myntra size"]
        run_input = {
            "searches": search_terms,
            "subreddits": self.subreddits,
            "maxItems": self.max_results,
            "sort": "relevance",
            "time": "year",
        }

        self.limiter.acquire()
        items = apify_helper.run_actor(actor_id, run_input, timeout_secs=180)

        for item in items:
            # Extract post or comment text
            body = item.get("body") or item.get("selftext") or item.get("title") or ""
            url = item.get("url") or item.get("permalink")
            created_at = item.get("createdAt") or item.get("timestamp")
            subreddit = item.get("subreddit")

            # Filter deleted / removed (EC-1.11)
            if body in ("[deleted]", "[removed]") or not body.strip():
                continue

            # Strip any residual u/ username mentions in text
            cleaned_text = re.sub(r"u\/[A-Za-z0-9_-]+", "[USER]", body)

            rec = self.create_record(
                text=cleaned_text,
                source_url=url,
                timestamp=created_at,
                metadata={
                    "subreddit": subreddit,
                    "thread_title": item.get("title"),
                    "score": item.get("score"),
                },
            )
            if rec:
                records.append(rec)

        return records

    def _fetch_via_public_api(self) -> List[Dict[str, Any]]:
        """Scrapes public Reddit search JSON with rate limiting and headers."""
        records: List[Dict[str, Any]] = []
        headers = {"User-Agent": "MyntraResearchBot/1.0 (Mozilla/5.0; research discovery)"}

        for subreddit in self.subreddits:
            for term in self.query_terms[:4]:
                if len(records) >= self.max_results:
                    break

                search_url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    "q": term,
                    "restrict_sr": "1",
                    "sort": "relevance",
                    "t": "year",
                    "limit": 25,
                }

                try:
                    self.limiter.acquire()
                    resp = requests.get(search_url, params=params, headers=headers, timeout=10)
                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    children = data.get("data", {}).get("children", [])

                    for child in children:
                        pdata = child.get("data", {})
                        title = pdata.get("title", "")
                        selftext = pdata.get("selftext", "")
                        permalink = f"https://reddit.com{pdata.get('permalink', '')}"
                        created_utc = pdata.get("created_utc")

                        timestamp = None
                        if created_utc:
                            from datetime import datetime, timezone
                            timestamp = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

                        # Combine title and selftext
                        full_text = f"{title}\n{selftext}".strip()
                        if full_text in ("[deleted]", "[removed]"):
                            continue

                        cleaned_text = re.sub(r"u\/[A-Za-z0-9_-]+", "[USER]", full_text)

                        rec = self.create_record(
                            text=cleaned_text,
                            source_url=permalink,
                            timestamp=timestamp,
                            metadata={
                                "subreddit": subreddit,
                                "thread_title": title,
                                "score": pdata.get("score"),
                            },
                        )
                        if rec:
                            records.append(rec)

                except Exception as e:
                    logger.debug(f"Error fetching Reddit r/{subreddit} for '{term}': {e}")
                    continue

        return records

"""
Instagram Scraper

Scrapes public Instagram posts and comments on fashion hauls, sizing, and review hashtags
(#myntrahaul, #myntrafashion, #myntrareview, #myntrafinds, #ajiohaul) via Apify Instagram Scraper.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List
from src.ingestion.base_scraper import BaseScraper
from src.ingestion.config import INSTAGRAM_HASHTAGS
from src.ingestion.apify_helper import apify_helper
from src.utils.logger import get_logger

logger = get_logger("instagram_scraper")


class InstagramScraper(BaseScraper):
    """Scrapes Instagram captions and comments on fashion haul/review hashtags."""

    def __init__(self):
        super().__init__()
        self.hashtags = INSTAGRAM_HASHTAGS

    def get_source_name(self) -> str:
        return "instagram"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Fetches Instagram captions and comments using Apify actor.
        """
        records: List[Dict[str, Any]] = []
        if not apify_helper.is_available:
            logger.info("Apify not configured. Instagram scraper requires Apify.")
            return records

        actor_id = "apify/instagram-scraper"

        clean_hashtags = [h.replace("#", "") for h in self.hashtags[:3]]
        run_input = {
            "hashtags": clean_hashtags,
            "resultsLimit": min(50, self.max_results),
            "resultsType": "posts",
        }

        try:
            self.limiter.acquire()
            items = apify_helper.run_actor(actor_id, run_input, timeout_secs=180)

            for item in items:
                caption = item.get("caption") or ""
                url = item.get("url") or item.get("postUrl")
                timestamp = item.get("timestamp")
                likes = item.get("likesCount", 0)
                comments_count = item.get("commentsCount", 0)

                # Strip @handle tags from caption
                cleaned_caption = re.sub(r"@[\w_.]+", "[USER]", caption)

                # Add post caption record if meaningful (EC-1.09)
                rec = self.create_record(
                    text=cleaned_caption,
                    source_url=url,
                    timestamp=timestamp,
                    metadata={
                        "likes_count": likes,
                        "comments_count": comments_count,
                        "content_type": "post_caption",
                    },
                )
                if rec:
                    records.append(rec)

                # Process top comments if returned
                top_comments = item.get("latestComments", [])
                for comment in top_comments:
                    c_text = comment.get("text", "")
                    cleaned_c_text = re.sub(r"@[\w_.]+", "[USER]", c_text)
                    c_rec = self.create_record(
                        text=cleaned_c_text,
                        source_url=url,
                        timestamp=comment.get("timestamp"),
                        metadata={
                            "content_type": "post_comment",
                        },
                    )
                    if c_rec:
                        records.append(c_rec)

        except Exception as e:
            logger.warning(f"Error scraping Instagram: {e}")

        return records

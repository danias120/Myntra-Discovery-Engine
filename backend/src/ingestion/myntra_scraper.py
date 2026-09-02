"""
Myntra Product Reviews Scraper

Scrapes public customer reviews, star ratings, product categories, and sizing comments
from Myntra product pages using requests + BeautifulSoup and Apify web scraper fallback.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

from src.ingestion.base_scraper import BaseScraper
from src.ingestion.apify_helper import apify_helper
from src.utils.logger import get_logger

logger = get_logger("myntra_scraper")


class MyntraScraper(BaseScraper):
    """Scrapes product reviews directly from public Myntra fashion product categories."""

    def __init__(self):
        super().__init__()
        # Representative sample of high-wishlist fashion product categories
        self.sample_category_urls = [
            "https://www.myntra.com/dresses",
            "https://www.myntra.com/kurtas",
            "https://www.myntra.com/jeans",
            "https://www.myntra.com/jackets",
            "https://www.myntra.com/casual-shoes",
        ]

    def get_source_name(self) -> str:
        return "myntra_reviews"

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Scrapes Myntra reviews using HTTP requests with fallback to Apify web scraper.
        """
        records: List[Dict[str, Any]] = []

        # Attempt 1: Direct HTTP parsing with defensive headers
        records = self._fetch_via_http()
        if records:
            return records

        # Attempt 2: Apify Web Scraper Actor if HTTP blocked
        if apify_helper.is_available:
            records = self._fetch_via_apify()

        return records

    def _fetch_via_http(self) -> List[Dict[str, Any]]:
        """Parses public product pages using BeautifulSoup."""
        records = []
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        for cat_url in self.sample_category_urls:
            if len(records) >= self.max_results:
                break

            try:
                self.limiter.acquire()
                resp = requests.get(cat_url, headers=headers, timeout=12)
                if resp.status_code != 200:
                    logger.debug(f"Myntra HTTP {resp.status_code} for {cat_url}")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Extract script state data if embedded
                scripts = soup.find_all("script")
                for script in scripts:
                    text = script.string or ""
                    if "window.__myx = " in text or "pdpData" in text:
                        # Extract product reviews from embedded state JSON
                        review_texts = re.findall(r'"reviewText":"([^"]+)"', text)
                        ratings = re.findall(r'"userRating":(\d+)', text)
                        prod_names = re.findall(r'"name":"([^"]+)"', text)
                        
                        prod_name = prod_names[0] if prod_names else "Fashion Apparel"
                        category = cat_url.split("/")[-1]

                        for idx, r_text in enumerate(review_texts):
                            rating = int(ratings[idx]) if idx < len(ratings) else 0
                            rec = self.create_record(
                                text=r_text,
                                source_url=cat_url,
                                metadata={
                                    "product_name": prod_name,
                                    "product_category": category,
                                    "rating": rating,
                                },
                            )
                            if rec:
                                records.append(rec)

            except Exception as e:
                logger.debug(f"Direct Myntra review scrape error for {cat_url}: {e}")
                continue

        return records

    def _fetch_via_apify(self) -> List[Dict[str, Any]]:
        """Uses Apify Web Scraper for Myntra."""
        records = []
        actor_id = "apify/web-scraper"
        run_input = {
            "startUrls": [{"url": u} for u in self.sample_category_urls[:2]],
            "maxPagesPerCrawl": 5,
        }

        try:
            self.limiter.acquire()
            items = apify_helper.run_actor(actor_id, run_input, timeout_secs=120)
            for item in items:
                text = item.get("reviewText") or item.get("text") or ""
                rec = self.create_record(
                    text=text,
                    source_url=item.get("url"),
                    metadata={
                        "product_name": item.get("productName", "Myntra Product"),
                        "rating": item.get("rating", 0),
                    },
                )
                if rec:
                    records.append(rec)
        except Exception as e:
            logger.warning(f"Apify Myntra scraper error: {e}")

        return records

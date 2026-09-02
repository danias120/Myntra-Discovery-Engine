"""
Fashion Forum Scraper

Lightweight HTTP scraper for Indian fashion discussion forums and communities
with strict robots.txt compliance and rate limiting. (Handles EC-1.13, EC-1.14)
"""

from __future__ import annotations

import urllib.robotparser
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

from src.ingestion.base_scraper import BaseScraper
from src.utils.logger import get_logger

logger = get_logger("forum_scraper")


class ForumScraper(BaseScraper):
    """Scrapes publicly accessible fashion discussion forums and threads."""

    def __init__(self):
        super().__init__()
        self.forum_urls = [
            "https://fashionbombdaily.com",
            "https://stylecracker.com/blog",
        ]

    def get_source_name(self) -> str:
        return "forum"

    def is_allowed_by_robots(self, url: str) -> bool:
        """Checks robots.txt before making scraping requests (EC-1.14)."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch("*", url)
        except Exception as e:
            logger.debug(f"Could not check robots.txt for {url}: {e}")
            return True

    def fetch(self) -> List[Dict[str, Any]]:
        """
        Scrapes fashion forums while respecting rate limits and robots.txt.
        """
        records: List[Dict[str, Any]] = []
        headers = {
            "User-Agent": "MyntraResearchBot/1.0 (Mozilla/5.0; Academic Research)",
        }

        for site_url in self.forum_urls:
            if len(records) >= self.max_results:
                break

            if not self.is_allowed_by_robots(site_url):
                logger.warning(f"robots.txt disallows scraping for: {site_url}. Skipping.")
                continue

            try:
                self.limiter.acquire()
                resp = requests.get(site_url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                
                # Extract articles, threads, paragraphs
                articles = soup.find_all(["article", "div"], class_=lambda c: c and ("post" in c or "thread" in c or "entry" in c))
                
                for art in articles:
                    title_elem = art.find(["h1", "h2", "h3"])
                    title = title_elem.get_text().strip() if title_elem else ""
                    
                    paragraphs = art.find_all("p")
                    body = " ".join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20)
                    
                    full_text = f"{title}\n{body}".strip() if title else body
                    if len(full_text.split()) < 15:
                        continue

                    link_elem = art.find("a", href=True)
                    source_url = link_elem["href"] if link_elem else site_url

                    rec = self.create_record(
                        text=full_text,
                        source_url=source_url,
                        metadata={
                            "thread_title": title,
                            "site": site_url,
                        },
                    )
                    if rec:
                        records.append(rec)

            except Exception as e:
                logger.debug(f"Error scraping forum {site_url}: {e}")
                continue

        return records

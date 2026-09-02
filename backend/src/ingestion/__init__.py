"""
Ingestion Package

Provides scrapers and data loaders for all raw conversation and user research sources.
"""

from src.ingestion.base_scraper import BaseScraper, sanitize_text, validate_raw_record
from src.ingestion.apify_helper import ApifyHelper, apify_helper, QuotaExhaustedError
from src.ingestion.config import (
    QUERY_TERMS,
    RECENCY_MONTHS,
    TARGET_RECORDS_PER_SOURCE,
    PLATFORM_RATE_LIMITS,
    RESEARCH_DATA,
    TARGET_SUBREDDITS,
    YOUTUBE_SEARCH_QUERIES,
    INSTAGRAM_HASHTAGS,
    TARGET_APP_IDS,
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
from src.ingestion.runner import run_ingestion

__all__ = [
    "BaseScraper",
    "sanitize_text",
    "validate_raw_record",
    "ApifyHelper",
    "apify_helper",
    "QuotaExhaustedError",
    "QUERY_TERMS",
    "RECENCY_MONTHS",
    "TARGET_RECORDS_PER_SOURCE",
    "PLATFORM_RATE_LIMITS",
    "RESEARCH_DATA",
    "TARGET_SUBREDDITS",
    "YOUTUBE_SEARCH_QUERIES",
    "INSTAGRAM_HASHTAGS",
    "TARGET_APP_IDS",
    "get_query_terms_for_platform",
    "RedditScraper",
    "QuoraScraper",
    "AppStoreScraper",
    "PlayStoreScraper",
    "YouTubeScraper",
    "InstagramScraper",
    "MyntraScraper",
    "ForumScraper",
    "ResearchIngester",
    "run_ingestion",
]

"""
Cleaning Package

Provides deterministic text normalization, PII stripping, deduplication,
spam filtering, relevance filtering, and semantic chunking.
"""

from src.cleaning.pii_stripper import (
    PIIStripper,
    pii_stripper,
    BRAND_WHITELIST,
    CITY_WHITELIST,
)
from src.cleaning.deduplicator import (
    Deduplicator,
    deduplicator,
    normalize_text_for_hash,
    create_minhash,
)
from src.cleaning.spam_filter import (
    SpamFilter,
    spam_filter,
    calculate_shannon_entropy,
    is_keyboard_mash,
)
from src.cleaning.relevance_filter import (
    RelevanceFilter,
    relevance_filter,
    TIER_1_KEYWORDS,
    TIER_2_KEYWORDS,
    EXCLUDE_PATTERNS,
)
from src.cleaning.chunker import (
    Chunker,
    chunker,
)

__all__ = [
    "PIIStripper",
    "pii_stripper",
    "BRAND_WHITELIST",
    "CITY_WHITELIST",
    "Deduplicator",
    "deduplicator",
    "normalize_text_for_hash",
    "create_minhash",
    "SpamFilter",
    "spam_filter",
    "calculate_shannon_entropy",
    "is_keyboard_mash",
    "RelevanceFilter",
    "relevance_filter",
    "TIER_1_KEYWORDS",
    "TIER_2_KEYWORDS",
    "EXCLUDE_PATTERNS",
    "Chunker",
    "chunker",
]

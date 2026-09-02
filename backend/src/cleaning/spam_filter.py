"""
Spam and Boilerplate Filter Module

Implements multi-rule noise and spam filtering:
1. Length validation (3 to 2,000 words, exempting interview transcripts).
2. Shannon character entropy calculation for gibberish and keyboard mash detection.
3. Character and word repetition normalization.
4. Promotional spam and referral link detection.
5. Platform boilerplate and bot signature stripping.

Handles Edge Cases: EC-2.12, EC-2.13, EC-2.14, EC-2.15, EC-2.16
"""

from __future__ import annotations

import collections
import math
import re
from typing import Any, Dict, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger("spam_filter")

# Regex for promotional links, referral codes, and affiliate spam (EC-2.14)
RE_PROMO = re.compile(
    r"(?:"
    r"t\.me/[\w_-]+"
    r"|telegram\.me/[\w_-]+"
    r"|chat\.whatsapp\.com/[\w_-]+"
    r"|wa\.me/\d+"
    r"|bit\.ly/[\w_-]+"
    r"|tinyurl\.com/[\w_-]+"
    r"|cutt\.ly/[\w_-]+"
    r"|\b(?:use|apply)\s+(?:my\s+)?(?:referral\s+|coupon\s+)?code\s+[:\-]?\s*[A-Z0-9]{4,15}\b"
    r"|\bearn\s+(?:₹|rs\.?|inr)\s*\d+\s*(?:daily|free|online)\b"
    r"|\b(?:crypto|bitcoin|binance|forex trading|invest now)\b"
    r")",
    re.IGNORECASE,
)

# Regex for platform boilerplate patterns (EC-2.15)
RE_REDDIT_BOT = re.compile(
    r"I am a bot, and this action was performed automatically[^\n]*",
    re.IGNORECASE,
)
RE_REDDIT_SUBMITTED = re.compile(
    r"submitted by\s+/?\[USER\][^\n]*|\[link\]\s+\[comments\]",
    re.IGNORECASE,
)
RE_STORE_HELPFUL = re.compile(
    r"(?:Was this review helpful\??|\d+\s+people found this helpful)[^\n]*",
    re.IGNORECASE,
)
RE_READ_MORE = re.compile(r"\b(?:Read more\.\.\.|Show less|Translate review)\b", re.IGNORECASE)
RE_QUORA_UPVOTE = re.compile(
    r"(?:Upvote if (?:you (?:found this helpful|agree|liked this)|helpful)|Follow (?:me|my profile) for more)[^\n]*",
    re.IGNORECASE,
)
RE_YT_SUBSCRIBE = re.compile(
    r"(?:Don't forget to like,?\s*share\s*and\s*subscribe|Subscribe to my channel)[^\n]*",
    re.IGNORECASE,
)
RE_YT_TIMESTAMPS = re.compile(
    r"\b\d{1,2}:\d{2}(?::\d{2})?\s+[-–—]?\s*[A-Za-z0-9\s]{3,30}(?=\n|$)",
    re.MULTILINE,
)

# Character lengthening for letters only (e.g., "sooooo goooood" -> "soo good", preserving numbers like "1000") (EC-2.13)
RE_CHAR_LENGTHENING = re.compile(r"([a-zA-Z])\1{2,}")


def calculate_shannon_entropy(text: str) -> float:
    """
    Calculates the Shannon character entropy of a string.
    Normal natural English text typically ranges between 3.0 and 4.8.
    Low entropy (< 1.8) indicates repetitive characters (e.g. 'aaaaaaaaaa').
    High entropy (> 5.2 on long strings) with lack of dictionary words indicates random mash.
    """
    if not text:
        return 0.0
    text_clean = text.lower().strip()
    if not text_clean:
        return 0.0
    
    counts = collections.Counter(text_clean)
    total = len(text_clean)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def is_keyboard_mash(text: str) -> bool:
    """Detects random keyboard mashing (e.g., 'asdkjfhaskjdfh', 'zzzzzzzz')."""
    words = text.split()
    for w in words:
        w_clean = re.sub(r"[^\w]", "", w.lower())
        if len(w_clean) >= 12:
            # Check vowel ratio
            vowels = sum(1 for c in w_clean if c in "aeiou")
            vowel_ratio = vowels / len(w_clean)
            if vowel_ratio < 0.10 or vowel_ratio > 0.85:
                return True
            # Check character entropy of the long token
            token_entropy = calculate_shannon_entropy(w_clean)
            if token_entropy < 2.0 or (token_entropy > 4.5 and len(set(w_clean)) > 10):
                return True
    return False


class SpamFilter:
    """Multi-rule spam and noise filter for evidence datasets."""

    def __init__(self, min_words: int = 3, max_words: int = 2000):
        self.min_words = min_words
        self.max_words = max_words
        self.stats = {
            "total_processed": 0,
            "passed": 0,
            "dropped_length": 0,
            "dropped_spam": 0,
            "dropped_gibberish": 0,
        }

    def strip_boilerplate(self, text: str) -> str:
        """Removes platform boilerplate, bot footers, and timestamp tables (EC-2.15)."""
        if not text:
            return ""

        # Reddit
        text = RE_REDDIT_BOT.sub("", text)
        text = RE_REDDIT_SUBMITTED.sub("", text)

        # App Store / Play Store
        text = RE_STORE_HELPFUL.sub("", text)
        text = RE_READ_MORE.sub("", text)

        # Quora
        text = RE_QUORA_UPVOTE.sub("", text)

        # YouTube
        text = RE_YT_SUBSCRIBE.sub("", text)
        text = RE_YT_TIMESTAMPS.sub("", text)

        # Normalize multiple newlines/spaces
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines).strip()

    def normalize_repetition(self, text: str) -> str:
        """Normalizes character lengthening (EC-2.13) and repetitive words."""
        if not text:
            return ""

        # Replace 3+ repeated letters with 2 (e.g. 'sooo' -> 'soo')
        text = RE_CHAR_LENGTHENING.sub(r"\1\1", text)

        # Normalize 4+ repeated consecutive words (e.g. 'good good good good' -> 'good')
        text = re.sub(r"\b(\w+)(?:\s+\1){3,}\b", r"\1", text, flags=re.IGNORECASE)

        return text

    def clean_text(self, text: str) -> str:
        """Applies boilerplate stripping and character repetition normalization."""
        if not text:
            return ""
        text = self.strip_boilerplate(text)
        text = self.normalize_repetition(text)
        return text

    def is_spam_or_noise(
        self, text: str, source_platform: str = "", source_type: str = ""
    ) -> Tuple[bool, str]:
        """
        Evaluates whether a text is spam, gibberish, or outside valid length thresholds.
        Returns (is_invalid, reason).
        """
        if not text or not text.strip():
            return True, "empty_text"

        words = text.split()
        word_count = len(words)

        # 1. Length Check (EC-2.16) - interviews and surveys are exempt from max_words
        is_interview_or_survey = source_type == "interview" or source_platform in ("interviews", "surveys")
        if word_count < self.min_words:
            return True, f"too_short_{word_count}_words"
        if not is_interview_or_survey and word_count > self.max_words:
            return True, f"too_long_{word_count}_words"

        # 2. Promotional Spam Check (EC-2.14)
        if RE_PROMO.search(text):
            return True, "promotional_or_referral_spam"

        # 3. Gibberish & Shannon Entropy Check (EC-2.12)
        if len(text) >= 20:
            entropy = calculate_shannon_entropy(text)
            if entropy < 1.8:
                return True, f"low_entropy_{entropy:.2f}"
            if is_keyboard_mash(text):
                return True, "keyboard_mash_detected"

        return False, "valid"

    def process_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Cleans and validates a record.
        Returns the sanitized record with boilerplate stripped, or None if dropped as spam.
        """
        self.stats["total_processed"] += 1
        raw_text = record.get("text", "")
        source_platform = record.get("source_platform", "")
        source_type = record.get("source_type", "")

        cleaned_text = self.clean_text(raw_text)
        is_spam, reason = self.is_spam_or_noise(cleaned_text, source_platform, source_type)

        if is_spam:
            if "too_short" in reason or "too_long" in reason:
                self.stats["dropped_length"] += 1
            elif "promo" in reason:
                self.stats["dropped_spam"] += 1
            else:
                self.stats["dropped_gibberish"] += 1
            logger.debug(f"Dropped record {record.get('record_id')}: {reason}")
            return None

        self.stats["passed"] += 1
        clean_rec = dict(record)
        clean_rec["text"] = cleaned_text
        meta = clean_rec.setdefault("metadata", {})
        meta["spam_checked"] = True
        return clean_rec

    def get_stats(self) -> Dict[str, Any]:
        """Returns filter statistics."""
        return self.stats


# Global singleton instance
spam_filter = SpamFilter()

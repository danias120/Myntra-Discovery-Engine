"""
Deduplicator Module

Implements a two-tier deduplication engine:
1. Exact deduplication via normalized text SHA-256 hashing.
2. Near-duplicate / fuzzy deduplication via MinHash LSH (128 permutations, Jaccard threshold >= 0.85).

Handles Edge Cases: EC-2.07, EC-2.08, EC-2.09, EC-2.10, EC-2.11
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Set, Tuple
from datasketch import MinHash, MinHashLSH

from src.utils.logger import get_logger

logger = get_logger("deduplicator")


def normalize_text_for_hash(text: str) -> str:
    """Normalizes text by lowercasing, stripping punctuation and collapsing whitespace."""
    if not text:
        return ""
    # Lowercase and replace non-alphanumeric with spaces
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


def create_minhash(text: str, num_perm: int = 128, shingle_k: int = 4) -> MinHash:
    """
    Creates a MinHash signature using character k-grams and word shingles
    to capture both typo resilience and semantic phrase overlap.
    """
    m = MinHash(num_perm=num_perm)
    norm = normalize_text_for_hash(text)
    if not norm:
        return m

    # Character 4-grams (robust to minor typos and punctuation differences)
    if len(norm) <= shingle_k:
        m.update(norm.encode("utf-8"))
    else:
        for i in range(len(norm) - shingle_k + 1):
            shingle = norm[i:i + shingle_k]
            m.update(shingle.encode("utf-8"))

    # Word 2-grams (captures phrase sequences)
    words = norm.split()
    if len(words) >= 2:
        for i in range(len(words) - 1):
            w_shingle = f"{words[i]} {words[i+1]}"
            m.update(w_shingle.encode("utf-8"))

    return m


def calculate_metadata_richness(record: Dict[str, Any]) -> int:
    """Calculates a completeness score for a record's metadata."""
    score = 0
    if record.get("source_url"):
        score += 2
    if record.get("timestamp"):
        score += 2
    meta = record.get("metadata", {})
    if isinstance(meta, dict):
        for k, v in meta.items():
            if v is not None and v != "":
                score += 1
                if k in ("rating", "product_category", "product_name", "subreddit"):
                    score += 2
    return score


class Deduplicator:
    """
    Two-tier deduplicator for raw/cleaned evidence corpora.
    Preserves highest metadata completeness and records cross-platform occurrences.
    """

    def __init__(self, threshold: float = 0.85, num_perm: int = 128):
        self.threshold = threshold
        self.num_perm = num_perm
        self.stats = {
            "total_evaluated": 0,
            "exact_duplicates_removed": 0,
            "near_duplicates_merged": 0,
            "unique_records_retained": 0,
        }

    def deduplicate_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes a list of records through exact and MinHash LSH fuzzy deduplication.
        Returns the deduplicated list of records with updated cross-posting metadata.
        """
        self.stats = {
            "total_evaluated": len(records),
            "exact_duplicates_removed": 0,
            "near_duplicates_merged": 0,
            "unique_records_retained": 0,
        }
        unique_records: List[Dict[str, Any]] = []
        exact_hash_map: Dict[str, int] = {}  # hash -> index in unique_records
        lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)

        for rec in records:
            text = rec.get("text", "")
            if not text or len(text.strip()) == 0:
                continue

            norm_text = normalize_text_for_hash(text)
            text_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
            platform = rec.get("source_platform", "unknown")

            # --- Tier 1: Exact Deduplication (EC-2.07) ---
            if text_hash in exact_hash_map:
                self.stats["exact_duplicates_removed"] += 1
                existing_idx = exact_hash_map[text_hash]
                existing_rec = unique_records[existing_idx]
                
                # Merge cross-platform presence (EC-2.08)
                existing_meta = existing_rec.setdefault("metadata", {})
                platforms = set(existing_meta.get("cross_posted_platforms", [existing_rec.get("source_platform")]))
                platforms.add(platform)
                existing_meta["cross_posted_platforms"] = sorted(list(platforms))
                existing_meta["duplicate_count"] = existing_meta.get("duplicate_count", 1) + 1

                # If current record has richer metadata, replace core metadata
                if calculate_metadata_richness(rec) > calculate_metadata_richness(existing_rec):
                    merged_meta = dict(rec.get("metadata", {}))
                    merged_meta["cross_posted_platforms"] = sorted(list(platforms))
                    merged_meta["duplicate_count"] = existing_meta["duplicate_count"]
                    existing_rec["metadata"] = merged_meta
                continue

            # --- Tier 2: Fuzzy MinHash LSH Deduplication (EC-2.09) ---
            words = norm_text.split()
            is_near_dup = False
            if len(words) >= 5:
                mh = create_minhash(norm_text, num_perm=self.num_perm)
                try:
                    candidates = lsh.query(mh)
                    for cand_id in candidates:
                        cand_idx = int(cand_id)
                        cand_rec = unique_records[cand_idx]
                        cand_mh = create_minhash(cand_rec.get("text", ""), num_perm=self.num_perm)
                        jaccard = mh.jaccard(cand_mh)

                        if jaccard >= self.threshold:
                            is_near_dup = True
                            self.stats["near_duplicates_merged"] += 1
                            cand_meta = cand_rec.setdefault("metadata", {})
                            cand_meta["near_duplicate_count"] = cand_meta.get("near_duplicate_count", 1) + 1
                            cand_meta["jaccard_similarity"] = round(jaccard, 3)
                            
                            # Record cross-posting
                            platforms = set(cand_meta.get("cross_posted_platforms", [cand_rec.get("source_platform")]))
                            platforms.add(platform)
                            cand_meta["cross_posted_platforms"] = sorted(list(platforms))
                            break
                except Exception as e:
                    logger.debug(f"MinHash LSH query error: {e}")

            if is_near_dup:
                continue

            # Record is unique!
            new_idx = len(unique_records)
            unique_records.append(rec)
            exact_hash_map[text_hash] = new_idx

            # Index in LSH if eligible length
            if len(words) >= 5:
                mh = create_minhash(norm_text, num_perm=self.num_perm)
                try:
                    lsh.insert(str(new_idx), mh)
                except Exception as e:
                    logger.debug(f"MinHash LSH insert error: {e}")

        self.stats["unique_records_retained"] = len(unique_records)
        logger.info(
            f"Deduplication finished: {self.stats['total_evaluated']} evaluated -> "
            f"{self.stats['unique_records_retained']} unique retained "
            f"({self.stats['exact_duplicates_removed']} exact, {self.stats['near_duplicates_merged']} fuzzy merged)."
        )
        return unique_records

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics from the most recent deduplication run."""
        return self.stats


# Global singleton instance
deduplicator = Deduplicator()

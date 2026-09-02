"""
Cache Utility

JSON/File-based caching for LLM responses and intermediate results.
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Optional
from src.utils.config import THEMES_DIR
from src.utils.logger import get_logger

logger = get_logger("cache")
CACHE_DIR = THEMES_DIR / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class FileCache:
    """Key-value cache backed by individual JSON files keyed by SHA-256 hash."""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_key(data: str) -> str:
        """Computes SHA-256 hash for the given string data."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieves a cached value if it exists."""
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    logger.debug(f"Cache HIT for key: {key[:8]}...")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache for {key}: {e}")
                return None
        return None

    def set(self, key: str, value: Any) -> None:
        """Stores a JSON-serializable value in the cache."""
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False, indent=2)
            logger.debug(f"Cached result for key: {key[:8]}...")
        except Exception as e:
            logger.warning(f"Error writing cache for {key}: {e}")

    def clear(self) -> int:
        """Clears all cached items in the cache directory. Returns count of deleted files."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {cache_file}: {e}")
        logger.info(f"Cleared {count} cached files.")
        return count


# Default global cache instance
default_cache = FileCache()

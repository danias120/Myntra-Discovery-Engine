"""
Rate Limiter Utility

Token-bucket and sliding window rate limiting with exponential backoff.
"""

import time
import threading
from typing import Dict
from src.utils.logger import get_logger

logger = get_logger("rate_limiter")


class RateLimiter:
    """Thread-safe rate limiter managing requests per minute and daily quotas."""

    def __init__(self, requests_per_minute: int = 15, requests_per_day: int = 1500):
        self.rpm = requests_per_minute
        self.rpd = requests_per_day
        self.interval = 60.0 / requests_per_minute if requests_per_minute > 0 else 0.0
        
        self.last_request_time = 0.0
        self.daily_requests: list[float] = []
        self.lock = threading.Lock()

    def acquire(self) -> None:
        """Blocks if needed until a request slot is available under the rate limit."""
        with self.lock:
            now = time.time()
            
            # Prune daily request timestamps older than 24h (86400s)
            cutoff = now - 86400.0
            self.daily_requests = [t for t in self.daily_requests if t > cutoff]
            
            if len(self.daily_requests) >= self.rpd:
                oldest = self.daily_requests[0]
                wait_time = max(0.0, 86400.0 - (now - oldest))
                logger.warning(
                    f"Daily limit of {self.rpd} requests reached. Must wait {wait_time:.1f}s"
                )
                raise RuntimeError(f"Daily request quota ({self.rpd}) exhausted.")

            # Enforce RPM spacing
            elapsed = now - self.last_request_time
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)

            self.last_request_time = time.time()
            self.daily_requests.append(self.last_request_time)

    def get_status(self) -> Dict[str, int]:
        """Returns current quota status."""
        with self.lock:
            now = time.time()
            cutoff = now - 86400.0
            active_daily = len([t for t in self.daily_requests if t > cutoff])
            return {
                "rpm_limit": self.rpm,
                "rpd_limit": self.rpd,
                "requests_last_24h": active_daily,
                "daily_remaining": max(0, self.rpd - active_daily),
            }


# Pre-configured rate limiters per platform
_LIMITERS: Dict[str, RateLimiter] = {
    "gemini": RateLimiter(requests_per_minute=15, requests_per_day=1500),
    "reddit": RateLimiter(requests_per_minute=10, requests_per_day=500),
    "quora": RateLimiter(requests_per_minute=5, requests_per_day=300),
    "youtube": RateLimiter(requests_per_minute=5, requests_per_day=300),
    "instagram": RateLimiter(requests_per_minute=3, requests_per_day=200),
    "appstore": RateLimiter(requests_per_minute=10, requests_per_day=500),
    "playstore": RateLimiter(requests_per_minute=10, requests_per_day=500),
    "myntra": RateLimiter(requests_per_minute=5, requests_per_day=200),
    "forum": RateLimiter(requests_per_minute=10, requests_per_day=300),
}


def get_limiter(platform: str) -> RateLimiter:
    """Retrieves or creates a rate limiter for the given platform."""
    if platform not in _LIMITERS:
        _LIMITERS[platform] = RateLimiter(requests_per_minute=10, requests_per_day=500)
    return _LIMITERS[platform]

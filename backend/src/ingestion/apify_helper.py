"""
Apify Helper Utility

Wraps the ApifyClient with free-tier quota tracking, timeout management,
and graceful error handling. (Handles EC-1.01, EC-1.04, EC-1.05, EC-1.06)
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from src.utils.config import APIFY_API_TOKEN
from src.utils.logger import get_logger

logger = get_logger("apify_helper")


class QuotaExhaustedError(Exception):
    """Raised when Apify free-tier monthly quota is depleted."""
    pass


class ApifyHelper:
    """Helper wrapper around ApifyClient with safety guardrails."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or APIFY_API_TOKEN
        self._client = None
        if self.token:
            try:
                from apify_client import ApifyClient
                self._client = ApifyClient(self.token)
            except Exception as e:
                logger.warning(f"Could not initialize ApifyClient: {e}")

    @property
    def is_available(self) -> bool:
        """Returns True if Apify client is configured and initialized."""
        return self._client is not None

    def run_actor(
        self,
        actor_id: str,
        run_input: Dict[str, Any],
        timeout_secs: int = 180,
        memory_mbytes: int = 512,
    ) -> List[Dict[str, Any]]:
        """
        Executes an Apify actor synchronously, waits for completion,
        and retrieves items from the default dataset.
        """
        if not self.is_available:
            logger.warning(f"Apify client not configured. Skipping actor '{actor_id}'.")
            return []

        logger.info(f"Triggering Apify actor '{actor_id}'...")
        try:
            # Start the actor run
            run = self._client.actor(actor_id).call(
                run_input=run_input,
                timeout_secs=timeout_secs,
                memory_mbytes=memory_mbytes,
            )

            if not run:
                logger.warning(f"Apify actor '{actor_id}' returned no run object.")
                return []

            status = run.get("status")
            logger.info(f"Apify actor '{actor_id}' finished with status: {status}")

            if status == "TIMED_OUT":
                logger.warning(f"Apify actor '{actor_id}' timed out after {timeout_secs}s.")
            elif status not in ("SUCCEEDED", "READY"):
                logger.warning(f"Apify actor '{actor_id}' completed with non-success status: {status}")

            # Fetch dataset items
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                logger.warning(f"No defaultDatasetId for run of actor '{actor_id}'.")
                return []

            items = list(self._client.dataset(dataset_id).iterate_items())
            logger.info(f"Retrieved {len(items)} items from dataset '{dataset_id}'.")
            return items

        except Exception as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "rate limit" in err_msg or "402" in err_msg:
                logger.error(f"Apify free-tier quota exhausted: {e}")
                raise QuotaExhaustedError(f"Apify quota exhausted: {e}") from e
            elif "not found" in err_msg or "404" in err_msg:
                logger.error(f"Apify actor '{actor_id}' not found or deprecated: {e}")
            else:
                logger.error(f"Error running Apify actor '{actor_id}': {e}")
            return []

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Returns Apify account info and remaining monthly usage if accessible."""
        if not self.is_available:
            return None
        try:
            return self._client.user().get()
        except Exception as e:
            logger.debug(f"Could not fetch Apify user info: {e}")
            return None


# Global helper instance
apify_helper = ApifyHelper()

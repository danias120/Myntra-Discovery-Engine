"""
Unified LLM Client

Wraps Google Gemini API and local fallbacks behind a single unified interface.
Handles:
  1. Token estimation
  2. Multi-model fallback rotation (gemini-3.5-flash-lite, gemini-3.1-flash-lite, gemini-3.5-flash)
  3. Dynamic 429 rate limit delay parsing and waiting
  4. Response caching by hash(prompt + system_prompt)
  5. Structured JSON mode support (response_mime_type="application/json")
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    tiktoken = None

from src.utils.config import (
    LLM_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_MODEL,
)
from src.utils.logger import get_logger
from src.utils.cache import default_cache
from src.utils.rate_limiter import get_limiter

logger = get_logger("llm_client")

FALLBACK_MODELS: List[str] = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]


class LLMClient:
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or LLM_PROVIDER).lower()
        self.gemini_model_name = GEMINI_MODEL or "gemini-2.0-flash"
        self.ollama_model_name = OLLAMA_MODEL
        self.limiter = get_limiter("gemini")
        self.cache = default_cache

        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

        self._gemini_client = None
        if self.provider == "gemini" and GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI Client: {e}")

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        return max(1, len(text) // 4)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1,
        use_cache: bool = True,
        max_retries: int = 5,
    ) -> str:
        combined_text = f"SYSTEM: {system_prompt or ''}\nJSON_MODE: {json_mode}\nUSER: {prompt}"
        cache_key = self.cache.generate_key(combined_text)

        if use_cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for LLM prompt")
                return cached.get("text", "") if isinstance(cached, dict) else str(cached)

        estimated_tokens = self.estimate_tokens(combined_text)
        result_text = ""

        if self.provider == "gemini":
            result_text = self._generate_gemini(
                prompt, system_prompt, json_mode=json_mode, temperature=temperature, max_retries=max_retries
            )
        elif self.provider == "ollama":
            result_text = self._generate_ollama(prompt, system_prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        if use_cache and result_text:
            self.cache.set(
                cache_key,
                {
                    "text": result_text,
                    "provider": self.provider,
                    "estimated_input_tokens": estimated_tokens,
                    "timestamp": time.time(),
                },
            )

        return result_text

    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_mode: bool = False,
        temperature: float = 0.1,
        max_retries: int = 5,
    ) -> str:
        if not self._gemini_client and GEMINI_API_KEY:
            from google import genai
            self._gemini_client = genai.Client(api_key=GEMINI_API_KEY)

        if not self._gemini_client:
            logger.warning("Gemini client not available.")
            return ""

        models_to_try = [self.gemini_model_name] + [m for m in FALLBACK_MODELS if m != self.gemini_model_name]

        for model_name in models_to_try:
            backoff = 2.0
            for attempt in range(1, max_retries + 1):
                try:
                    self.limiter.acquire()
                    config_args: Dict[str, Any] = {"temperature": temperature}
                    if system_prompt:
                        config_args["system_instruction"] = system_prompt
                    if json_mode:
                        config_args["response_mime_type"] = "application/json"

                    response = self._gemini_client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config_args,
                    )

                    if response and hasattr(response, "text") and response.text:
                        return response.text.strip()
                    return ""

                except Exception as e:
                    err_str = str(e)
                    # Detect 429 retryDelay
                    delay_match = re.search(r"retry\s+in\s+([0-9\.]+)\s*s", err_str, re.IGNORECASE) or re.search(r"retryDelay':\s*'([0-9]+)s'", err_str)
                    sleep_time = float(delay_match.group(1)) + 1.0 if delay_match else backoff

                    if "429" in err_str or "503" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        logger.warning(
                            f"Rate limit / 503 on {model_name} (attempt {attempt}/{max_retries}): waiting {sleep_time:.1f}s..."
                        )
                        time.sleep(sleep_time)
                        backoff = min(60.0, backoff * 2.0)
                    else:
                        logger.error(f"Error on {model_name}: {e}")
                        break  # Try next model

        logger.error("Exhausted all Gemini models.")
        return ""

    def _generate_ollama(self, prompt: str, system_prompt: Optional[str]) -> str:
        try:
            import urllib.request
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": self.ollama_model_name,
                "prompt": prompt,
                "system": system_prompt or "",
                "stream": False,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, data=data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "").strip()
        except Exception as e:
            logger.debug(f"Ollama fallback skipped: {e}")
            return ""

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        if not self._gemini_client and GEMINI_API_KEY:
            from google import genai
            self._gemini_client = genai.Client(api_key=GEMINI_API_KEY)

        if not self._gemini_client:
            resp = self.generate(prompt, system_prompt)
            yield resp
            return

        try:
            self.limiter.acquire()
            config_args = {}
            if system_prompt:
                config_args["system_instruction"] = system_prompt

            response_stream = self._gemini_client.models.generate_content_stream(
                model=self.gemini_model_name,
                contents=prompt,
                config=config_args if config_args else None,
            )

            for chunk in response_stream:
                if chunk and hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Error in Gemini streaming: {e}")
            yield f"\n[Generation error: {e}]"


default_llm_client = LLMClient()
llm_client = default_llm_client

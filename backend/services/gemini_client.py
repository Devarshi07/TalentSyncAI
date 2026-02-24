"""
Gemini client wrapper with retry logic, timeouts, and rate limit handling.
All services should use this instead of calling genai.Client directly.
"""
import time
import functools
from typing import Callable

from google import genai
from google.genai import types

import config
from core.logging import get_logger

logger = get_logger(__name__)

# Retry config
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # seconds
BACKOFF_MULTIPLIER = 2
TIMEOUT_SECONDS = 30


def _get_client() -> genai.Client:
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=config.GEMINI_API_KEY)


def generate_with_retry(
    contents: str,
    system_instruction: str = "",
    temperature: float = 0.3,
    model: str = None,
) -> str:
    """
    Call Gemini with automatic retry on rate limits and transient errors.
    Returns the text response or raises after MAX_RETRIES.
    """
    model = model or config.GEMINI_MODEL
    client = _get_client()

    gen_config = types.GenerateContentConfig(temperature=temperature)
    if system_instruction:
        gen_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        )

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=gen_config,
            )
            text = getattr(response, "text", "") or ""
            if text.strip():
                return text.strip()

            logger.warning("Gemini returned empty response", extra={"attempt": attempt + 1})
            # Treat empty response as retryable
            last_error = ValueError("Empty response from Gemini")

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            # Rate limit — wait and retry
            if "429" in str(e) or "resource_exhausted" in error_str or "quota" in error_str:
                wait = INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ** attempt)
                logger.warning(
                    "Gemini rate limited, retrying",
                    extra={"attempt": attempt + 1, "wait_seconds": wait, "error": str(e)[:200]},
                )
                time.sleep(wait)
                continue

            # Server error (500, 503) — retry
            if "500" in str(e) or "503" in str(e) or "unavailable" in error_str:
                wait = INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ** attempt)
                logger.warning(
                    "Gemini server error, retrying",
                    extra={"attempt": attempt + 1, "wait_seconds": wait},
                )
                time.sleep(wait)
                continue

            # Non-retryable error — fail immediately
            logger.exception("Gemini non-retryable error", extra={"error": str(e)[:300]})
            raise

    # All retries exhausted
    logger.error("Gemini call failed after all retries", extra={"retries": MAX_RETRIES})
    raise last_error or RuntimeError("Gemini call failed")

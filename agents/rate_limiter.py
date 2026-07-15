"""
Rate limiter for ad platform APIs.

Meta Ads API: 200 requests per hour per user, burst of 100
Google Ads API: 15,000 requests per day per developer token, 5,000 per hour
"""

import asyncio
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    def __init__(self, status_code: int, message: str, retry_after: float = 0):
        self.status_code = status_code
        self.retry_after = retry_after
        super().__init__(message)


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float, name: str = ""):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self.name = name

    async def acquire(self, tokens: int = 1) -> float:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return 0.0
        wait_time = (tokens - self.tokens) / self.refill_rate
        logger.debug(f"[{self.name}] Waiting {wait_time:.1f}s for {tokens} tokens")
        await asyncio.sleep(wait_time)
        self._refill()
        self.tokens -= tokens
        return wait_time

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now


class PlatformRateLimiter:
    """
    Manages per-platform rate limits with awareness of asymmetric limits.
    Meta has per-user limits, Google has per-developer-token limits.
    """

    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}

        # Meta: 200 req/hr per user, burst 100
        self._buckets["meta"] = TokenBucket(
            capacity=100,
            refill_rate=200 / 3600,
            name="meta",
        )

        # Google: 5000 req/hr per dev token
        self._buckets["google"] = TokenBucket(
            capacity=500,
            refill_rate=5000 / 3600,
            name="google",
        )

        # Convex: no hard limit but be respectful
        self._buckets["convex"] = TokenBucket(
            capacity=50,
            refill_rate=200 / 60,
            name="convex",
        )

    async def wait(self, platform: str, tokens: int = 1):
        bucket = self._buckets.get(platform)
        if not bucket:
            return
        await bucket.acquire(tokens)


class RetryHandler:
    """
    Configurable retry with exponential backoff + jitter.
    Respects Retry-After headers from 429 responses.
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def execute(
        self,
        fn,
        retryable_statuses: set[int] = {429, 500, 502, 503, 504},
    ):
        import random

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return await fn()
            except Exception as e:
                last_error = e
                status = getattr(e, "status_code", 0) or getattr(e, "response", None) and getattr(e.response, "status_code", 0)

                if status not in retryable_statuses and status != 0:
                    raise

                if attempt >= self.max_retries:
                    logger.error(f"All {self.max_retries} retries exhausted: {e}")
                    raise

                delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                retry_after = getattr(e, "retry_after", None)
                if retry_after:
                    delay = max(delay, float(retry_after))

                logger.warning(f"Retry {attempt + 1}/{self.max_retries} after {delay:.1f}s (status={status})")
                await asyncio.sleep(delay)

        raise last_error

"""
Tests for rate limiter with intentional failure scenarios:
- Token bucket acquisition timing
- Multiple concurrent acquires
- Rate limit error handling
"""

import asyncio
import pytest

from agents.rate_limiter import TokenBucket, PlatformRateLimiter, RateLimitError


class TestTokenBucket:
    def test_initial_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=1, name="test")
        assert bucket.tokens == 10

    @pytest.mark.asyncio
    async def test_acquire_reduces_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=100, name="test")
        await bucket.acquire(3)
        assert bucket.tokens == 7

    @pytest.mark.asyncio
    async def test_acquire_waits_when_empty(self):
        bucket = TokenBucket(capacity=2, refill_rate=10, name="test")
        await bucket.acquire(2)
        start = asyncio.get_running_loop().time()
        await bucket.acquire(1)
        elapsed = asyncio.get_running_loop().time() - start
        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_refill_over_time(self):
        bucket = TokenBucket(capacity=5, refill_rate=10, name="test")
        await bucket.acquire(5)
        wait = await bucket.acquire(1)
        assert wait > 0


class TestPlatformRateLimiter:
    @pytest.mark.asyncio
    async def test_meta_limiter_exists(self):
        limiter = PlatformRateLimiter()
        await limiter.wait("meta")
        # Should not raise

    @pytest.mark.asyncio
    async def test_unknown_platform_does_not_block(self):
        limiter = PlatformRateLimiter()
        await limiter.wait("nonexistent")
        # Should not raise


class TestRateLimitError:
    def test_error_attributes(self):
        err = RateLimitError(status_code=429, message="Too many requests", retry_after=30.0)
        assert err.status_code == 429
        assert err.retry_after == 30.0
        assert "Too many requests" in str(err)

    def test_default_retry_after(self):
        err = RateLimitError(status_code=429, message="Too many requests")
        assert err.retry_after == 0

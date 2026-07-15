"""
Researcher Agent: Fetches campaign data from Meta/Google Ads APIs.
Handles rate limits, token refresh, API timeouts with full audit logging.

Intentional failure scenarios this handles:
1. Rate limit (429) → exponential backoff + Retry-After respect
2. Token expiry (401) → refresh token flow
3. API timeout → retry with timeout configuration
4. Empty response → graceful empty result, no crash
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any, Optional

import httpx

from .rate_limiter import PlatformRateLimiter, RetryHandler, RateLimitError

logger = logging.getLogger(__name__)


class TokenExpiredError(Exception):
    def __init__(self, platform: str):
        self.platform = platform
        super().__init__(f"Token expired for {platform}")


class ResearcherAgent:
    def __init__(self):
        self.rate_limiter = PlatformRateLimiter()
        self.retry = RetryHandler(max_retries=3, base_delay=2.0)
        self.meta_token = os.getenv("META_ACCESS_TOKEN", "")
        self.google_token = os.getenv("GOOGLE_ACCESS_TOKEN", "")

    async def fetch_campaigns(self, client_config: dict) -> dict[str, Any]:
        """Fetch campaigns from all connected platforms for a client."""
        result = {
            "campaigns": [],
            "platforms_fetched": [],
            "platforms_failed": [],
            "errors": [],
            "metrics": {"total_api_calls": 0, "rate_limits_hit": 0, "tokens_refreshed": 0},
        }

        tasks = []

        meta_config = client_config.get("platformConnections", {}).get("meta")
        if meta_config:
            tasks.append(self._fetch_meta_campaigns(meta_config, result))

        google_config = client_config.get("platformConnections", {}).get("google")
        if google_config:
            tasks.append(self._fetch_google_campaigns(google_config, result))

        if tasks:
            await asyncio.gather(*tasks)

        return result

    async def _fetch_meta_campaigns(self, config: dict, result: dict):
        platform_config = {**config, "accessToken": self.meta_token}
        ad_account_id = config.get("adAccountId", "")
        if not ad_account_id:
            result["errors"].append("Meta: no adAccountId configured")
            result["platforms_failed"].append("meta")
            return

        try:
            campaigns = await self._call_meta_api(ad_account_id, platform_config)
            result["campaigns"].extend(campaigns)
            result["platforms_fetched"].append("meta")
            result["metrics"]["total_api_calls"] += 1
        except TokenExpiredError:
            logger.info("Meta token expired, attempting refresh")
            try:
                await self._refresh_meta_token(config)
                result["metrics"]["tokens_refreshed"] += 1
                campaigns = await self._call_meta_api(ad_account_id, platform_config)
                result["campaigns"].extend(campaigns)
                result["platforms_fetched"].append("meta")
            except Exception as e:
                result["errors"].append(f"Meta: {e}")
                result["platforms_failed"].append("meta")
        except RateLimitError as e:
            result["metrics"]["rate_limits_hit"] += 1
            result["errors"].append(f"Meta rate limited (retry after {e.retry_after}s)")
            result["platforms_failed"].append("meta")
        except Exception as e:
            result["errors"].append(f"Meta: {e}")
            result["platforms_failed"].append("meta")

    async def _call_meta_api(self, ad_account_id: str, config: dict) -> list[dict]:
        async def _do_fetch():
            await self.rate_limiter.wait("meta")
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.get(
                    f"https://graph.facebook.com/v18.0/act_{ad_account_id}/campaigns",
                    params={
                        "fields": "id,name,status,daily_budget,spend,impressions,clicks,conversions,actions,ctr,cpc",
                        "access_token": config.get("accessToken", self.meta_token),
                        "limit": 100,
                    },
                )
                if resp.status_code == 401:
                    raise TokenExpiredError("meta")
                if resp.status_code == 429:
                    raise RateLimitError(
                        status_code=429,
                        message="Meta rate limit",
                        retry_after=float(resp.headers.get("Retry-After", 10)),
                    )
                resp.raise_for_status()
                data = resp.json()
                return [
                    {
                        "id": c["id"],
                        "platform": "meta",
                        "name": c.get("name", ""),
                        "status": c.get("status", "UNKNOWN"),
                        "dailyBudget": float(c.get("daily_budget", 0)) / 100,
                        "spend": float(c.get("spend", 0)) / 100,
                        "impressions": int(c.get("impressions", 0)),
                        "clicks": int(c.get("clicks", 0)),
                        "conversions": int(c.get("conversions", 0)),
                        "revenue": self._extract_revenue(c.get("actions", [])),
                        "ctr": float(c.get("ctr", 0)) / 100,
                        "cpc": float(c.get("cpc", 0)) / 100,
                    }
                    for c in data.get("data", [])
                ]

        return await self.retry.execute(_do_fetch)

    async def _fetch_google_campaigns(self, config: dict, result: dict):
        customer_id = config.get("customerId", "")
        if not customer_id:
            result["errors"].append("Google: no customerId configured")
            result["platforms_failed"].append("google")
            return

        try:
            campaigns = await self._call_google_api(customer_id)
            result["campaigns"].extend(campaigns)
            result["platforms_fetched"].append("google")
            result["metrics"]["total_api_calls"] += 1
        except TokenExpiredError:
            logger.info("Google token expired, attempting refresh")
            try:
                await self._refresh_google_token(config)
                result["metrics"]["tokens_refreshed"] += 1
                campaigns = await self._call_google_api(customer_id)
                result["campaigns"].extend(campaigns)
                result["platforms_fetched"].append("google")
            except Exception as e:
                result["errors"].append(f"Google: {e}")
                result["platforms_failed"].append("google")
        except Exception as e:
            result["errors"].append(f"Google: {e}")
            result["platforms_failed"].append("google")

    async def _call_google_api(self, customer_id: str) -> list[dict]:
        async def _do_fetch():
            await self.rate_limiter.wait("google")
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"https://googleads.googleapis.com/v18/customers/{customer_id}/googleAds:search",
                    headers={
                        "Authorization": f"Bearer {self.google_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": """
                            SELECT campaign.id, campaign.name, campaign.status,
                                   campaign.optimization_score,
                                   metrics.impressions, metrics.clicks, metrics.conversions,
                                   metrics.cost_micros, metrics.conversions_value
                            FROM campaign
                            WHERE campaign.status != 'REMOVED'
                        """
                    },
                )
                if resp.status_code == 401:
                    raise TokenExpiredError("google")
                if resp.status_code == 429:
                    raise RateLimitError(
                        status_code=429,
                        message="Google rate limit",
                        retry_after=float(resp.headers.get("Retry-After", 60)),
                    )
                resp.raise_for_status()
                data = resp.json()
                return [
                    {
                        "id": row["campaign"]["id"],
                        "platform": "google",
                        "name": row["campaign"].get("name", ""),
                        "status": row["campaign"].get("status", "UNKNOWN"),
                        "dailyBudget": 0,
                        "spend": float(row["metrics"].get("costMicros", 0)) / 1_000_000,
                        "impressions": int(row["metrics"].get("impressions", 0)),
                        "clicks": int(row["metrics"].get("clicks", 0)),
                        "conversions": int(row["metrics"].get("conversions", 0)),
                        "revenue": float(row["metrics"].get("conversionsValue", 0)),
                        "ctr": 0.0,
                        "cpc": 0.0,
                    }
                    for row in data.get("results", [])
                ]

        return await self.retry.execute(_do_fetch)

    async def _refresh_meta_token(self, config: dict) -> str:
        """Exchange short-lived token for long-lived token."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": os.getenv("META_APP_ID", ""),
                    "client_secret": os.getenv("META_APP_SECRET", ""),
                    "fb_exchange_token": config.get("accessToken", ""),
                },
            )
            resp.raise_for_status()
            new_token = resp.json().get("access_token", "")
            self.meta_token = new_token
            logger.info("Meta token refreshed successfully")
            return new_token

    async def _refresh_google_token(self, config: dict) -> str:
        """Exchange refresh token for new access token."""
        refresh_token = config.get("refreshToken", "")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            new_token = resp.json().get("access_token", "")
            self.google_token = new_token
            logger.info("Google token refreshed successfully")
            return new_token

    def _extract_revenue(self, actions: list[dict]) -> float:
        if not actions:
            return 0.0
        for action in actions:
            if action.get("action_type") in ("purchase", "offsite_conversion.fb_pixel_purchase"):
                return float(action.get("value", 0))
        return 0.0

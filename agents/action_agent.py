"""
Action agent: executes approved budget changes via Meta/Google Ads APIs.
Runs only after human approval for high-impact changes.
"""

import logging
from typing import Any

import httpx

from .rate_limiter import PlatformRateLimiter, RateLimitError, RetryHandler

logger = logging.getLogger(__name__)


class ActionExecutionError(Exception):
    pass


class ActionAgent:
    def __init__(self, meta_token: str, google_token: str = ""):
        self.meta_token = meta_token
        self.google_token = google_token
        self.rate_limiter = PlatformRateLimiter()
        self.retry = RetryHandler(max_retries=3)

    async def execute_budget_change(
        self,
        platform: str,
        campaign_id: str,
        new_budget: float,
    ) -> dict[str, Any]:
        if platform == "meta":
            return await self._execute_meta_budget(campaign_id, new_budget)
        elif platform == "google":
            return await self._execute_google_budget(campaign_id, new_budget)
        else:
            raise ActionExecutionError(f"Unknown platform: {platform}")

    async def _execute_meta_budget(self, campaign_id: str, new_budget: float) -> dict[str, Any]:
        async def _call():
            await self.rate_limiter.wait("meta")
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://graph.facebook.com/v18.0/{campaign_id}",
                    params={
                        "daily_budget": int(new_budget * 100),
                        "access_token": self.meta_token,
                    },
                )
                if resp.status_code == 429:
                    raise RateLimitError(
                        status_code=429,
                        message="Meta rate limit exceeded",
                        retry_after=float(resp.headers.get("Retry-After", 10)),
                    )
                resp.raise_for_status()
                return {"success": True, "platform": "meta", "campaign_id": campaign_id, "new_budget": new_budget}

        return await self.retry.execute(_call)

    async def _execute_google_budget(self, campaign_id: str, new_budget: float) -> dict[str, Any]:
        async def _call():
            await self.rate_limiter.wait("google")
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://googleads.googleapis.com/v18/customers/-/campaigns:mutate",
                    headers={
                        "Authorization": f"Bearer {self.google_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "operations": [{
                            "updateMask": "campaign_budget.amount_micros",
                            "update": {
                                "resourceName": f"customers/-/campaigns/{campaign_id}",
                                "campaignBudget": {
                                    "amountMicros": int(new_budget * 1_000_000),
                                },
                            },
                        }],
                    },
                )
                if resp.status_code == 429:
                    raise RateLimitError(
                        status_code=429,
                        message="Google rate limit exceeded",
                        retry_after=float(resp.headers.get("Retry-After", 60)),
                    )
                resp.raise_for_status()
                return {"success": True, "platform": "google", "campaign_id": campaign_id, "new_budget": new_budget}

        return await self.retry.execute(_call)

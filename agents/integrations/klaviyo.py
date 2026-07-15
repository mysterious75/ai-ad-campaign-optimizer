"""
Klaviyo API integration: fetches email marketing metrics,
campaign performance, and revenue attribution.
Uses Klaviyo REST API v2024-10-15 with private API key.
"""

import os
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class KlaviyoError(Exception):
    pass


class KlaviyoClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("KLAVIYO_API_KEY", "")
        self.base_url = "https://a.klaviyo.com/api"
        self.api_version = "2024-10-15"

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        if not self.api_key:
            raise KlaviyoError("Klaviyo API key not configured")
        headers = {
            "Authorization": f"Klaviyo-API-Key {self.api_key}",
            "Accept": "application/json",
            "revision": self.api_version,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.base_url}/{path}", headers=headers, params=params)
            if resp.status_code == 401:
                raise KlaviyoError("Invalid Klaviyo API key")
            if resp.status_code == 429:
                raise KlaviyoError("Klaviyo rate limit hit")
            resp.raise_for_status()
            return resp.json()

    async def fetch_campaigns(self, days_back: int = 30) -> list[dict]:
        data = await self._get("campaigns", {
            "filter": f"less-than(updated_at,{days_back})",
            "page[size]": 50,
            "sort": "-updated_at",
        })
        return [
            {
                "id": c["id"],
                "name": c["attributes"].get("name", ""),
                "status": c["attributes"].get("status", ""),
                "channel": c["attributes"].get("channel", ""),
                "created_at": c["attributes"].get("created_at", ""),
                "updated_at": c["attributes"].get("updated_at", ""),
            }
            for c in data.get("data", [])
        ]

    async def fetch_metrics(self, days_back: int = 30) -> dict[str, Any]:
        data = await self._get("metrics", {"page[size]": 100})
        return {"metrics": [m["attributes"] for m in data.get("data", [])]}

    async def fetch_revenue_attribution(self, days_back: int = 30) -> list[dict]:
        data = await self._get("events", {
            "filter": f"greater-than(datetime,{days_back})",
            "page[size]": 100,
        })
        return [
            {
                "id": e["id"],
                "type": e["attributes"].get("event_type", ""),
                "timestamp": e["attributes"].get("datetime", ""),
                "properties": e["attributes"].get("properties", {}),
            }
            for e in data.get("data", [])
        ]

    async def health_check(self) -> bool:
        try:
            await self._get("metrics", {"page[size]": 1})
            return True
        except Exception:
            return False

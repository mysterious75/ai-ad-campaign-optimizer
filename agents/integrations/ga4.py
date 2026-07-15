"""
Google Analytics 4 (GA4) Data API integration.
Fetches traffic sources, conversion events, and campaign attribution.
Uses Google OAuth 2.0 service account or access token.
"""

import os
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class GA4Error(Exception):
    pass


class GA4Client:
    def __init__(self, property_id: str = "", access_token: str = ""):
        self.property_id = property_id or os.getenv("GA4_PROPERTY_ID", "")
        self.access_token = access_token or os.getenv("GOOGLE_ACCESS_TOKEN", "")
        self.base_url = "https://analyticsdata.googleapis.com/v1beta"

    async def run_report(self, metrics: list[str], dimensions: list[str], days_back: int = 30) -> dict[str, Any]:
        if not self.property_id:
            raise GA4Error("GA4 property ID not configured")
        if not self.access_token:
            raise GA4Error("GA4 access token not configured")

        url = f"{self.base_url}/properties/{self.property_id}:runReport"
        body = {
            "dateRanges": [{"startDate": f"{days_back}daysAgo", "endDate": "today"}],
            "metrics": [{"name": m} for m in metrics],
            "dimensions": [{"name": d} for d in dimensions],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            if resp.status_code == 401:
                raise GA4Error("GA4 token expired or invalid")
            if resp.status_code == 403:
                raise GA4Error("GA4 access denied -- check property permissions")
            resp.raise_for_status()
            return resp.json()

    async def fetch_campaign_attribution(self, days_back: int = 30) -> list[dict[str, Any]]:
        result = await self.run_report(
            metrics=["totalUsers", "newUsers", "sessions", "conversions", "totalRevenue"],
            dimensions=["sessionCampaignName", "sessionSource", "sessionMedium"],
            days_back=days_back,
        )
        rows = []
        for row in result.get("rows", []):
            dims = [d["value"] for d in row.get("dimensionValues", [])]
            vals = [v["value"] for v in row.get("metricValues", [])]
            rows.append({
                "campaign": dims[0] if len(dims) > 0 else "(not set)",
                "source": dims[1] if len(dims) > 1 else "",
                "medium": dims[2] if len(dims) > 2 else "",
                "users": int(vals[0]) if len(vals) > 0 else 0,
                "sessions": int(vals[2]) if len(vals) > 2 else 0,
                "conversions": int(vals[3]) if len(vals) > 3 else 0,
                "revenue": float(vals[4]) if len(vals) > 4 else 0.0,
            })
        return rows

    async def health_check(self) -> bool:
        try:
            await self.run_report(metrics=["sessions"], dimensions=["date"], days_back=1)
            return True
        except Exception:
            return False

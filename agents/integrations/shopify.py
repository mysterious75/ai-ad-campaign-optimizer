"""
Shopify integration: fetches product revenue, order data, and campaign attribution.
Uses Shopify REST Admin API with per-store access tokens.
"""

import os
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class ShopifyError(Exception):
    pass


class ShopifyClient:
    def __init__(self, store_domain: str = "", access_token: str = ""):
        self.store_domain = store_domain or os.getenv("SHOPIFY_STORE_DOMAIN", "")
        self.access_token = access_token or os.getenv("SHOPIFY_ACCESS_TOKEN", "")
        self.base_url = f"https://{self.store_domain}/admin/api/2024-07"

    async def fetch_orders(self, since_id: Optional[str] = None, limit: int = 50) -> list[dict]:
        params = {"limit": min(limit, 250), "status": "any", "fields": "id,created_at,total_price,subtotal_price,total_discounts,note,customer"}
        if since_id:
            params["since_id"] = since_id

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.base_url}/orders.json",
                headers={"X-Shopify-Access-Token": self.access_token},
                params=params,
            )
            if resp.status_code == 401:
                raise ShopifyError("Invalid Shopify access token")
            if resp.status_code == 429:
                raise ShopifyError("Shopify rate limit hit -- retry after " + resp.headers.get("Retry-After", "10s"))
            resp.raise_for_status()
            return resp.json().get("orders", [])

    async def fetch_revenue(self, days_back: int = 30) -> dict[str, Any]:
        orders = await self.fetch_orders(limit=250)
        total_revenue = sum(float(o.get("total_price", 0)) for o in orders)
        total_orders = len(orders)
        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "average_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
            "orders": orders[:20],
        }

    async def health_check(self) -> bool:
        try:
            await self.fetch_orders(limit=1)
            return True
        except Exception:
            return False

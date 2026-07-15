"""
Resend email integration: sends alerts, reports, and approval notifications.
Uses Resend API (resend.com) with API key.
"""

import os
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class ResendError(Exception):
    pass


class EmailClient:
    def __init__(self, api_key: str = "", from_address: str = ""):
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "")
        self.from_address = from_address or os.getenv("RESEND_FROM_ADDRESS", "ai-agent@yourdomain.com")
        self.base_url = "https://api.resend.com"

    async def send(self, to: str, subject: str, html: str) -> dict[str, Any]:
        if not self.api_key:
            raise ResendError("Resend API key not configured")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/emails",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self.from_address,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
            )
            if resp.status_code == 401:
                raise ResendError("Invalid Resend API key")
            resp.raise_for_status()
            return resp.json()

    async def send_alert(self, to: str, client_name: str, severity: str, message: str) -> dict:
        html = f"""
        <h2>Ad Optimizer Alert - {client_name}</h2>
        <p><strong>Severity:</strong> {severity}</p>
        <p><strong>Message:</strong> {message}</p>
        <hr>
        <p style="color:#888;font-size:12px">Sent by AI Campaign Optimizer</p>
        """
        return await self.send(to, f"[{severity.upper()}] Ad Optimizer Alert - {client_name}", html)

    async def send_report(self, to: str, client_name: str, summary: dict) -> dict:
        high = len(summary.get("high_priority_findings", []))
        total = summary.get("findings_summary", {}).get("total", 0)
        html = f"""
        <h2>Ad Optimizer Report - {client_name}</h2>
        <p>Analysis complete. Found <strong>{total}</strong> issues ({high} high priority).</p>
        <hr>
        <p style="color:#888;font-size:12px">View full report in your dashboard.</p>
        <p style="color:#888;font-size:12px">Sent by AI Campaign Optimizer</p>
        """
        return await self.send(to, f"Ad Optimizer Report - {client_name}", html)

    async def send_approval_request(self, to: str, client_name: str, action_type: str, details: str, impact: float) -> dict:
        html = f"""
        <h2>Approval Required - {client_name}</h2>
        <p><strong>Action:</strong> {action_type}</p>
        <p><strong>Details:</strong> {details}</p>
        <p><strong>Budget Impact:</strong> ${impact:.2f}</p>
        <hr>
        <p style="color:#888;font-size:12px">Review and approve/reject in your dashboard.</p>
        """
        return await self.send(to, f"Approval Required - {client_name}", html)

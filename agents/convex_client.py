"""
Convex data client for Python agent scripts.
Reads/writes campaign data, agent runs, and audit logs to Convex.
"""

import os
import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class ConvexClient:
    """
    Lightweight Convex HTTP client for Python agents.
    Uses Convex's HTTP action/mutation endpoints.
    """

    def __init__(self):
        self.deployment_url = os.getenv("CONVEX_DEPLOYMENT_URL")
        self.access_key = os.getenv("CONVEX_ACCESS_KEY")
        if not self.deployment_url:
            raise ValueError("CONVEX_DEPLOYMENT_URL is required")

    async def mutation(self, name: str, args: dict[str, Any]) -> Any:
        return await self._call("mutation", name, args)

    async def query(self, name: str, args: dict[str, Any]) -> Any:
        return await self._call("query", name, args)

    async def action(self, name: str, args: dict[str, Any]) -> Any:
        return await self._call("action", name, args)

    async def _call(self, call_type: str, name: str, args: dict[str, Any]) -> Any:
        url = f"{self.deployment_url}/api/{call_type}"
        headers = {"Content-Type": "application/json"}
        if self.access_key:
            headers["Authorization"] = f"Bearer {self.access_key}"

        body = {
            "path": name,
            "args": args,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Convex {call_type} '{name}' failed: {e.response.status_code} {e.response.text}")
                raise
            except httpx.TimeoutException:
                logger.error(f"Convex {call_type} '{name}' timed out")
                raise

    # -- Convenience wrappers matching Convex functions --

    async def get_campaigns(self, client_id: str) -> list[dict]:
        return await self.query("campaigns:list", {"clientId": client_id})

    async def upsert_campaign(self, **data) -> str:
        return await self.mutation("campaigns:upsert", data)

    async def create_agent_run(self, client_id: str, trigger: str = "schedule") -> str:
        return await self.mutation("agentRuns:create", {
            "clientId": client_id,
            "trigger": trigger,
        })

    async def update_run_status(self, run_id: str, status: str, **extra) -> None:
        await self.mutation("agentRuns:updateStatus", {
            "runId": run_id,
            "status": status,
            **extra,
        })

    async def append_log(self, run_id: str, client_id: str, agent: str, msg_type: str, payload: dict) -> str:
        return await self.mutation("agentLogs:append", {
            "runId": run_id,
            "clientId": client_id,
            "agent": agent,
            "msgType": msg_type,
            "payload": payload,
        })

    async def create_approval(self, run_id: str, client_id: str, action_type: str, details: str, impact: float) -> str:
        return await self.mutation("approvals:create", {
            "runId": run_id,
            "clientId": client_id,
            "actionType": action_type,
            "details": details,
            "impact": impact,
        })

    # -- Onboarding helpers --

    async def get_or_create_onboarding(self, client_id: str) -> str:
        return await self.mutation("onboarding:getOrCreate", {"clientId": client_id})

    async def update_onboarding(self, client_id: str, step: str, updates: dict) -> None:
        await self.mutation("onboarding:updateStep", {
            "clientId": client_id,
            "step": step,
            "updates": updates,
        })

    # -- Audit trail helper --

    async def append_audit_event(self, client_id: str, action: str, actor: str, resource: str, details: dict) -> str:
        return await self.append_log(
            run_id="audit",
            client_id=client_id,
            agent="audit",
            msg_type="audit_event",
            payload={
                "action": action,
                "actor": actor,
                "resource": resource,
                "details": details,
                "timestamp": __import__("time").time(),
            },
        )

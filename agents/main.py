"""
Cron entrypoint for the multi-agent pipeline.

Crontab (hourly):
    0 * * * * cd /app && python -m agents.main

Runs the full 5-agent pipeline for every active client.
Each client runs in isolation — one failure doesn't block others.
"""

import asyncio
import json
import logging
import os
import sys

from dotenv import load_dotenv

from .convex_client import ConvexClient
from .supervisor import Supervisor
from .rate_limiter import PlatformRateLimiter

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("main")


async def main():
    convex = ConvexClient()
    supervisor = Supervisor(convex)
    rate_limiter = PlatformRateLimiter()

    logger.info("=== Multi-Agent Pipeline Start ===")

    try:
        active_clients = await convex.query("clients:listActive", {})
    except Exception as e:
        logger.error(f"Failed to fetch active clients: {e}")
        sys.exit(1)

    if not active_clients:
        logger.info("No active clients found")
        return

    logger.info(f"Processing {len(active_clients)} client(s)")

    results = []
    for client in active_clients:
        client_id = client["_id"]
        client_name = client.get("name", client_id)

        try:
            await rate_limiter.wait("convex")
            logger.info(f"[{client_name}] Starting pipeline")
            result = await supervisor.run_for_client(client_id, client)
            results.append({"client_id": client_id, "client_name": client_name, **result})

            findings = result.get("findings", 0)
            actions = result.get("actions_taken", 0)
            status = result.get("status", "unknown")
            logger.info(f"[{client_name}] {status} | {findings} findings, {actions} actions")

        except Exception as e:
            logger.error(f"[{client_name}] Pipeline crashed: {e}")
            results.append({
                "client_id": client_id,
                "client_name": client_name,
                "status": "crashed",
                "error": str(e),
            })

    summary = {
        "total": len(results),
        "completed": sum(1 for r in results if r.get("status") == "completed"),
        "failed": sum(1 for r in results if r.get("status") == "failed"),
        "crashed": sum(1 for r in results if r.get("status") == "crashed"),
    }
    logger.info(f"=== Pipeline Complete: {json.dumps(summary)} ===")

    for r in results:
        if r.get("status") in ("failed", "crashed"):
            logger.error(f"  {r['client_name']}: {r.get('error', 'unknown')}")


if __name__ == "__main__":
    asyncio.run(main())

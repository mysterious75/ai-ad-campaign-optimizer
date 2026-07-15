"""
Report Agent: Generates the final structured summary after all agents complete.
Writes results to Convex for the frontend to display in real-time.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ReportAgent:
    def __init__(self, convex_client):
        self.convex = convex_client

    async def generate_and_save(
        self,
        run_id: str,
        client_id: str,
        researcher_result: dict[str, Any],
        planner_result: dict[str, Any],
        analyst_findings: list[dict[str, Any]],
        validator_result: dict[str, Any],
        execution_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        summary = self._build_summary(
            researcher_result, planner_result, analyst_findings,
            validator_result, execution_results,
        )

        await self.convex.append_log(run_id, client_id, "report_agent", "summary", summary)

        if validator_result.get("warnings"):
            await self.convex.append_log(
                run_id, client_id, "report_agent", "warnings",
                {"warnings": validator_result["warnings"]},
            )

        if execution_results:
            await self.convex.append_log(
                run_id, client_id, "report_agent", "execution_results",
                {"results": execution_results},
            )

        return summary

    def _build_summary(
        self,
        researcher: dict[str, Any],
        planner: dict[str, Any],
        findings: list[dict[str, Any]],
        validator: dict[str, Any],
        execution: list[dict[str, Any]],
    ) -> dict[str, Any]:
        platforms = researcher.get("platforms_fetched", [])
        errors = researcher.get("errors", [])
        metrics = researcher.get("metrics", {})

        high_count = sum(1 for f in findings if f.get("severity") == "high")
        medium_count = sum(1 for f in findings if f.get("severity") == "medium")
        low_count = sum(1 for f in findings if f.get("severity") == "low")

        executed = sum(1 for e in execution if e.get("success"))
        failed = sum(1 for e in execution if not e.get("success"))

        validation_warnings = validator.get("warnings", [])
        validation_passed = validator.get("valid", True)

        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "overview": {
                "platforms_analyzed": platforms,
                "platforms_with_errors": researcher.get("platforms_failed", []),
                "total_campaigns": planner.get("total_campaigns", 0),
                "total_spend": planner.get("total_spend", 0),
                "overall_roas": planner.get("overall_roas", 0),
            },
            "findings_summary": {
                "total": len(findings),
                "high_severity": high_count,
                "medium_severity": medium_count,
                "low_severity": low_count,
                "validation_passed": validation_passed,
                "validation_warnings": validation_warnings,
            },
            "execution_summary": {
                "total": len(execution),
                "successful": executed,
                "failed": failed,
            },
            "api_metrics": {
                "total_calls": metrics.get("total_api_calls", 0),
                "rate_limits_hit": metrics.get("rate_limits_hit", 0),
                "tokens_refreshed": metrics.get("tokens_refreshed", 0),
            },
            "errors": errors,
            "high_priority_findings": [f for f in findings if f.get("severity") == "high"],
        }

        return summary

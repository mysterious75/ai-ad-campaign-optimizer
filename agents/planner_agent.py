"""
Planner Agent: Decides what analysis to run and sets priorities.
No LLM call needed — uses deterministic rules to create a plan.
This avoids unnecessary token spend for planning decisions.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PlannerAgent:
    def create_plan(self, researcher_result: dict[str, Any]) -> dict[str, Any]:
        campaigns = researcher_result.get("campaigns", [])
        platforms_failed = researcher_result.get("platforms_failed", [])
        errors = researcher_result.get("errors", [])
        metrics = researcher_result.get("metrics", {})

        if not campaigns:
            return {
                "should_proceed": False,
                "reason": "No campaigns fetched from any platform",
                "plan": [],
                "anomalies": errors,
            }

        plan = []
        total_spend = sum(c.get("spend", 0) for c in campaigns)
        total_revenue = sum(c.get("revenue", 0) for c in campaigns)
        overall_roas = total_revenue / total_spend if total_spend > 0 else 0

        plan.append({
            "analysis_type": "roas_analysis",
            "target": "all_campaigns",
            "reason": f"Overall ROAS is {overall_roas:.2f}",
            "threshold": 1.5,
            "priority": "high" if overall_roas < 1.5 else "medium",
        })

        cheap_campaigns = [c for c in campaigns if c.get("spend", 0) < 100]
        if cheap_campaigns:
            plan.append({
                "analysis_type": "budget_utilization",
                "target": [c["id"] for c in cheap_campaigns],
                "reason": f"{len(cheap_campaigns)} campaigns with low spend",
                "threshold": 100,
                "priority": "low",
            })

        high_spend_campaigns = [c for c in campaigns if c.get("spend", 0) > 1000]
        if high_spend_campaigns:
            plan.append({
                "analysis_type": "high_spend_review",
                "target": [c["id"] for c in high_spend_campaigns],
                "reason": f"{len(high_spend_campaigns)} campaigns with >$1k spend",
                "threshold": 1000,
                "priority": "high",
            })

        plan.append({
            "analysis_type": "anomaly_detection",
            "target": "all_campaigns",
            "reason": "Routine anomaly scan across all campaigns",
            "threshold": None,
            "priority": "medium",
        })

        if platforms_failed:
            plan.append({
                "analysis_type": "platform_error_review",
                "target": platforms_failed,
                "reason": f"Failed to fetch data from: {', '.join(platforms_failed)}",
                "details": errors,
                "priority": "high",
            })

        return {
            "should_proceed": True,
            "total_campaigns": len(campaigns),
            "total_spend": total_spend,
            "total_revenue": total_revenue,
            "overall_roas": round(overall_roas, 2),
            "plan": plan,
            "anomalies": errors,
            "metrics": metrics,
        }

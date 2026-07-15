"""
Tests for the Planner Agent — deterministic rule-based planning.
"""

import pytest

from agents.planner_agent import PlannerAgent


class TestPlannerAgent:
    def setup_method(self):
        self.planner = PlannerAgent()

    def test_empty_campaigns_returns_no_plan(self):
        result = self.planner.create_plan({"campaigns": [], "platforms_failed": [], "errors": []})
        assert result["should_proceed"] is False

    def test_healthy_campaigns_create_plan(self):
        campaigns = [
            {"id": "c1", "spend": 500, "revenue": 1500},
            {"id": "c2", "spend": 300, "revenue": 600},
        ]
        result = self.planner.create_plan({
            "campaigns": campaigns,
            "platforms_failed": [],
            "errors": [],
            "metrics": {},
        })
        assert result["should_proceed"] is True
        assert result["total_campaigns"] == 2
        assert len(result["plan"]) >= 2  # roas + anomaly at minimum
        assert result["overall_roas"] > 0

    def test_low_roas_triggers_high_priority(self):
        campaigns = [
            {"id": "c1", "spend": 1000, "revenue": 500},
        ]
        result = self.planner.create_plan({
            "campaigns": campaigns,
            "platforms_failed": [],
            "errors": [],
            "metrics": {},
        })
        roas_plan = [p for p in result["plan"] if p["analysis_type"] == "roas_analysis"]
        assert roas_plan[0]["priority"] == "high"

    def test_platform_failures_added_to_plan(self):
        result = self.planner.create_plan({
            "campaigns": [{"id": "c1", "spend": 100, "revenue": 200}],
            "platforms_failed": ["google"],
            "errors": ["Google: token expired"],
            "metrics": {},
        })
        error_plans = [p for p in result["plan"] if p["analysis_type"] == "platform_error_review"]
        assert len(error_plans) == 1
        assert "google" in error_plans[0]["target"]

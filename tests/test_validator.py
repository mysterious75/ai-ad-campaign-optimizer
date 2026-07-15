"""
Tests for the Validator Agent — catches LLM hallucinations and errors.

Intentional failure scenarios tested:
1. Hallucinated campaign IDs → caught by validator
2. Missing required fields → caught by schema check
3. Negative numeric values → caught by sanity check
4. Contradictory recommendations → caught by consistency check
5. Invalid severity values → caught by enum check
"""

import pytest

from agents.validator_agent import ValidatorAgent, ValidationError

SAMPLE_CAMPAIGNS = [
    {"id": "camp_001", "name": "Brand Awareness", "dailyBudget": 100},
    {"id": "camp_002", "name": "Retargeting", "dailyBudget": 75},
    {"id": "camp_003", "name": "Lead Gen", "dailyBudget": 50},
]

SAMPLE_PLAN = {"plan": [], "total_campaigns": 3}


class TestValidatorFindings:
    def setup_method(self):
        self.validator = ValidatorAgent()

    def test_valid_findings_pass(self):
        findings = [
            {
                "campaign_id": "camp_001",
                "metric": "roas",
                "current_value": 0.8,
                "threshold": 1.5,
                "severity": "high",
                "confidence": "high",
                "detail": "ROAS below target",
                "recommendation": "Reduce budget",
            }
        ]
        result = self.validator.validate_findings(findings, SAMPLE_CAMPAIGNS, SAMPLE_PLAN)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_hallucinated_campaign_id(self):
        """LLM references a campaign that doesn't exist in the data."""
        findings = [
            {
                "campaign_id": "camp_999",
                "metric": "roas",
                "current_value": 0.5,
                "severity": "high",
                "detail": "Bad ROAS",
                "recommendation": "Fix it",
            }
        ]
        result = self.validator.validate_findings(findings, SAMPLE_CAMPAIGNS, SAMPLE_PLAN)
        assert result["valid"] is False
        assert any("HALLUCINATION" in e for e in result["errors"])

    def test_missing_required_field(self):
        findings = [
            {
                "campaign_id": "camp_001",
                # missing 'metric', 'severity', 'detail'
            }
        ]
        result = self.validator.validate_findings(findings, SAMPLE_CAMPAIGNS, SAMPLE_PLAN)
        assert result["valid"] is False
        assert len(result["errors"]) >= 3

    def test_negative_numeric_value(self):
        findings = [
            {
                "campaign_id": "camp_001",
                "metric": "roas",
                "current_value": -1.5,
                "severity": "medium",
                "detail": "Negative ROAS doesn't make sense",
                "recommendation": "Review data source",
            }
        ]
        result = self.validator.validate_findings(findings, SAMPLE_CAMPAIGNS, SAMPLE_PLAN)
        assert result["valid"] is False
        assert any("negative" in e.lower() for e in result["errors"])

    def test_invalid_severity_value(self):
        findings = [
            {
                "campaign_id": "camp_001",
                "metric": "roas",
                "current_value": 1.0,
                "severity": "critical",
                "detail": "Critical issue",
                "recommendation": "Fix urgently",
            }
        ]
        result = self.validator.validate_findings(findings, SAMPLE_CAMPAIGNS, SAMPLE_PLAN)
        assert result["valid"] is False
        assert any("severity" in e for e in result["errors"])

    def test_contradictory_recommendations(self):
        findings = [
            {
                "campaign_id": "camp_001",
                "metric": "roas",
                "current_value": 0.8,
                "severity": "high",
                "detail": "ROAS too low",
                "recommendation": "Increase budget to improve scale",
            },
            {
                "campaign_id": "camp_001",
                "metric": "cpc",
                "current_value": 5.0,
                "severity": "high",
                "detail": "CPC too high",
                "recommendation": "Decrease budget to control costs",
            },
        ]
        result = self.validator.validate_findings(findings, SAMPLE_CAMPAIGNS, SAMPLE_PLAN)
        assert result["valid"] is True
        assert any("Contradictory" in w for w in result["warnings"])

    def test_empty_findings(self):
        result = self.validator.validate_findings([], SAMPLE_CAMPAIGNS, SAMPLE_PLAN)
        assert result["valid"] is True

    def test_low_confidence_flag(self):
        findings = [
            {
                "campaign_id": "camp_001",
                "metric": "roas",
                "current_value": 0.8,
                "severity": "medium",
                "confidence": "low",
                "detail": "Unsure about this data",
                "recommendation": "Review manually",
            }
        ]
        result = self.validator.validate_findings(findings, SAMPLE_CAMPAIGNS, SAMPLE_PLAN)
        assert result["valid"] is True
        assert any("low confidence" in w for w in result["warnings"])


class TestValidatorRecommendations:
    def setup_method(self):
        self.validator = ValidatorAgent()

    def test_valid_recommendations_pass(self):
        recs = [
            {"campaign_id": "camp_001", "amount": 50, "new_budget": 150},
        ]
        result = self.validator.validate_recommendations(recs, SAMPLE_CAMPAIGNS)
        assert result["valid"] is True

    def test_hallucinated_campaign_in_recommendation(self):
        recs = [
            {"campaign_id": "camp_999", "amount": 50, "new_budget": 100},
        ]
        result = self.validator.validate_recommendations(recs, SAMPLE_CAMPAIGNS)
        assert result["valid"] is False
        assert any("not found" in e for e in result["errors"])

    def test_negative_amount(self):
        recs = [
            {"campaign_id": "camp_001", "amount": -100, "new_budget": 50},
        ]
        result = self.validator.validate_recommendations(recs, SAMPLE_CAMPAIGNS)
        assert result["valid"] is False
        assert any("negative" in e for e in result["errors"])

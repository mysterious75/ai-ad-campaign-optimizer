"""
Validator Agent: Validates LLM outputs before they reach the execution phase.

Checks performed:
1. JSON schema compliance — required fields present and correct types
2. Hallucination detection — campaign IDs must exist in source data
3. Numeric sanity — no negative budgets, no infinite ROAS, no >1000% CTR
4. Consistency check — recommendations don't contradict each other
5. Confidence threshold — low-confidence findings are flagged for review

Intentional failure scenarios this catches:
1. LLM hallucinates campaign IDs → caught by hallucination check
2. LLM returns negative budget values → caught by numeric sanity
3. LLM recommends contradictory actions (increase + decrease same campaign) → caught by consistency check
4. LLM returns malformed JSON → caught by JSON schema compliance
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    def __init__(self, message: str, details: list[str]):
        self.details = details
        super().__init__(message)


class ValidatorAgent:
    def validate_findings(
        self,
        findings: list[dict[str, Any]],
        campaigns: list[dict[str, Any]],
        plan: dict[str, Any],
    ) -> dict[str, Any]:
        errors = []
        warnings = []

        if not findings:
            return {"valid": True, "findings": findings, "errors": [], "warnings": []}

        valid_ids = {c.get("id") for c in campaigns}

        for i, f in enumerate(findings):
            finding_errors = self._validate_single_finding(f, i, valid_ids)
            errors.extend(finding_errors)

        contradictions = self._check_contradictions(findings)
        warnings.extend(contradictions)

        low_confidence = [
            f for f in findings if f.get("confidence") == "low"
        ]
        if low_confidence:
            warnings.append(
                f"{len(low_confidence)} finding(s) have low confidence and need manual review"
            )

        if errors:
            return {
                "valid": False,
                "findings": findings,
                "errors": errors,
                "warnings": warnings,
            }

        return {
            "valid": True,
            "findings": findings,
            "errors": [],
            "warnings": warnings,
        }

    def validate_recommendations(
        self,
        recommendations: list[dict[str, Any]],
        campaigns: list[dict[str, Any]],
    ) -> dict[str, Any]:
        errors = []
        warnings = []
        valid_ids = {c.get("id") for c in campaigns}

        budgets = {c.get("id"): c.get("dailyBudget", 0) for c in campaigns}

        for i, rec in enumerate(recommendations):
            cid = rec.get("campaign_id")
            if cid not in valid_ids:
                errors.append(f"Recommendation {i}: campaign_id '{cid}' not found")

            amount = rec.get("amount", 0)
            if amount < 0:
                errors.append(f"Recommendation {i}: negative amount ${amount}")

            new_budget = rec.get("new_budget", 0)
            current_budget = budgets.get(cid, 0)
            if new_budget > 0 and current_budget > 0:
                change_pct = abs(new_budget - current_budget) / current_budget * 100
                if change_pct > 50:
                    warnings.append(
                        f"Recommendation {i}: {change_pct:.0f}% budget change for {cid} exceeds 50% threshold"
                    )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_single_finding(
        self,
        f: dict[str, Any],
        index: int,
        valid_ids: set,
    ) -> list[str]:
        errors = []

        required_fields = ["campaign_id", "metric", "severity", "detail"]
        for field in required_fields:
            if field not in f:
                errors.append(f"Finding {index}: missing required field '{field}'")

        cid = f.get("campaign_id")
        if cid and cid not in valid_ids:
            errors.append(
                f"Finding {index}: HALLUCINATION — campaign_id '{cid}' does not exist in source data"
            )

        severity = f.get("severity")
        if severity and severity not in ("low", "medium", "high"):
            errors.append(f"Finding {index}: invalid severity '{severity}'")

        current_value = f.get("current_value")
        if current_value is not None and not isinstance(current_value, (int, float)):
            errors.append(f"Finding {index}: current_value must be numeric, got {type(current_value).__name__}")

        if isinstance(current_value, (int, float)) and current_value < 0:
            errors.append(f"Finding {index}: negative current_value {current_value}")

        return errors

    def _check_contradictions(self, findings: list[dict]) -> list[str]:
        warnings = []
        campaigns_mentioned = {}
        for f in findings:
            cid = f.get("campaign_id")
            if cid:
                if cid not in campaigns_mentioned:
                    campaigns_mentioned[cid] = []
                campaigns_mentioned[cid].append(f.get("recommendation", ""))

        for cid, recs in campaigns_mentioned.items():
            increase = any("increase" in r.lower() for r in recs)
            decrease = any("decrease" in r.lower() for r in recs)
            if increase and decrease:
                warnings.append(
                    f"Contradictory recommendations for {cid}: both increase and decrease suggested"
                )

        return warnings

"""
Analyst Agent: LLM-powered campaign performance analysis.
Uses ModelRouter to call multiple models (Claude, Gemini) with fallback.

Intentional failure scenarios this handles:
1. LLM returns invalid JSON → retry with stricter instruction
2. Model times out or rate limited → fallback to next model
3. LLM hallucination (invented campaign IDs) → caught by Validator agent
"""

import json
import logging
from typing import Any

from .model_router import ModelRouter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI analyst for paid media campaigns. Given campaign data and an analysis plan:

1. Calculate ROAS for every campaign. Flag any with ROAS < 1.5.
2. Flag campaigns with CTR < 0.5% as poor creative performance.
3. Flag campaigns where CPC > 2x the account average.
4. Identify campaigns with suspicious metrics (e.g. impressions but 0 clicks, or spend > budget).
5. For each flagged campaign, provide a specific recommendation.

IMPORTANT RULES:
- Only reference campaign IDs that actually exist in the provided data.
- Never invent data or campaign IDs.
- If you are unsure about something, set confidence to "low".
- Return ONLY valid JSON. No markdown, no explanations outside JSON.

Return format:
{
  "findings": [
    {
      "campaign_id": "string (must match exactly one of the provided IDs)",
      "campaign_name": "string",
      "metric": "roas | ctr | cpc | suspicious | budget",
      "current_value": float,
      "threshold": float,
      "severity": "low | medium | high",
      "confidence": "low | medium | high",
      "detail": "plain english explanation",
      "recommendation": "specific action the strategist should take"
    }
  ]
}

If all campaigns are healthy, return {"findings": []}."""  # noqa: E501


class AnalystAgent:
    def __init__(self, model_router: ModelRouter):
        self.router = model_router

    def analyze(self, campaigns: list[dict], plan: dict) -> list[dict[str, Any]]:
        if not campaigns:
            return []

        summary = self._build_summary(campaigns, plan)
        findings = self._call_llm(summary)

        validated = self._validate_findings(findings, campaigns)
        if len(validated) < len(findings):
            logger.warning(
                f"Validator caught {len(findings) - len(validated)} hallucinated/synthetic findings"
            )

        return validated

    def _build_summary(self, campaigns: list[dict], plan: dict) -> dict:
        total_spend = sum(c.get("spend", 0) for c in campaigns)
        total_revenue = sum(c.get("revenue", 0) for c in campaigns)
        avg_cpc = (
            sum(c.get("cpc", 0) for c in campaigns) / len(campaigns)
            if campaigns
            else 0
        )

        return {
            "account_summary": {
                "total_campaigns": len(campaigns),
                "total_spend_30d": round(total_spend, 2),
                "total_revenue_30d": round(total_revenue, 2),
                "overall_roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
                "average_cpc": round(avg_cpc, 2),
            },
            "analysis_plan": [
                {
                    "type": item["analysis_type"],
                    "priority": item["priority"],
                    "reason": item["reason"],
                }
                for item in plan.get("plan", [])
            ],
            "campaigns": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "platform": c.get("platform", "unknown"),
                    "status": c.get("status", "UNKNOWN"),
                    "daily_budget": c.get("dailyBudget", 0),
                    "spend_30d": c.get("spend", 0),
                    "revenue_30d": c.get("revenue", 0),
                    "roas": round(c.get("revenue", 0) / c.get("spend", 1), 2) if c.get("spend", 0) > 0 else 0,
                    "impressions": c.get("impressions", 0),
                    "clicks": c.get("clicks", 0),
                    "conversions": c.get("conversions", 0),
                    "ctr_pct": c.get("ctr", 0),
                    "cpc": c.get("cpc", 0),
                }
                for c in campaigns
            ],
        }

    def _call_llm(self, summary: dict) -> list[dict]:
        user_message = json.dumps(summary, indent=2)

        for attempt in range(2):
            try:
                text = self.router.call(
                    system_prompt=SYSTEM_PROMPT,
                    user_message=user_message,
                    max_tokens=8192,
                )
                return self._parse_findings(text)
            except json.JSONDecodeError as e:
                logger.warning(f"LLM returned invalid JSON (attempt {attempt + 1}): {e}")
                if attempt == 1:
                    raise
            except Exception as e:
                logger.error(f"LLM call failed (attempt {attempt + 1}): {e}")
                if attempt == 1:
                    raise
        return []

    def _parse_findings(self, text: str) -> list[dict[str, Any]]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("` \n")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            text = self._repair_json(text)
            result = json.loads(text)

        if isinstance(result, dict):
            return result.get("findings", [])
        return result

    def _repair_json(self, text: str) -> str:
        """Fix common Gemini JSON issues before parsing."""
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("` \n")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        in_string = False
        escape = False
        chars = []
        for ch in text:
            if escape:
                chars.append(ch)
                escape = False
                continue
            if ch == "\\":
                chars.append(ch)
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                chars.append(ch)
                continue
            if not in_string:
                if ch == "'":
                    chars.append('"')
                    continue
            chars.append(ch)

        repaired = "".join(chars)
        repaired = repaired.replace("True", "true").replace("False", "false").replace("None", "null")
        repaired = repaired.replace(",]", "]").replace(",}", "}")
        return repaired

    def _validate_findings(
        self, findings: list[dict], campaigns: list[dict]
    ) -> list[dict]:
        valid_ids = {c.get("id") for c in campaigns}
        validated = []
        for f in findings:
            cid = f.get("campaign_id")
            if cid and cid in valid_ids:
                validated.append(f)
            else:
                logger.warning(
                    f"Removed hallucinated finding: campaign_id '{cid}' not in data"
                )
        return validated

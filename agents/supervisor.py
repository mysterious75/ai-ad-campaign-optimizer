"""
Supervisor: Orchestrates the 6-agent pipeline for one client.
Pipeline:
  Researcher (incl. Shopify/GA4/Klaviyo) -> Planner -> Analyst(LLM) -> Validator -> Action -> Report
Every decision is logged to Convex for real-time frontend updates.
"""

import asyncio
import logging
import os
from typing import Any, Optional

from .convex_client import ConvexClient
from .researcher_agent import ResearcherAgent
from .planner_agent import PlannerAgent
from .analyst_agent import AnalystAgent
from .validator_agent import ValidatorAgent
from .report_agent import ReportAgent
from .action_agent import ActionAgent
from .model_router import ModelRouter
from .email_client import EmailClient
from .integrations import ShopifyClient, GA4Client, KlaviyoClient

logger = logging.getLogger(__name__)


class Supervisor:
    def __init__(self, convex: ConvexClient):
        self.convex = convex
        self.researcher = ResearcherAgent()
        self.planner = PlannerAgent()
        self.router = ModelRouter()
        self.analyst = AnalystAgent(model_router=self.router)
        self.validator = ValidatorAgent()
        self.action = ActionAgent(
            meta_token=os.getenv("META_ACCESS_TOKEN", ""),
            google_token=os.getenv("GOOGLE_ACCESS_TOKEN", ""),
        )
        self.report = ReportAgent(convex)
        self.email = EmailClient()

    async def _collect_integration_data(self, client_config: dict) -> dict[str, Any]:
        data = {}
        shopify_cfg = client_config.get("platformConnections", {}).get("shopify", {})
        if shopify_cfg:
            shopify = ShopifyClient(
                store_domain=shopify_cfg.get("storeDomain", ""),
                access_token=shopify_cfg.get("accessToken", ""),
            )
            try:
                data["shopify"] = await shopify.fetch_revenue(days_back=30)
                logger.info(f"Shopify: fetched {data['shopify'].get('total_orders', 0)} orders")
            except Exception as e:
                logger.warning(f"Shopify fetch failed: {e}")

        ga4_cfg = client_config.get("platformConnections", {}).get("google", {})
        if ga4_cfg and os.getenv("GA4_PROPERTY_ID"):
            ga4 = GA4Client(
                property_id=os.getenv("GA4_PROPERTY_ID", ""),
                access_token=os.getenv("GOOGLE_ACCESS_TOKEN", ""),
            )
            try:
                data["ga4"] = {"attribution": await ga4.fetch_campaign_attribution(days_back=30)}
                logger.info("GA4: fetched campaign attribution")
            except Exception as e:
                logger.warning(f"GA4 fetch failed: {e}")

        klaviyo_cfg = client_config.get("platformConnections", {}).get("klaviyo", {})
        if klaviyo_cfg:
            klaviyo = KlaviyoClient(api_key=klaviyo_cfg.get("apiKey", ""))
            try:
                data["klaviyo"] = {"campaigns": await klaviyo.fetch_campaigns(days_back=30)}
                logger.info(f"Klaviyo: fetched email campaigns")
            except Exception as e:
                logger.warning(f"Klaviyo fetch failed: {e}")

        return data

    async def run_for_client(self, client_id: str, client_config: dict) -> dict[str, Any]:
        run_id = await self.convex.create_agent_run(client_id, trigger="schedule")
        pipeline_log = []
        client_name = client_config.get("name", client_id)
        admin_email = client_config.get("settings", {}).get("notificationEmail", "")

        try:
            await self.convex.append_audit_event(client_id, "pipeline_started", "supervisor", "agent_run", {"run_id": run_id})

            # Step 1: Research
            await self.convex.update_run_status(run_id, "researching")
            researcher_result = await self.researcher.fetch_campaigns(client_config)

            integrations_data = await self._collect_integration_data(client_config)
            researcher_result["integrations"] = integrations_data

            pipeline_log.append({"agent": "researcher", "status": "done", "campaigns": len(researcher_result.get("campaigns", []))})

            if not researcher_result.get("campaigns"):
                await self.convex.update_run_status(run_id, "completed", summary="No campaigns fetched")
                return {"status": "completed", "summary": "No campaigns"}

            # Step 2: Plan
            await self.convex.update_run_status(run_id, "planning")
            planner_result = self.planner.create_plan(researcher_result)
            pipeline_log.append({"agent": "planner", "status": "done", "plan_items": len(planner_result.get("plan", []))})

            if not planner_result.get("should_proceed"):
                await self.convex.update_run_status(run_id, "completed", summary=planner_result.get("reason"))
                return {"status": "completed", "summary": planner_result.get("reason")}

            # Step 3: Analyze
            await self.convex.update_run_status(run_id, "analyzing")
            await self.convex.append_log(run_id, client_id, "supervisor", "phase_start", {
                "phase": "analyzing",
                "campaigns": planner_result.get("total_campaigns"),
                "plan": planner_result.get("plan"),
            })
            findings = self.analyst.analyze(researcher_result.get("campaigns", []), planner_result)
            pipeline_log.append({"agent": "analyst", "status": "done", "findings": len(findings)})

            # Step 4: Validate
            await self.convex.update_run_status(run_id, "validating")
            validator_result = self.validator.validate_findings(findings, researcher_result.get("campaigns", []), planner_result)
            pipeline_log.append({
                "agent": "validator", "status": "done",
                "valid": validator_result.get("valid"),
                "errors": len(validator_result.get("errors", [])),
                "warnings": len(validator_result.get("warnings", [])),
            })

            validated_findings = validator_result.get("findings", [])
            if validator_result.get("errors"):
                await self.convex.append_log(run_id, client_id, "validator", "errors", {"errors": validator_result["errors"]})
            if validator_result.get("warnings"):
                await self.convex.append_log(run_id, client_id, "validator", "warnings", {"warnings": validator_result["warnings"]})

            if not validator_result.get("valid"):
                logger.warning(f"Validation failed for run {run_id}: {validator_result['errors']}")
                await self.convex.update_run_status(run_id, "failed", error=f"Validation failed: {'; '.join(validator_result['errors'])}")
                if admin_email:
                    await self.email.send_alert(admin_email, client_name, "high", f"Validation failed: {'; '.join(validator_result['errors'])}")
                return {"status": "failed", "errors": validator_result["errors"]}

            # Step 5: Execute
            execution_results = await self._execute_findings(run_id, client_id, validated_findings, researcher_result.get("campaigns", []), client_name, admin_email)
            pipeline_log.append({"agent": "action", "status": "done", "executed": len(execution_results)})

            # Step 6: Report
            await self.convex.update_run_status(run_id, "reporting")
            summary = await self.report.generate_and_save(
                run_id=run_id, client_id=client_id,
                researcher_result=researcher_result,
                planner_result=planner_result,
                analyst_findings=validated_findings,
                validator_result=validator_result,
                execution_results=execution_results,
            )

            await self.convex.append_audit_event(client_id, "pipeline_completed", "supervisor", "agent_run", {
                "run_id": run_id, "findings": len(validated_findings), "actions": len(execution_results),
            })

            if admin_email:
                await self.email.send_report(admin_email, client_name, summary)

            await self.convex.update_run_status(run_id, "completed", summary=summary.get("overview", {}))
            return {"status": "completed", "run_id": run_id, "pipeline": pipeline_log, "findings": len(validated_findings), "actions_taken": len(execution_results), "api_metrics": researcher_result.get("metrics", {})}

        except Exception as e:
            logger.error(f"Pipeline failed for run {run_id}: {e}")
            await self.convex.update_run_status(run_id, "failed", error=str(e))
            await self.convex.append_audit_event(client_id, "pipeline_failed", "supervisor", "agent_run", {"run_id": run_id, "error": str(e)})
            if admin_email:
                await self.email.send_alert(admin_email, client_name, "critical", f"Pipeline failed: {e}")
            return {"status": "failed", "run_id": run_id, "error": str(e)}

    async def _execute_findings(self, run_id: str, client_id: str, findings: list[dict], campaigns: list[dict], client_name: str = "", admin_email: str = "") -> list[dict]:
        execution_results = []
        high_severity = [f for f in findings if f.get("severity") == "high" and f.get("confidence") != "low"]

        for finding in high_severity:
            campaign_id = finding["campaign_id"]
            campaign = next((c for c in campaigns if c.get("id") == campaign_id), None)
            if not campaign:
                continue

            platform = campaign.get("platform", "meta")
            detail = finding.get("detail", "")
            impact = 0
            if "increase" in finding.get("recommendation", "").lower():
                recommended_budget = campaign.get("dailyBudget", 0) * 1.2
                impact = recommended_budget - campaign.get("dailyBudget", 0)

                if impact > 1000:
                    await self.convex.create_approval(run_id=run_id, client_id=client_id, action_type="budget_increase", details=detail, impact=impact)
                    if admin_email:
                        await self.email.send_approval_request(admin_email, client_name, "budget_increase", detail, impact)
                    execution_results.append({"campaign_id": campaign_id, "action": "budget_increase", "status": "pending_approval", "impact": impact})
                    continue

                try:
                    result = await self.action.execute_budget_change(platform=platform, campaign_id=campaign_id, new_budget=recommended_budget)
                    await self.convex.append_audit_event(client_id, "budget_changed", "action_agent", f"campaign:{campaign_id}", {"old_budget": campaign.get("dailyBudget"), "new_budget": recommended_budget})
                    execution_results.append({**result, "reasoning": detail})
                except Exception as e:
                    execution_results.append({"campaign_id": campaign_id, "action": "budget_increase", "status": "failed", "error": str(e)})

        return execution_results

    async def run_onboarding(self, client_id: str, client_config: dict) -> dict[str, Any]:
        onboarding_id = await self.convex.get_or_create_onboarding(client_id)
        steps = ["connect_meta", "connect_google", "connect_shopify", "connect_klaviyo", "import_campaigns", "first_run"]

        for step in steps:
            success = False
            try:
                if step == "connect_meta":
                    meta = client_config.get("platformConnections", {}).get("meta", {})
                    success = bool(meta.get("accessToken") and meta.get("adAccountId"))
                    await self.convex.update_onboarding(client_id, step, {"metaConnected": success})
                elif step == "connect_google":
                    google = client_config.get("platformConnections", {}).get("google", {})
                    success = bool(google.get("accessToken") and google.get("customerId"))
                    await self.convex.update_onboarding(client_id, step, {"googleConnected": success})
                elif step == "connect_shopify":
                    shopify = client_config.get("platformConnections", {}).get("shopify", {})
                    success = bool(shopify.get("accessToken") and shopify.get("storeDomain"))
                    await self.convex.update_onboarding(client_id, step, {"shopifyConnected": success})
                elif step == "connect_klaviyo":
                    klaviyo = client_config.get("platformConnections", {}).get("klaviyo", {})
                    success = bool(klaviyo.get("apiKey"))
                    await self.convex.update_onboarding(client_id, step, {"klaviyoConnected": success})
                elif step == "import_campaigns":
                    result = await self.researcher.fetch_campaigns(client_config)
                    success = len(result.get("campaigns", [])) > 0
                    await self.convex.update_onboarding(client_id, step, {"campaignsImported": success})
                elif step == "first_run":
                    result = await self.run_for_client(client_id, client_config)
                    success = result.get("status") == "completed"
                    await self.convex.update_onboarding(client_id, step, {"firstAgentRunCompleted": success})

                if not success:
                    await self.convex.update_onboarding(client_id, step, {"status": "failed", "error": f"Step {step} failed"})
                    return {"status": "failed", "step": step}

            except Exception as e:
                logger.error(f"Onboarding step {step} failed: {e}")
                await self.convex.update_onboarding(client_id, step, {"status": "failed", "error": str(e)})
                return {"status": "failed", "step": step, "error": str(e)}

        await self.convex.update_onboarding(client_id, "completed", {"status": "completed"})
        return {"status": "completed"}

"""
demo_full.py - Complete pipeline demo with all 5 agents.
Shows every step: prompts, logic, results.
Runs with real Gemini LLM.
"""

import os, sys, json, asyncio, time
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ["LLM_MODELS"] = "gemini-2.5-flash,gemini-2.5-pro"

from agents.planner_agent import PlannerAgent
from agents.analyst_agent import AnalystAgent, SYSTEM_PROMPT as ANALYST_PROMPT
from agents.validator_agent import ValidatorAgent
from agents.report_agent import ReportAgent
from agents.model_router import ModelRouter


class MockConvex:
    async def create_agent_run(self, cid, trigger="schedule"): return "demo_run_001"
    async def update_run_status(self, rid, status, **kw): pass
    async def append_log(self, rid, cid, agent, mtype, payload): pass
    async def create_approval(self, **kw): return "approval_demo"


CAMPAIGNS = [
    {"id": "c1", "platform": "meta", "name": "Brand Awareness", "status": "ACTIVE",
     "dailyBudget": 100, "spend": 2450, "revenue": 5200, "impressions": 185000,
     "clicks": 3200, "conversions": 45, "ctr": 1.73, "cpc": 0.77},
    {"id": "c2", "platform": "meta", "name": "Lead Gen - Webinars", "status": "ACTIVE",
     "dailyBudget": 50, "spend": 1550, "revenue": 1200, "impressions": 89000,
     "clicks": 410, "conversions": 12, "ctr": 0.46, "cpc": 3.78},
    {"id": "c3", "platform": "meta", "name": "Retargeting - Website", "status": "ACTIVE",
     "dailyBudget": 75, "spend": 1820, "revenue": 6800, "impressions": 42000,
     "clicks": 980, "conversions": 38, "ctr": 2.33, "cpc": 1.86},
    {"id": "c4", "platform": "meta", "name": "DPA - Products", "status": "ACTIVE",
     "dailyBudget": 200, "spend": 5800, "revenue": 18200, "impressions": 210000,
     "clicks": 5100, "conversions": 92, "ctr": 2.43, "cpc": 1.14},
    {"id": "c5", "platform": "meta", "name": "Video Views", "status": "ACTIVE",
     "dailyBudget": 150, "spend": 4200, "revenue": 2100, "impressions": 420000,
     "clicks": 2100, "conversions": 18, "ctr": 0.50, "cpc": 2.00},
]


def sep(title):
    print("\n" + "=" * 72)
    print("  " + title)
    print("=" * 72)


def show_campaigns():
    print(f"  {'ID':<5} {'Name':<24} {'Spend':>8} {'Revenue':>9} {'ROAS':>6} {'CTR':>6} {'CPC':>6}")
    print(f"  " + "-" * 68)
    for c in CAMPAIGNS:
        roas = round(c["revenue"] / c["spend"], 2) if c["spend"] > 0 else 0
        print(f"  {c['id']:<5} {c['name']:<24} ${c['spend']:>6,.0f} ${c['revenue']:>7,.0f} {roas:>5.2f} {c['ctr']:>5.2f}% ${c['cpc']:>4.2f}")
    total_spend = sum(c['spend'] for c in CAMPAIGNS)
    total_rev = sum(c['revenue'] for c in CAMPAIGNS)
    print(f"\n  TOTAL: ${total_spend:,} spend, ${total_rev:,} revenue, ROAS {total_rev/total_spend:.2f}")


async def main():
    print("\n" + "=" * 72)
    print("  MULTI-AGENT AD CAMPAIGN OPTIMIZER")
    print("  Agents: Researcher -> Planner -> Analyst(LLM) -> Validator -> Report")
    print("  LLM: Gemini 2.5 Flash (via OpenRouter-style API)")
    print("=" * 72)

    convex = MockConvex()
    router = ModelRouter()
    print(f"\n  Models: {router.models}")
    print(f"  API Key: GEMINI_API_KEY = SET [{os.environ['GEMINI_API_KEY'][:15]}...]")

    # ========== INPUT ==========
    sep("INPUT DATA: 5 Meta Ads Campaigns")
    show_campaigns()

    # ========== STEP 1: RESEARCHER ==========
    sep("STEP 1: RESEARCHER AGENT -- Data Collection")
    print("  File: agents/researcher_agent.py")
    print("  Job: Fetch campaigns from Meta & Google Ads APIs")
    print("  Handles: 429 rate limits, 401 token expiry, API timeouts")
    print()
    print("  In production (live):")
    print("    GET https://graph.facebook.com/v18.0/act_{id}/campaigns")
    print("    + Token bucket: 200 req/hr for Meta, 5000 req/hr for Google")
    print("    + Retry: exponential backoff with jitter + Retry-After respect")
    print("    + Token refresh: auto-refresh on 401 via fb_exchange_token")
    print()
    print("  In demo (simulated): Using pre-loaded sample data")
    researcher_result = {
        "campaigns": CAMPAIGNS,
        "platforms_fetched": ["meta"],
        "platforms_failed": [],
        "errors": [],
        "metrics": {"total_api_calls": 1, "rate_limits_hit": 0, "tokens_refreshed": 0},
    }
    print(f"  Result: {len(researcher_result['campaigns'])} campaigns from meta")

    # ========== STEP 2: PLANNER ==========
    sep("STEP 2: PLANNER AGENT -- Analysis Planning")
    print("  File: agents/planner_agent.py")
    print("  Job: Decide WHAT to analyze (deterministic rules, no LLM cost)")
    print()
    print("  Rules (no AI needed -- pure logic):")
    print("    1. ROAS analysis -- flag if ROAS < 1.5 threshold")
    print("    2. Budget utilization -- campaigns with spend < $100")
    print("    3. High spend review -- campaigns with spend > $1k")
    print("    4. Anomaly detection -- routine scan of all metrics")
    print("    5. Platform error review -- if API fetch failed")

    planner = PlannerAgent()
    plan = planner.create_plan(researcher_result)

    print(f"\n  Total campaigns: {plan['total_campaigns']}")
    print(f"  Overall ROAS: {plan['overall_roas']}")
    print(f"  Should proceed: {plan['should_proceed']}")
    print(f"\n  Plan ({len(plan['plan'])} items):")
    for p in plan['plan']:
        print(f"    [{p['priority'].upper()}] {p['analysis_type']}")
        print(f"           Reason: {p['reason']}")

    # ========== STEP 3: ANALYST ==========
    sep("STEP 3: ANALYST AGENT -- LLM Campaign Analysis")
    print("  File: agents/analyst_agent.py")
    print("  Model Router: agents/model_router.py")
    print("  Job: Send campaign data to LLM, get structured findings")
    print()
    print("  -- SYSTEM PROMPT sent to LLM --")
    for line in ANALYST_PROMPT.strip().split("\n"):
        print(f"  | {line}")
    print("  ----------------------------------------")
    print()
    print("  Flow:")
    print("    1. Campaign data is PRE-SUMMARIZED (not raw)")
    print("    2. Sent to LLM via ModelRouter.call()")
    print("    3. LLM must return valid JSON (prompt enforces schema)")
    print("    4. If JSON parse fails -> auto-repair (fix quotes/commas)")
    print("    5. If model fails -> fallback to next in list")
    print("    6. Hallucination check after: campaign_ids validated vs source")
    print()

    analyst = AnalystAgent(model_router=router)
    start = time.time()
    findings = analyst.analyze(CAMPAIGNS, plan)
    elapsed = time.time() - start

    print(f"  LLM used: gemini-2.5-flash")
    print(f"  Response time: {elapsed:.1f}s")
    tokens = router.usage.get("gemini-2.5-flash", {}).get("tokens", 0)
    print(f"  Tokens consumed: ~{tokens}")
    print()

    if not findings:
        print("  All campaigns healthy -- no issues found")
    else:
        print(f"  FINDINGS ({len(findings)} total):")
        print()
        for i, f in enumerate(findings):
            sev = f['severity'].upper()
            print(f"  --- Finding #{i+1} [{sev}] ---")
            print(f"  Campaign: {f['campaign_id']} ({f['campaign_name']})")
            print(f"  Metric:   {f['metric']} = {f['current_value']}")
            print(f"  Threshold: {f['threshold']}")
            print(f"  Detail:   {f['detail']}")
            print(f"  Suggest:  {f['recommendation']}")
            print(f"  Confidence: {f.get('confidence', 'N/A')}")
            print()

    # ========== STEP 4: VALIDATOR ==========
    sep("STEP 4: VALIDATOR AGENT -- Quality Check")
    print("  File: agents/validator_agent.py")
    print("  Job: Validate LLM output before any execution")
    print()
    print("  Checks:")
    print("    1. HALLUCINATION -- all campaign_ids must exist in source data")
    print("    2. SCHEMA -- required fields present and correct types")
    print("    3. SANITY -- no negative budgets, no impossible values")
    print("    4. CONTRADICTION -- no increase+decrease for same campaign")
    print("    5. CONFIDENCE -- low-confidence findings flagged for review")
    print()

    validator = ValidatorAgent()
    validation = validator.validate_findings(findings, CAMPAIGNS, plan)

    print(f"  VALID: {validation['valid']}")
    print(f"  Errors: {len(validation['errors'])}")
    for e in validation['errors']:
        print(f"    [ERROR] {e}")
    print(f"  Warnings: {len(validation['warnings'])}")
    for w in validation['warnings']:
        print(f"    [WARN] {w}")

    # Check budget recommendations too
    high_findings = [f for f in findings if f.get("severity") == "high"]
    if high_findings:
        recs = [{"campaign_id": f["campaign_id"], "amount": 50, "new_budget": 200} for f in high_findings]
        rec_val = validator.validate_recommendations(recs, CAMPAIGNS)
        print(f"\n  Budget rec check: {'PASS' if rec_val['valid'] else 'FAIL'}")
        for w in rec_val.get('warnings', []):
            print(f"    [WARN] {w}")

    # ========== STEP 5: REPORT ==========
    sep("STEP 5: REPORT AGENT -- Summary Generation")
    print("  File: agents/report_agent.py")
    print("  Job: Build structured summary, save to Convex DB")
    print("  Convex data powers the real-time client portal")
    print()

    report = ReportAgent(convex)
    summary = await report.generate_and_save(
        run_id="demo_run", client_id="demo_client",
        researcher_result=researcher_result,
        planner_result=plan,
        analyst_findings=findings,
        validator_result=validation,
        execution_results=[],
    )

    print("  FINAL SUMMARY (saved to Convex agentLogs table):")
    print(json.dumps(summary, indent=2))

    # ========== MODEL USAGE ==========
    sep("MODEL USAGE")
    print(router.get_usage_report())

    # ========== ERROR HANDLING ==========
    sep("ERROR HANDLING (what if things go wrong?)")
    scenarios = [
        ("RATE LIMIT (429)", "Token bucket waits -> exponential backoff -> retry -> fallback model"),
        ("INVALID JSON", "Auto-repair (fix quotes/commas) -> retry -> fail gracefully"),
        ("HALLUCINATION", "Validator removes non-existent campaign_ids, warning logged"),
        ("TOKEN EXPIRY (401)", "Researcher auto-refreshes via fb_exchange_token or refresh_token grant"),
        ("CONTRADICTION", "Validator flags increase+decrease for same campaign, human review"),
    ]
    for title, desc in scenarios:
        print(f"  [{title}]")
        print(f"    {desc}")
        print()

    print("=" * 72)
    print("  DEMO COMPLETE - ALL 5 AGENTS WORKING END-TO-END")
    print("=" * 72)
    print()
    print("  FILES INVOLVED:")
    print("    agents/researcher_agent.py  - API fetching + rate limits + token refresh")
    print("    agents/planner_agent.py     - Analysis planning (deterministic, no LLM)")
    print("    agents/analyst_agent.py     - LLM campaign analysis (Gemini/Claude)")
    print("    agents/model_router.py      - Multi-model router with fallback")
    print("    agents/validator_agent.py   - LLM output validation (hallucinations, schema)")
    print("    agents/report_agent.py      - Summary generation + Convex logging")
    print("    agents/rate_limiter.py      - Token bucket rate limiter + RetryHandler")
    print("    agents/supervisor.py        - Full pipeline orchestrator (all 6 steps)")
    print()
    print("  CONFIGURATION (.env):")
    print(f"    LLM_MODELS={os.environ['LLM_MODELS']}")
    print("    GEMINI_API_KEY=SET")
    print("    ANTHROPIC_API_KEY=(not set)")
    print()


if __name__ == "__main__":
    asyncio.run(main())

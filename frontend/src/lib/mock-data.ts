import type { Client, Campaign, AgentRun, AgentLog, Approval, Onboarding } from "./types";

export const MOCK_CLIENT: Client = {
  _id: "client_demo_001",
  _creationTime: Date.now() - 86400000 * 30,
  name: "Acme Digital Agency",
  platformConnections: {
    meta: { accessToken: "EAAM...", adAccountId: "act_123456789", tokenExpiresAt: Date.now() + 86400000 * 60 },
    google: { accessToken: "ya29...", customerId: "123-456-7890", refreshToken: "1//...", tokenExpiresAt: Date.now() + 86400000 * 60 },
    shopify: { storeDomain: "acme.myshopify.com", accessToken: "shpat_..." },
    klaviyo: { apiKey: "pk_..." },
  },
  settings: {
    defaultRoasTarget: 1.5,
    maxBudgetChangePct: 50,
    requireApprovalForBudgetOver: 500,
    timezone: "Australia/Sydney",
  },
  createdAt: Date.now() - 86400000 * 30,
};

export const MOCK_CAMPAIGNS: Campaign[] = [
  { _id: "camp_001", _creationTime: Date.now(), clientId: "client_demo_001", platform: "meta", platformCampaignId: "p1", name: "Brand Awareness", status: "ACTIVE", dailyBudget: 100, spend: 2450, impressions: 185000, clicks: 3200, conversions: 45, revenue: 5200, roas: 2.12, ctr: 1.73, cpc: 0.77, lastSyncedAt: Date.now() },
  { _id: "camp_002", _creationTime: Date.now(), clientId: "client_demo_001", platform: "meta", platformCampaignId: "p2", name: "Lead Gen - Webinars", status: "ACTIVE", dailyBudget: 50, spend: 1550, impressions: 89000, clicks: 410, conversions: 12, revenue: 1200, roas: 0.77, ctr: 0.46, cpc: 3.78, lastSyncedAt: Date.now() },
  { _id: "camp_003", _creationTime: Date.now(), clientId: "client_demo_001", platform: "meta", platformCampaignId: "p3", name: "Retargeting - Website", status: "ACTIVE", dailyBudget: 75, spend: 1820, impressions: 42000, clicks: 980, conversions: 38, revenue: 6800, roas: 3.74, ctr: 2.33, cpc: 1.86, lastSyncedAt: Date.now() },
  { _id: "camp_004", _creationTime: Date.now(), clientId: "client_demo_001", platform: "meta", platformCampaignId: "p4", name: "DPA - Products", status: "ACTIVE", dailyBudget: 200, spend: 5800, impressions: 210000, clicks: 5100, conversions: 92, revenue: 18200, roas: 3.14, ctr: 2.43, cpc: 1.14, lastSyncedAt: Date.now() },
  { _id: "camp_005", _creationTime: Date.now(), clientId: "client_demo_001", platform: "meta", platformCampaignId: "p5", name: "Video Views", status: "ACTIVE", dailyBudget: 150, spend: 4200, impressions: 420000, clicks: 2100, conversions: 18, revenue: 2100, roas: 0.50, ctr: 0.50, cpc: 2.00, lastSyncedAt: Date.now() },
];

export const MOCK_RUNS: AgentRun[] = [
  { _id: "run_001", _creationTime: Date.now(), clientId: "client_demo_001", trigger: "schedule", status: "completed", summary: "Found 4 issues (2 high). 2 budget changes executed.", startedAt: Date.now() - 3600000, completedAt: Date.now() - 3500000 },
  { _id: "run_002", _creationTime: Date.now(), clientId: "client_demo_001", trigger: "manual", status: "awaiting_approval", summary: "Found 3 issues. 1 change requires approval.", startedAt: Date.now() - 7200000, completedAt: Date.now() - 7100000 },
  { _id: "run_003", _creationTime: Date.now(), clientId: "client_demo_001", trigger: "schedule", status: "completed", summary: "All campaigns healthy, no changes needed.", startedAt: Date.now() - 10800000, completedAt: Date.now() - 10700000 },
];

export const MOCK_LOGS: AgentLog[] = [
  { _id: "log_001", _creationTime: Date.now(), runId: "run_001", clientId: "client_demo_001", agent: "Researcher", msgType: "info", payload: { message: "Fetched 5 campaigns from Meta Ads API", platforms: ["meta"] }, createdAt: Date.now() - 3590000 },
  { _id: "log_002", _creationTime: Date.now(), runId: "run_001", clientId: "client_demo_001", agent: "Planner", msgType: "info", payload: { message: "Created 3 analysis plan items", plan: ["roas_analysis", "high_spend_review", "anomaly_detection"] }, createdAt: Date.now() - 3580000 },
  { _id: "log_003", _creationTime: Date.now(), runId: "run_001", clientId: "client_demo_001", agent: "Analyst", msgType: "llm_call", payload: { model: "gemini-2.5-flash", tokens: 1953, latency_ms: 17600, findings_count: 4 }, createdAt: Date.now() - 3560000 },
  { _id: "log_004", _creationTime: Date.now(), runId: "run_001", clientId: "client_demo_001", agent: "Validator", msgType: "result", payload: { valid: true, errors: [], warnings: ["Budget change >50% flagged"] }, createdAt: Date.now() - 3540000 },
  { _id: "log_005", _creationTime: Date.now(), runId: "run_001", clientId: "client_demo_001", agent: "Action", msgType: "execution", payload: { c2: { action: "decrease_budget", amount: 50, old_budget: 100, new_budget: 50, status: "executed" } }, createdAt: Date.now() - 3520000 },
  { _id: "log_006", _creationTime: Date.now(), runId: "run_001", clientId: "client_demo_001", agent: "Report", msgType: "summary", payload: { total_findings: 4, high_severity: 2, medium_severity: 2 }, createdAt: Date.now() - 3500000 },
];

export const MOCK_APPROVALS: Approval[] = [
  { _id: "appr_001", _creationTime: Date.now(), runId: "run_002", clientId: "client_demo_001", actionType: "budget_change", details: "Increase c5 daily budget from $150 to $225 (50% increase) to capture more video view traffic", impact: 75, status: "pending", createdAt: Date.now() - 7200000, expiresAt: Date.now() + 86400000 * 1 },
];

export const MOCK_ONBOARDING: Onboarding = {
  _id: "onb_001", _creationTime: Date.now(), clientId: "client_demo_001",
  step: "completed", status: "completed",
  metaConnected: true, googleConnected: true, shopifyConnected: true, klaviyoConnected: true,
  campaignsImported: true, firstAgentRunCompleted: true,
  createdAt: Date.now() - 86400000 * 25, updatedAt: Date.now() - 86400000 * 23,
};

export interface Client {
  _id: string;
  _creationTime: number;
  name: string;
  platformConnections: {
    meta?: { accessToken: string; adAccountId: string; tokenExpiresAt: number };
    google?: { accessToken: string; customerId: string; refreshToken: string; tokenExpiresAt: number };
    shopify?: { storeDomain: string; accessToken: string };
    klaviyo?: { apiKey: string };
  };
  settings: {
    defaultRoasTarget: number;
    maxBudgetChangePct: number;
    requireApprovalForBudgetOver: number;
    timezone: string;
  };
  createdAt: number;
}

export interface Campaign {
  _id: string;
  _creationTime: number;
  clientId: string;
  platform: "meta" | "google";
  platformCampaignId: string;
  name: string;
  status: string;
  dailyBudget: number;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
  roas: number;
  ctr: number;
  cpc: number;
  lastSyncedAt: number;
}

export type AgentRunStatus =
  | "pending" | "researching" | "planning" | "analyzing"
  | "validating" | "reporting" | "awaiting_approval"
  | "executing" | "completed" | "failed";

export interface AgentRun {
  _id: string;
  _creationTime: number;
  clientId: string;
  trigger: "schedule" | "manual" | "webhook";
  status: AgentRunStatus;
  summary?: string;
  startedAt: number;
  completedAt?: number;
  error?: string;
}

export interface AgentLog {
  _id: string;
  _creationTime: number;
  runId: string;
  clientId: string;
  agent: string;
  msgType: string;
  payload: any;
  createdAt: number;
}

export interface Approval {
  _id: string;
  _creationTime: number;
  runId: string;
  clientId: string;
  actionType: string;
  details: string;
  impact: number;
  status: "pending" | "approved" | "rejected" | "expired";
  reviewedBy?: string;
  reviewedAt?: number;
  createdAt: number;
  expiresAt: number;
}

export interface Onboarding {
  _id: string;
  _creationTime: number;
  clientId: string;
  step: string;
  status: "in_progress" | "completed" | "failed";
  metaConnected: boolean;
  googleConnected: boolean;
  shopifyConnected: boolean;
  klaviyoConnected: boolean;
  campaignsImported: boolean;
  firstAgentRunCompleted: boolean;
  error?: string;
  createdAt: number;
  updatedAt: number;
}

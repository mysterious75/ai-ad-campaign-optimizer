import { createContext, useContext } from "react";
import type { Campaign, AgentRun, AgentLog, Approval, Onboarding, Client } from "./types";
import { MOCK_CLIENT, MOCK_CAMPAIGNS, MOCK_RUNS, MOCK_LOGS, MOCK_APPROVALS, MOCK_ONBOARDING } from "./mock-data";

export interface ConvexAPI {
  // Queries (simulated)
  getClient: () => Client;
  getCampaigns: (clientId: string) => Campaign[];
  getLatestRun: (clientId: string) => AgentRun | null;
  getRunHistory: (clientId: string) => AgentRun[];
  getLogs: (runId: string) => AgentLog[];
  getPendingApprovals: (clientId: string) => Approval[];
  getOnboarding: (clientId: string) => Onboarding | null;

  // Mutations (simulated)
  createRun: (clientId: string, trigger: "schedule" | "manual" | "webhook") => string;
  reviewApproval: (approvalId: string, status: "approved" | "rejected", reviewedBy: string) => void;
  triggerRun: (clientId: string) => void;

  // Uses mock? (for frontend display)
  usingMockData: boolean;
}

const mockApi: ConvexAPI = {
  getClient: () => MOCK_CLIENT,
  getCampaigns: () => MOCK_CAMPAIGNS,
  getLatestRun: () => MOCK_RUNS[0],
  getRunHistory: () => MOCK_RUNS,
  getLogs: (runId) => MOCK_LOGS.filter(l => l.runId === runId),
  getPendingApprovals: () => MOCK_APPROVALS,
  getOnboarding: () => MOCK_ONBOARDING,
  createRun: () => "run_new_001",
  reviewApproval: () => {},
  triggerRun: () => {},
  usingMockData: true,
};

export const ConvexCtx = createContext<ConvexAPI>(mockApi);
export const useConvex = () => useContext(ConvexCtx);

export { mockApi };

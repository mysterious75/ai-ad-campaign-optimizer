import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // Each client (agency customer) has their own data partition
  clients: defineTable({
    name: v.string(),
    platformConnections: v.object({
      meta: v.optional(v.object({
        accessToken: v.string(),
        adAccountId: v.string(),
        tokenExpiresAt: v.number(),
      })),
      google: v.optional(v.object({
        accessToken: v.string(),
        customerId: v.string(),
        refreshToken: v.string(),
        tokenExpiresAt: v.number(),
      })),
      shopify: v.optional(v.object({
        storeDomain: v.string(),
        accessToken: v.string(),
      })),
      klaviyo: v.optional(v.object({
        apiKey: v.string(),
      })),
    }),
    settings: v.object({
      defaultRoasTarget: v.number(),
      maxBudgetChangePct: v.number(),
      requireApprovalForBudgetOver: v.number(),
      timezone: v.string(),
    }),
    createdAt: v.number(),
  }).index("by_name", ["name"]),

  // Synced campaigns from Meta/Google
  campaigns: defineTable({
    clientId: v.id("clients"),
    platform: v.union(v.literal("meta"), v.literal("google")),
    platformCampaignId: v.string(),
    name: v.string(),
    status: v.string(),
    dailyBudget: v.number(),
    spend: v.number(),
    impressions: v.number(),
    clicks: v.number(),
    conversions: v.number(),
    revenue: v.number(),
    roas: v.number(),
    ctr: v.number(),
    cpc: v.number(),
    lastSyncedAt: v.number(),
  })
    .index("by_client", ["clientId"])
    .index("by_platform", ["platform", "platformCampaignId"]),

  // Each run of the agent system
  agentRuns: defineTable({
    clientId: v.id("clients"),
    trigger: v.union(v.literal("schedule"), v.literal("manual"), v.literal("webhook")),
    status: v.union(
      v.literal("pending"),
      v.literal("researching"),
      v.literal("planning"),
      v.literal("analyzing"),
      v.literal("validating"),
      v.literal("reporting"),
      v.literal("awaiting_approval"),
      v.literal("executing"),
      v.literal("completed"),
      v.literal("failed")
    ),
    summary: v.optional(v.string()),
    startedAt: v.number(),
    completedAt: v.optional(v.number()),
    error: v.optional(v.string()),
  })
    .index("by_client", ["clientId"])
    .index("by_status", ["status"])
    .index("by_client_status", ["clientId", "status"]),

  // Append-only log of agent decisions
  agentLogs: defineTable({
    runId: v.id("agentRuns"),
    clientId: v.id("clients"),
    agent: v.string(),
    msgType: v.string(),
    payload: v.any(),
    createdAt: v.number(),
  })
    .index("by_run", ["runId"])
    .index("by_client", ["clientId"]),

  // Actions requiring human approval
  approvals: defineTable({
    runId: v.id("agentRuns"),
    clientId: v.id("clients"),
    actionType: v.string(),
    details: v.string(),
    impact: v.number(),
    status: v.union(
      v.literal("pending"),
      v.literal("approved"),
      v.literal("rejected"),
      v.literal("expired")
    ),
    reviewedBy: v.optional(v.string()),
    reviewedAt: v.optional(v.number()),
    createdAt: v.number(),
    expiresAt: v.number(),
  })
    .index("by_client_status", ["clientId", "status"])
    .index("by_run", ["runId"]),

  // Client onboarding state machine
  onboarding: defineTable({
    clientId: v.id("clients"),
    step: v.string(),
    status: v.union(v.literal("in_progress"), v.literal("completed"), v.literal("failed")),
    metaConnected: v.boolean(),
    googleConnected: v.boolean(),
    shopifyConnected: v.boolean(),
    klaviyoConnected: v.boolean(),
    campaignsImported: v.boolean(),
    firstAgentRunCompleted: v.boolean(),
    error: v.optional(v.string()),
    createdAt: v.number(),
    updatedAt: v.number(),
  })
    .index("by_client", ["clientId"])
    .index("by_step_status", ["step", "status"]),
});

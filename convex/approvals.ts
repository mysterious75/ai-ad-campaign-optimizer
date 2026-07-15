import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const create = mutation({
  args: {
    runId: v.id("agentRuns"),
    clientId: v.id("clients"),
    actionType: v.string(),
    details: v.string(),
    impact: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("approvals", {
      runId: args.runId,
      clientId: args.clientId,
      actionType: args.actionType,
      details: args.details,
      impact: args.impact,
      status: "pending",
      createdAt: Date.now(),
      expiresAt: Date.now() + 24 * 60 * 60 * 1000,
    });
  },
});

export const review = mutation({
  args: {
    approvalId: v.id("approvals"),
    status: v.union(v.literal("approved"), v.literal("rejected")),
    reviewedBy: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.approvalId, {
      status: args.status,
      reviewedBy: args.reviewedBy,
      reviewedAt: Date.now(),
    });
  },
});

export const listPending = query({
  args: { clientId: v.id("clients") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("approvals")
      .withIndex("by_client_status", (q) =>
        q.eq("clientId", args.clientId).eq("status", "pending")
      )
      .collect();
  },
});

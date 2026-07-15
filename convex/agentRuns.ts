import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const create = mutation({
  args: {
    clientId: v.id("clients"),
    trigger: v.union(v.literal("schedule"), v.literal("manual"), v.literal("webhook")),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("agentRuns", {
      clientId: args.clientId,
      trigger: args.trigger,
      status: "pending",
      startedAt: Date.now(),
    });
  },
});

export const updateStatus = mutation({
  args: {
    runId: v.id("agentRuns"),
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
    error: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const patch: Record<string, any> = { status: args.status };
    if (args.summary) patch.summary = args.summary;
    if (args.error) patch.error = args.error;
    if (args.status === "completed" || args.status === "failed") {
      patch.completedAt = Date.now();
    }
    await ctx.db.patch(args.runId, patch);
  },
});

export const getLatestByClient = query({
  args: { clientId: v.id("clients") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("agentRuns")
      .withIndex("by_client", (q) => q.eq("clientId", args.clientId))
      .order("desc")
      .first();
  },
});

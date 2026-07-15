import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const append = mutation({
  args: {
    runId: v.id("agentRuns"),
    clientId: v.id("clients"),
    agent: v.string(),
    msgType: v.string(),
    payload: v.any(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("agentLogs", {
      runId: args.runId,
      clientId: args.clientId,
      agent: args.agent,
      msgType: args.msgType,
      payload: args.payload,
      createdAt: Date.now(),
    });
  },
});

export const listByRun = query({
  args: { runId: v.id("agentRuns") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("agentLogs")
      .withIndex("by_run", (q) => q.eq("runId", args.runId))
      .order("asc")
      .collect();
  },
});

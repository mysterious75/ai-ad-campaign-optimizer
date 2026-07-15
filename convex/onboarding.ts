import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const getOrCreate = mutation({
  args: { clientId: v.id("clients") },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("onboarding")
      .withIndex("by_client", (q) => q.eq("clientId", args.clientId))
      .first();

    if (existing) return existing._id;

    return await ctx.db.insert("onboarding", {
      clientId: args.clientId,
      step: "connect_meta",
      status: "in_progress",
      metaConnected: false,
      googleConnected: false,
      shopifyConnected: false,
      klaviyoConnected: false,
      campaignsImported: false,
      firstAgentRunCompleted: false,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    });
  },
});

export const updateStep = mutation({
  args: {
    clientId: v.id("clients"),
    step: v.string(),
    updates: v.object({
      metaConnected: v.optional(v.boolean()),
      googleConnected: v.optional(v.boolean()),
      shopifyConnected: v.optional(v.boolean()),
      klaviyoConnected: v.optional(v.boolean()),
      campaignsImported: v.optional(v.boolean()),
      firstAgentRunCompleted: v.optional(v.boolean()),
      status: v.optional(v.union(v.literal("in_progress"), v.literal("completed"), v.literal("failed"))),
      error: v.optional(v.string()),
    }),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("onboarding")
      .withIndex("by_client", (q) => q.eq("clientId", args.clientId))
      .first();

    if (!existing) throw new Error("Onboarding not found");

    await ctx.db.patch(existing._id, {
      step: args.step,
      ...args.updates,
      updatedAt: Date.now(),
    });
  },
});

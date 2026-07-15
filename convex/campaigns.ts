import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

export const list = query({
  args: { clientId: v.id("clients") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("campaigns")
      .withIndex("by_client", (q) => q.eq("clientId", args.clientId))
      .collect();
  },
});

export const upsert = mutation({
  args: {
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
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("campaigns")
      .withIndex("by_platform", (q) =>
        q.eq("platform", args.platform).eq("platformCampaignId", args.platformCampaignId)
      )
      .first();

    const data = { ...args, lastSyncedAt: Date.now() };

    if (existing) {
      await ctx.db.patch(existing._id, data);
      return existing._id;
    }
    return await ctx.db.insert("campaigns", data);
  },
});

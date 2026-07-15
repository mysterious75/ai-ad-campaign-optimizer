import { useState } from "react";
import { useConvex } from "../lib/convex";

export default function Settings() {
  const convex = useConvex();
  const client = convex.getClient();

  const [settings, setSettings] = useState(client.settings);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Settings</h2>
          <p>Client configuration and platform connections</p>
        </div>
        <button className="btn btn-primary" onClick={handleSave}>
          {saved ? "Saved!" : "Save Changes"}
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <div className="card">
          <h3 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "1rem" }}>Agent Settings</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                Default ROAS Target
              </label>
              <input type="number" value={settings.defaultRoasTarget} step="0.1"
                onChange={e => setSettings({ ...settings, defaultRoasTarget: parseFloat(e.target.value) })}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", fontSize: "0.85rem" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                Max Budget Change %
              </label>
              <input type="number" value={settings.maxBudgetChangePct}
                onChange={e => setSettings({ ...settings, maxBudgetChangePct: parseInt(e.target.value) })}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", fontSize: "0.85rem" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                Require Approval For Budget Over ($)
              </label>
              <input type="number" value={settings.requireApprovalForBudgetOver}
                onChange={e => setSettings({ ...settings, requireApprovalForBudgetOver: parseInt(e.target.value) })}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", fontSize: "0.85rem" }} />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.3rem" }}>
                Timezone
              </label>
              <select value={settings.timezone}
                onChange={e => setSettings({ ...settings, timezone: e.target.value })}
                style={{ width: "100%", padding: "0.5rem", borderRadius: "var(--radius)", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)", fontSize: "0.85rem" }}>
                <option>Australia/Sydney</option>
                <option>Australia/Melbourne</option>
                <option>Australia/Brisbane</option>
                <option>America/New_York</option>
                <option>America/Los_Angeles</option>
                <option>Europe/London</option>
                <option>Asia/Kolkata</option>
                <option>UTC</option>
              </select>
            </div>
          </div>
        </div>

        <div>
          <div className="card" style={{ marginBottom: "1rem" }}>
            <h3 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "1rem" }}>Platform Connections</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {[
                { name: "Meta Ads", connected: !!client.platformConnections.meta, id: client.platformConnections.meta?.adAccountId || "-" },
                { name: "Google Ads", connected: !!client.platformConnections.google, id: client.platformConnections.google?.customerId || "-" },
                { name: "Shopify", connected: !!client.platformConnections.shopify, id: client.platformConnections.shopify?.storeDomain || "-" },
                { name: "Klaviyo", connected: !!client.platformConnections.klaviyo, id: "API Key: " + (client.platformConnections.klaviyo?.apiKey?.slice(0, 10) || "-") },
              ].map(p => (
                <div key={p.name} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0.5rem", border: "1px solid var(--border)", borderRadius: "var(--radius)" }}>
                  <div>
                    <div style={{ fontWeight: 500, fontSize: "0.85rem" }}>{p.name}</div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{p.id}</div>
                  </div>
                  <span className={`badge ${p.connected ? "badge-green" : "badge-red"}`}>
                    {p.connected ? "Connected" : "Disconnected"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.5rem" }}>Client Info</h3>
            <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
              <div>Name: {client.name}</div>
              <div>Client ID: {client._id}</div>
              <div>Created: {new Date(client.createdAt).toLocaleDateString()}</div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

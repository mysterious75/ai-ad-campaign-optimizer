import { Link } from "react-router-dom";
import { useConvex } from "../lib/convex";

export default function Dashboard() {
  const convex = useConvex();
  const campaigns = convex.getCampaigns("client_demo_001");
  const latestRun = convex.getLatestRun("client_demo_001");
  const pendingApprovals = convex.getPendingApprovals("client_demo_001");

  const totalSpend = campaigns.reduce((s, c) => s + c.spend, 0);
  const totalRevenue = campaigns.reduce((s, c) => s + c.revenue, 0);
  const overallRoas = totalSpend > 0 ? totalRevenue / totalSpend : 0;
  const activeCampaigns = campaigns.filter(c => c.status === "ACTIVE").length;
  const lowRoasCount = campaigns.filter(c => c.roas < 1.5).length;

  return (
    <>
      <div className="page-header page-header-row">
        <div>
          <h2>Dashboard</h2>
          <p>Real-time campaign performance overview</p>
        </div>
        <div className="page-header-actions">
          {pendingApprovals.length > 0 && (
            <Link to="/approvals" className="btn btn-primary">
              {pendingApprovals.length} Pending Approval{pendingApprovals.length > 1 ? "s" : ""}
            </Link>
          )}
        </div>
      </div>

      <div className="card-grid">
        <div className="card stat-card green">
          <div className="stat-value text-green">${(totalRevenue / 1000).toFixed(1)}k</div>
          <div className="stat-label">Total Revenue (30d)</div>
        </div>
        <div className="card stat-card accent">
          <div className="stat-value">${(totalSpend / 1000).toFixed(1)}k</div>
          <div className="stat-label">Total Ad Spend (30d)</div>
        </div>
        <div className="card stat-card" style={{ borderTop: "2px solid " + (overallRoas >= 1.5 ? "var(--green)" : "var(--red)") }}>
          <div className="stat-value" style={{ color: overallRoas >= 1.5 ? "var(--green)" : "var(--red)" }}>
            {overallRoas.toFixed(2)}x
          </div>
          <div className="stat-label">Overall ROAS</div>
          <span className={`stat-sub ${overallRoas >= 1.5 ? "badge-green" : "badge-red"}`}>
            {overallRoas >= 1.5 ? "Above target" : "Below target (1.5x)"}
          </span>
        </div>
        <div className="card stat-card blue">
          <div className="stat-value text-blue">{activeCampaigns}</div>
          <div className="stat-label">Active Campaigns</div>
          {lowRoasCount > 0 && (
            <span className="stat-sub badge-yellow">{lowRoasCount} below ROAS target</span>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
        <div className="card">
          <h3 style={{ fontSize: ".95rem", fontWeight: 600, marginBottom: "1rem" }}>Campaign Performance</h3>
          <table>
            <thead>
              <tr>
                <th>Campaign</th><th>Spend</th><th>Revenue</th><th>ROAS</th><th>CTR</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map(c => (
                <tr key={c._id}>
                  <td style={{ fontWeight: 500 }}>{c.name}</td>
                  <td>${c.spend.toLocaleString()}</td>
                  <td>${c.revenue.toLocaleString()}</td>
                  <td style={{ color: c.roas >= 1.5 ? "var(--green)" : "var(--red)", fontWeight: 600 }}>
                    {c.roas.toFixed(2)}x
                  </td>
                  <td>{c.ctr.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h3 style={{ fontSize: ".95rem", fontWeight: 600, marginBottom: "1rem" }}>Latest Agent Run</h3>
          {latestRun ? (
            <>
              <div style={{ display: "flex", alignItems: "center", gap: ".5rem", marginBottom: ".75rem", flexWrap: "wrap" }}>
                <span className={`badge ${latestRun.status === "completed" ? "badge-green" : latestRun.status === "failed" ? "badge-red" : "badge-yellow"}`}>
                  {latestRun.status}
                </span>
                <span className={`badge badge-${latestRun.trigger === "schedule" ? "gray" : "blue"}`}>
                  {latestRun.trigger}
                </span>
                <span style={{ fontSize: ".78rem", color: "var(--text-muted)", marginLeft: "auto" }}>
                  {new Date(latestRun.startedAt).toLocaleString()}
                </span>
              </div>
              <p style={{ fontSize: ".85rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                {latestRun.summary || "No summary available"}
              </p>
              <div style={{ marginTop: ".75rem", display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
                <span className="badge badge-green">Revenue: ${totalRevenue.toLocaleString()}</span>
                <span className="badge badge-yellow">ROAS: {overallRoas.toFixed(2)}x</span>
              </div>
            </>
          ) : (
            <div className="empty">
              <div className="empty-icon">O</div>
              <p>No runs yet. Trigger your first analysis from the Agent Runs page.</p>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: ".95rem", fontWeight: 600, marginBottom: "1rem" }}>Agent Pipeline</h3>
        <div className="agent-grid">
          {[
            { name: "Researcher", desc: "API data fetching with rate limits & auto token refresh", color: "var(--blue)" },
            { name: "Planner", desc: "Deterministic analysis planning — zero LLM cost", color: "var(--green)" },
            { name: "Analyst", desc: "LLM-powered campaign analysis via Gemini or Claude", color: "var(--accent)" },
            { name: "Validator", desc: "Hallucination, schema & contradiction detection", color: "var(--orange)" },
            { name: "Action", desc: "Executes budget changes via Meta/Google APIs", color: "var(--yellow)" },
            { name: "Report", desc: "Generates summaries + Convex logging + email alerts", color: "var(--text-muted)" },
          ].map(a => (
            <div key={a.name} className="agent-card">
              <div className="agent-card-name" style={{ color: a.color }}>{a.name}</div>
              <div className="agent-card-desc">{a.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

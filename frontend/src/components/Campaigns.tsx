import { useConvex } from "../lib/convex";

export default function Campaigns() {
  const convex = useConvex();
  const campaigns = convex.getCampaigns("client_demo_001");
  const avgRoas = campaigns.reduce((s, c) => s + c.roas, 0) / campaigns.length;
  const avgCpc = campaigns.reduce((s, c) => s + c.cpc, 0) / campaigns.length;

  return (
    <>
      <div className="page-header page-header-row">
        <div>
          <h2>Campaigns</h2>
          <p>{campaigns.length} campaigns across connected platforms</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary" onClick={() => convex.triggerRun("client_demo_001")}>
            Run Analysis
          </button>
        </div>
      </div>

      <div className="card-grid">
        <div className="card stat-card green">
          <div className="stat-value text-green">{campaigns.filter(c => c.roas >= 1.5).length}/{campaigns.length}</div>
          <div className="stat-label">Above ROAS Target (1.5x)</div>
        </div>
        <div className="card stat-card accent">
          <div className="stat-value">{avgRoas.toFixed(2)}x</div>
          <div className="stat-label">Average ROAS</div>
        </div>
        <div className="card stat-card blue">
          <div className="stat-value">${avgCpc.toFixed(2)}</div>
          <div className="stat-label">Average CPC</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value text-yellow">{campaigns.filter(c => c.roas < 1.5).length}</div>
          <div className="stat-label">Campaigns Below Target</div>
          <span className="stat-sub badge-yellow">Review recommended</span>
        </div>
      </div>

      <div className="card" style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Name</th><th>Platform</th><th>Status</th><th>Budget</th><th>Spend</th><th>Revenue</th>
              <th>ROAS</th><th>CTR</th><th>CPC</th><th>Impressions</th><th>Clicks</th><th>Conversions</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.map(c => (
              <tr key={c._id}>
                <td style={{ fontWeight: 500 }}>{c.name}</td>
                <td><span className={`badge ${c.platform === "meta" ? "badge-blue" : "badge-gray"}`}>{c.platform}</span></td>
                <td><span className={`badge ${c.status === "ACTIVE" ? "badge-green" : "badge-gray"}`}>{c.status}</span></td>
                <td>${c.dailyBudget}</td>
                <td>${c.spend.toLocaleString()}</td>
                <td style={{ color: "var(--green)", fontWeight: 500 }}>${c.revenue.toLocaleString()}</td>
                <td style={{ color: c.roas >= 1.5 ? "var(--green)" : "var(--red)", fontWeight: 600 }}>
                  {c.roas.toFixed(2)}x
                </td>
                <td>{c.ctr.toFixed(2)}%</td>
                <td>${c.cpc.toFixed(2)}</td>
                <td>{c.impressions.toLocaleString()}</td>
                <td>{c.clicks.toLocaleString()}</td>
                <td>{c.conversions}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {campaigns.filter(c => c.roas < 1.5).length > 0 && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h3 style={{ fontSize: ".95rem", fontWeight: 600, marginBottom: "1rem" }}>AI-Generated Findings</h3>
          {campaigns.filter(c => c.roas < 1.5).map(c => (
            <div key={c._id} className="finding-item high">
              <strong>{c.name}</strong>
              <p>
                ROAS of {c.roas.toFixed(2)}x is below the target of 1.5x. Total spend of ${c.spend.toLocaleString()} is yielding negative returns.
                {c.roas < 1 ? " Consider pausing this campaign and reallocating budget to higher-performing campaigns." : " Review targeting, ad creatives, and landing page experience."}
              </p>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

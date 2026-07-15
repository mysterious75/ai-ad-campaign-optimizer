import { useConvex } from "../lib/convex";

export default function Approvals() {
  const convex = useConvex();
  const pendingApprovals = convex.getPendingApprovals("client_demo_001");

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Approvals</h2>
          <p>{pendingApprovals.length} action{pendingApprovals.length !== 1 ? "s" : ""} awaiting your review</p>
        </div>
      </div>

      {pendingApprovals.length === 0 ? (
        <div className="card">
          <div className="empty">
            <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>All clear!</div>
            <p>No pending approvals. All agent actions are within configured thresholds.</p>
          </div>
        </div>
      ) : (
        pendingApprovals.map(approval => (
          <div key={approval._id} className="card" style={{ marginBottom: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <div>
                <span className="badge badge-yellow" style={{ marginRight: 8 }}>{approval.actionType}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  Expires {new Date(approval.expiresAt).toLocaleDateString()}
                </span>
              </div>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Created {new Date(approval.createdAt).toLocaleString()}
              </span>
            </div>
            <p style={{ marginBottom: "0.75rem" }}>{approval.details}</p>
            <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>Budget Impact:</span>
              <span style={{ fontWeight: 600, color: approval.impact > 0 ? "var(--orange)" : "var(--green)" }}>
                ${approval.impact > 0 ? "+" : ""}{approval.impact.toFixed(2)}
              </span>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button className="btn btn-primary" onClick={() => {
                convex.reviewApproval(approval._id, "approved", "demo_user");
                alert("Approved! Changes will be executed in the next cycle.");
              }}>
                Approve
              </button>
              <button className="btn btn-ghost" style={{ color: "var(--red)" }} onClick={() => {
                convex.reviewApproval(approval._id, "rejected", "demo_user");
                alert("Rejected. No changes will be made.");
              }}>
                Reject
              </button>
            </div>
          </div>
        ))
      )}
    </>
  );
}

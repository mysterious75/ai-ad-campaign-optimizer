import { useState } from "react";
import { useConvex } from "../lib/convex";
import type { AgentRun, AgentLog } from "../lib/types";

const statusColors: Record<string, string> = {
  completed: "badge-green", failed: "badge-red", awaiting_approval: "badge-yellow",
  pending: "badge-gray", researching: "badge-blue", planning: "badge-blue",
  analyzing: "badge-blue", validating: "badge-blue", reporting: "badge-blue",
  executing: "badge-blue",
};

function RunDetail({ run, logs }: { run: AgentRun; logs: AgentLog[] }) {
  return (
    <div className="card" style={{ marginTop: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
        <div>
          <span className={`badge ${statusColors[run.status]}`} style={{ marginRight: 8 }}>{run.status}</span>
          <span className="badge badge-gray">{run.trigger}</span>
        </div>
        <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          {new Date(run.startedAt).toLocaleString()}
          {run.completedAt && ` - ${Math.round((run.completedAt - run.startedAt) / 1000)}s`}
        </span>
      </div>
      {run.summary && (
        <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
          {run.summary}
        </p>
      )}
      {run.error && (
        <p style={{ fontSize: "0.85rem", color: "var(--red)", marginBottom: "0.75rem" }}>
          Error: {run.error}
        </p>
      )}

      <h4 style={{ fontSize: "0.85rem", fontWeight: 600, marginBottom: "0.5rem" }}>Agent Logs</h4>
      {logs.length === 0 ? (
        <div className="empty">No logs for this run</div>
      ) : (
        logs.map(log => (
          <div key={log._id} className="log-entry">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span className="log-agent">{log.agent}</span>
              <span className="log-time">{new Date(log.createdAt).toLocaleTimeString()}</span>
            </div>
            <div className="log-msg">
              {log.payload?.message || JSON.stringify(log.payload).slice(0, 200)}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default function AgentRuns() {
  const convex = useConvex();
  const runs = convex.getRunHistory("client_demo_001");
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [expandedLogs, setExpandedLogs] = useState<AgentLog[]>([]);

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Agent Runs</h2>
          <p>History of automated optimization cycles</p>
        </div>
        <button className="btn btn-primary" onClick={() => {
          convex.triggerRun("client_demo_001");
          alert("New analysis run triggered!");
        }}>
          Trigger New Run
        </button>
      </div>

      <div className="card" style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Started</th>
              <th>Trigger</th>
              <th>Status</th>
              <th>Duration</th>
              <th>Summary</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {runs.map(run => (
              <tr key={run._id}>
                <td style={{ fontSize: "0.8rem" }}>{new Date(run.startedAt).toLocaleString()}</td>
                <td><span className={`badge ${run.trigger === "schedule" ? "badge-gray" : "badge-blue"}`}>{run.trigger}</span></td>
                <td><span className={`badge ${statusColors[run.status]}`}>{run.status}</span></td>
                <td style={{ fontSize: "0.8rem" }}>
                  {run.completedAt ? `${Math.round((run.completedAt - run.startedAt) / 1000)}s` : "-"}
                </td>
                <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: "0.8rem" }}>
                  {run.summary || "-"}
                </td>
                <td>
                  <button className="btn btn-ghost btn-sm" onClick={() => {
                    if (expandedRun === run._id) {
                      setExpandedRun(null);
                      setExpandedLogs([]);
                    } else {
                      setExpandedRun(run._id);
                      setExpandedLogs(convex.getLogs(run._id));
                    }
                  }}>
                    {expandedRun === run._id ? "Hide" : "Logs"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {expandedRun && <RunDetail run={runs.find(r => r._id === expandedRun)!} logs={expandedLogs} />}
    </>
  );
}

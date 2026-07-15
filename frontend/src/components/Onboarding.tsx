import { useConvex } from "../lib/convex";

const steps = [
  { key: "connect_meta", label: "Connect Meta Ads", desc: "Link your Meta Ads account via OAuth 2.0" },
  { key: "connect_google", label: "Connect Google Ads", desc: "Link your Google Ads account via OAuth 2.0" },
  { key: "connect_shopify", label: "Connect Shopify", desc: "Link your Shopify store for revenue data" },
  { key: "connect_klaviyo", label: "Connect Klaviyo", desc: "Link your Klaviyo account for email metrics" },
  { key: "import_campaigns", label: "Import Campaigns", desc: "AI agent fetches and maps existing campaigns" },
  { key: "first_run", label: "First Analysis", desc: "Run the full agent pipeline for the first time" },
];

const stepOrder = steps.map(s => s.key);

function StepIcon({ status }: { status: "done" | "active" | "pending" }) {
  return (
    <div className={`step-icon ${status}`}>
      {status === "done" ? String.fromCharCode(10003) : status === "active" ? String.fromCharCode(9679) : stepOrder.indexOf(status as any) + 1 || ""}
    </div>
  );
}

function CheckItem({ label, checked }: { label: string; checked: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem" }}>
      <span style={{ color: checked ? "var(--green)" : "var(--text-muted)" }}>
        {checked ? String.fromCharCode(10003) : String.fromCharCode(9675)}
      </span>
      <span style={{ color: checked ? "var(--text)" : "var(--text-muted)" }}>{label}</span>
    </div>
  );
}

export default function Onboarding() {
  const convex = useConvex();
  const onboarding = convex.getOnboarding("client_demo_001");

  const completedSteps = onboarding ? stepOrder.filter(s => {
    switch (s) {
      case "connect_meta": return onboarding.metaConnected;
      case "connect_google": return onboarding.googleConnected;
      case "connect_shopify": return onboarding.shopifyConnected;
      case "connect_klaviyo": return onboarding.klaviyoConnected;
      case "import_campaigns": return onboarding.campaignsImported;
      case "first_run": return onboarding.firstAgentRunCompleted;
      default: return false;
    }
  }).length : 0;

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Onboarding</h2>
          <p>Client setup progress: {completedSteps}/{steps.length} steps completed</p>
        </div>
        {onboarding?.status === "completed" && (
          <span className="badge badge-green">Completed</span>
        )}
      </div>

      <div className="card-grid">
        <div className="card">
          <div className="stat-value text-green">{onboarding?.metaConnected ? "1" : "0"}/1</div>
          <div className="stat-label">Meta Ads Connected</div>
        </div>
        <div className="card">
          <div className="stat-value text-blue">{onboarding?.googleConnected ? "1" : "0"}/1</div>
          <div className="stat-label">Google Ads Connected</div>
        </div>
        <div className="card">
          <div className="stat-value">{onboarding?.campaignsImported ? "Yes" : "No"}</div>
          <div className="stat-label">Campaigns Imported</div>
        </div>
        <div className="card">
          <div className="stat-value text-green">{onboarding?.firstAgentRunCompleted ? "Done" : "Pending"}</div>
          <div className="stat-label">First Agent Run</div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "1rem" }}>Setup Steps</h3>
        <div className="onboarding-steps">
          {steps.map((step, idx) => {
            let status: "done" | "active" | "pending";
            if (onboarding) {
              const isDone = (() => {
                switch (step.key) {
                  case "connect_meta": return onboarding.metaConnected;
                  case "connect_google": return onboarding.googleConnected;
                  case "connect_shopify": return onboarding.shopifyConnected;
                  case "connect_klaviyo": return onboarding.klaviyoConnected;
                  case "import_campaigns": return onboarding.campaignsImported;
                  case "first_run": return onboarding.firstAgentRunCompleted;
                  default: return false;
                }
              })();
              if (isDone) status = "done";
              else if (stepOrder.indexOf(onboarding.step) === idx) status = "active";
              else status = "pending";
            } else {
              status = idx === 0 ? "active" : "pending";
            }

            return (
              <div key={step.key} className={`step ${status}`}>
                <StepIcon status={status} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500, fontSize: "0.9rem" }}>{step.label}</div>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{step.desc}</div>
                </div>
                {onboarding && onboarding.status === "completed" && status === "done" && (
                  <span style={{ color: "var(--green)", fontSize: "0.8rem" }}>Done</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="card" style={{ marginTop: "1rem" }}>
        <h3 style={{ fontSize: "0.9rem", fontWeight: 600, marginBottom: "0.75rem" }}>Connection Status</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
          <CheckItem label="Meta Ads API" checked={onboarding?.metaConnected || false} />
          <CheckItem label="Google Ads API" checked={onboarding?.googleConnected || false} />
          <CheckItem label="Shopify Integration" checked={onboarding?.shopifyConnected || false} />
          <CheckItem label="Klaviyo Integration" checked={onboarding?.klaviyoConnected || false} />
          <CheckItem label="Campaigns Imported" checked={onboarding?.campaignsImported || false} />
          <CheckItem label="First Agent Run" checked={onboarding?.firstAgentRunCompleted || false} />
        </div>
      </div>
    </>
  );
}

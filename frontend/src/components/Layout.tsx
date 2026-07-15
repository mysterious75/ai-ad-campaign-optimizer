import { NavLink, Outlet } from "react-router-dom";
import { useConvex } from "../lib/convex";

const navItems = [
  { to: "/", label: "Dashboard", icon: "D" },
  { to: "/campaigns", label: "Campaigns", icon: "C" },
  { to: "/runs", label: "Agent Runs", icon: "R" },
  { to: "/approvals", label: "Approvals", icon: "A" },
  { to: "/onboarding", label: "Onboarding", icon: "O" },
  { to: "/settings", label: "Settings", icon: "S" },
];

export default function Layout() {
  const convex = useConvex();
  const pending = convex.getPendingApprovals("client_demo_001");

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">O</div>
          <div className="sidebar-brand-text">
            Ad Optimizer
            <span>AI Campaign Management</span>
          </div>
        </div>
        <nav className="nav">
          {navItems.map(({ to, label, icon }) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => isActive ? "active" : ""}>
              <span className="nav-icon">{icon}</span>
              {label}
              {label === "Approvals" && pending.length > 0 && (
                <span className="sidebar-badge">{pending.length}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span>{convex.usingMockData ? "Demo Mode" : "Live"}</span>
          <span>v1.0</span>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}

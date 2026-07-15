import { HashRouter, Routes, Route } from "react-router-dom";
import { ConvexCtx, mockApi } from "./lib/convex";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import Campaigns from "./components/Campaigns";
import AgentRuns from "./components/AgentRuns";
import Approvals from "./components/Approvals";
import Onboarding from "./components/Onboarding";
import Settings from "./components/Settings";

export default function App() {
  return (
    <ConvexCtx.Provider value={mockApi}>
      <HashRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="campaigns" element={<Campaigns />} />
            <Route path="runs" element={<AgentRuns />} />
            <Route path="approvals" element={<Approvals />} />
            <Route path="onboarding" element={<Onboarding />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </HashRouter>
    </ConvexCtx.Provider>
  );
}

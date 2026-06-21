import { useEffect } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { useAuth } from "./stores/auth";
import { AuditLogPage } from "./pages/AuditLog";
import { ActivityPage } from "./pages/Activity";
import { CasesPage } from "./pages/Cases";
import { CommandsPage } from "./pages/Commands";
import { DashboardPage } from "./pages/Dashboard";
import { EventDetailPage } from "./pages/EventDetail";
import { EventsPage } from "./pages/Events";
import { GroupsPage } from "./pages/Groups";
import { HealthPage } from "./pages/Health";
import { IndicatorsPage } from "./pages/Indicators";
import { LiveMonitorPage } from "./pages/LiveMonitor";
import { LoginPage } from "./pages/Login";
import { MemberOSINTPage } from "./pages/MemberOSINT";
import { OfficersPage } from "./pages/Officers";
import { ReportsPage } from "./pages/Reports";
import { UsersPage } from "./pages/Users";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;
  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="monitor" element={<LiveMonitorPage />} />
        <Route path="activity" element={<ActivityPage />} />
        <Route path="events" element={<EventsPage />} />
        <Route path="events/:id" element={<EventDetailPage />} />
        <Route path="indicators" element={<IndicatorsPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="members-osint" element={<MemberOSINTPage />} />
        <Route path="groups" element={<GroupsPage />} />
        <Route path="commands" element={<CommandsPage />} />
        <Route path="cases" element={<CasesPage />} />
        <Route path="officers" element={<OfficersPage />} />
        <Route path="audit" element={<AuditLogPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="health" element={<HealthPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

import { useAuth } from "../../stores/auth";
import { useHealth } from "../../api/queries";

export function Header() {
  const { logout, officer } = useAuth();
  const { data: health } = useHealth();
  const healthy = health?.status === "healthy" || health?.database === "connected";

  return (
    <header className="flex h-16 items-center justify-between border-b border-surface-200 bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold text-surface-900">Telegram Security Operations</h1>
        <p className="text-xs text-surface-500">Authorized group monitoring and bot response console</p>
      </div>
      <div className="flex items-center gap-4">
        <span className={`badge ${healthy ? "badge-low" : "badge-medium"}`}>
          API {healthy ? "online" : "checking"}
        </span>
        <span className="text-sm text-surface-500">
          {officer?.display_name || officer?.role || "Officer"}
        </span>
        <button onClick={logout} className="btn-ghost text-sm">
          Chiqish
        </button>
      </div>
    </header>
  );
}

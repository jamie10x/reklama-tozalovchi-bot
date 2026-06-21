import { clsx } from "clsx";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../stores/auth";

const navItems = [
  { to: "/", label: "Dashboard", icon: "◉", roles: ["super_admin", "analyst", "responder", "auditor"] },
  { to: "/monitor", label: "Live Monitor", icon: "●", roles: ["super_admin", "analyst", "responder"] },
  { to: "/activity", label: "Activity", icon: "▣", roles: ["super_admin", "analyst", "responder"] },
  { to: "/events", label: "Voqealar", icon: "⚡", roles: ["super_admin", "analyst", "responder"] },
  { to: "/indicators", label: "Indikatorlar", icon: "◆", roles: ["super_admin", "analyst"] },
  { to: "/users", label: "Foydalanuvchilar", icon: "👤", roles: ["super_admin", "analyst"] },
  { to: "/members-osint", label: "Members OSINT", icon: "◎", roles: ["super_admin", "analyst"] },
  { to: "/groups", label: "Guruhlar", icon: "💬", roles: ["super_admin", "analyst", "responder"] },
  { to: "/commands", label: "Buyruqlar", icon: "▶", roles: ["super_admin", "responder"] },
  { to: "/cases", label: "Ishlar", icon: "📋", roles: ["super_admin", "analyst", "responder"] },
  { to: "/officers", label: "Officerlar", icon: "🔐", roles: ["super_admin"] },
  { to: "/audit", label: "Audit", icon: "📜", roles: ["super_admin", "auditor"] },
  { to: "/reports", label: "Hisobotlar", icon: "📊", roles: ["super_admin", "analyst"] },
  { to: "/health", label: "Sog'liq", icon: "❤️", roles: ["super_admin", "analyst", "responder", "auditor"] },
];

export function Sidebar() {
  const { officer } = useAuth();
  const role = officer?.role ?? "analyst";

  const visibleItems = navItems.filter((item) => item.roles.includes(role));

  return (
    <aside className="flex h-full w-64 flex-col border-r border-surface-200 bg-white">
      <div className="flex h-16 items-center gap-3 border-b border-surface-100 px-6">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-600 text-sm font-bold text-white">
          S
        </span>
        <span className="text-lg font-semibold text-surface-900">SecAdmin</span>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {visibleItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent-50 text-accent-700"
                  : "text-surface-600 hover:bg-surface-100 hover:text-surface-900",
              )
            }
          >
            <span className="w-5 text-center">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-surface-200 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-100 text-sm font-medium text-accent-700">
            {officer?.display_name?.charAt(0)?.toUpperCase() || "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-surface-900">
              {officer?.display_name || "Officer"}
            </p>
            <p className="text-xs text-surface-500">{officer?.role}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

import { clsx } from "clsx";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../stores/auth";
import { useI18n } from "../../i18n";

const navSections = [
  {
    labelKey: "operations",
    items: [
      { to: "/", labelKey: "command_center", icon: "CC", roles: ["super_admin", "analyst", "responder", "auditor"] },
      { to: "/monitor", labelKey: "live_triage", icon: "LT", roles: ["super_admin", "analyst", "responder"] },
      { to: "/groups", labelKey: "group_health", icon: "GH", roles: ["super_admin", "analyst", "responder"] },
      { to: "/activity", labelKey: "activity_store", icon: "AS", roles: ["super_admin", "analyst", "responder"] },
    ],
  },
  {
    labelKey: "investigation",
    items: [
      { to: "/events", labelKey: "events", icon: "EV", roles: ["super_admin", "analyst", "responder"] },
      { to: "/cases", labelKey: "cases", icon: "CA", roles: ["super_admin", "analyst", "responder"] },
      { to: "/members-osint", labelKey: "member_intel", icon: "MI", roles: ["super_admin", "analyst"] },
      { to: "/indicators", labelKey: "indicators", icon: "IN", roles: ["super_admin", "analyst"] },
      { to: "/users", labelKey: "users", icon: "US", roles: ["super_admin", "analyst"] },
    ],
  },
  {
    labelKey: "response",
    items: [
      { to: "/commands", labelKey: "bot_commands", icon: "BC", roles: ["super_admin", "responder"] },
      { to: "/reports", labelKey: "reports", icon: "RP", roles: ["super_admin", "analyst"] },
    ],
  },
  {
    labelKey: "administration",
    items: [
      { to: "/health", labelKey: "system_health", icon: "SH", roles: ["super_admin", "analyst", "responder", "auditor"] },
      { to: "/audit", labelKey: "audit_log", icon: "AL", roles: ["super_admin", "auditor"] },
      { to: "/officers", labelKey: "officers", icon: "OF", roles: ["super_admin"] },
    ],
  },
];

export function Sidebar() {
  const { officer } = useAuth();
  const { t } = useI18n();
  const role = officer?.role ?? "analyst";

  return (
    <aside className="flex h-full w-64 flex-col border-r border-surface-200 bg-white">
      <div className="flex h-16 items-center gap-3 border-b border-surface-100 px-6">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-900 text-sm font-bold text-white">
          S
        </span>
        <div>
          <span className="block text-lg font-semibold text-surface-900">SecAdmin</span>
          <span className="block text-[11px] font-medium uppercase tracking-wide text-surface-400">{t("telegram_soc")}</span>
        </div>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto p-3">
        {navSections.map((section) => {
          const visibleItems = section.items.filter((item) => item.roles.includes(role));
          if (visibleItems.length === 0) return null;
          return (
            <div key={section.labelKey}>
              <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wide text-surface-400">
                {t(section.labelKey)}
              </p>
              <div className="space-y-1">
                {visibleItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === "/"}
                    className={({ isActive }) =>
                      clsx(
                        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-surface-900 text-white"
                          : "text-surface-600 hover:bg-surface-100 hover:text-surface-900",
                      )
                    }
                  >
                    <span className="flex h-6 w-7 shrink-0 items-center justify-center rounded border border-current/15 text-[10px] font-semibold">
                      {item.icon}
                    </span>
                    <span className="truncate">{t(item.labelKey)}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          );
        })}
      </nav>
      <div className="border-t border-surface-200 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-100 text-sm font-medium text-accent-700">
            {officer?.display_name?.charAt(0)?.toUpperCase() || "?"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-surface-900">
              {officer?.display_name || t("officer")}
            </p>
            <p className="text-xs text-surface-500">{officer?.role}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

import { useAuth } from "../../stores/auth";
import { useHealth } from "../../api/queries";
import { useI18n } from "../../i18n";

export function Header() {
  const { logout, officer } = useAuth();
  const { data: health } = useHealth();
  const { lang, setLang, t } = useI18n();
  const healthy = health?.status === "healthy" || health?.database === "connected";

  return (
    <header className="flex min-h-16 items-center justify-between gap-4 border-b border-surface-200 bg-white px-6 py-3">
      <div className="min-w-0">
        <h1 className="truncate text-lg font-semibold text-surface-900">{t("header_title")}</h1>
        <p className="truncate text-xs text-surface-500">{t("header_subtitle")}</p>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <span className={`badge ${healthy ? "badge-low" : "badge-medium"}`}>
          {healthy ? t("api_online") : t("api_checking")}
        </span>
        <div className="flex rounded-lg border border-surface-200 p-0.5" aria-label={t("language")}>
          {(["en", "uz"] as const).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setLang(item)}
              className={`rounded-md px-2 py-1 text-xs font-medium ${
                lang === item ? "bg-surface-900 text-white" : "text-surface-500 hover:bg-surface-100"
              }`}
            >
              {item.toUpperCase()}
            </button>
          ))}
        </div>
        <span className="text-sm text-surface-500">
          {officer?.display_name || officer?.role || "Officer"}
        </span>
        <button onClick={logout} className="btn-ghost text-sm">
          {t("logout")}
        </button>
      </div>
    </header>
  );
}

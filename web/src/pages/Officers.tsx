import { useOfficers } from "../api/queries";
import { useI18n } from "../i18n";

export function OfficersPage() {
  const { t } = useI18n();
  const { data, isLoading } = useOfficers();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">{t("officers")}</h2>
        <p className="mt-1 text-sm text-surface-500">{t("officers_desc")}</p>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-surface-100" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-surface-200 text-surface-500">
                  <th className="pb-3 font-medium">Telegram ID</th>
                  <th className="pb-3 font-medium">{t("name")}</th>
                  <th className="pb-3 font-medium">{t("role")}</th>
                  <th className="pb-3 font-medium">{t("status")}</th>
                  <th className="pb-3 font-medium">{t("last_login")}</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((o) => (
                  <tr key={o.id} className="border-b border-surface-100 hover:bg-surface-50">
                    <td className="py-3 font-mono text-xs">{o.telegram_id}</td>
                    <td className="py-3 font-medium">{o.display_name || "—"}</td>
                    <td className="py-3 capitalize">{o.role}</td>
                    <td className="py-3">
                      <span className={`badge ${o.is_active ? "badge-low" : "badge-info"}`}>
                        {o.is_active ? t("active") : t("inactive")}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-surface-500">
                      {o.last_login_at
                        ? new Date(o.last_login_at).toLocaleString("uz-UZ")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

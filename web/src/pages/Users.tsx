import { useState } from "react";
import { useUsers } from "../api/queries";
import { useDebounce } from "../hooks/useDebounce";
import { useI18n } from "../i18n";

export function UsersPage() {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 400);

  const { data, isLoading } = useUsers(debouncedQuery);

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">{t("users")}</h2>
        <p className="mt-1 text-sm text-surface-500">{t("users_desc")}</p>
      </div>

      <div className="card mb-6">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="input max-w-md"
          placeholder={t("search_users_placeholder")}
        />
      </div>

      <div className="card">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-surface-100" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-surface-200 text-surface-500">
                  <th className="pb-3 font-medium">ID</th>
                  <th className="pb-3 font-medium">{t("username")}</th>
                  <th className="pb-3 font-medium">{t("name")}</th>
                  <th className="pb-3 font-medium">{t("bot")}</th>
                  <th className="pb-3 font-medium">{t("risk")}</th>
                  <th className="pb-3 font-medium">{t("last_activity")}</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((user) => (
                  <tr key={user.telegram_id} className="border-b border-surface-100 hover:bg-surface-50">
                    <td className="py-3 font-mono text-xs">{user.telegram_id}</td>
                    <td className="py-3">
                      {user.current_username ? `@${user.current_username}` : "—"}
                    </td>
                    <td className="py-3">
                      {[user.current_first_name, user.current_last_name]
                        .filter(Boolean)
                        .join(" ") || "—"}
                    </td>
                    <td className="py-3">{user.is_bot ? "🤖" : "👤"}</td>
                    <td className="py-3">
                      <span
                        className={`badge ${
                          user.risk_score >= 10
                            ? "badge-critical"
                            : user.risk_score >= 5
                              ? "badge-high"
                              : "badge-low"
                        }`}
                      >
                        {user.risk_score}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-surface-500">
                      {user.last_seen_at
                        ? new Date(user.last_seen_at).toLocaleString("uz-UZ")
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
